from datetime import datetime
import math

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mellioncoin import (
    MEC_VALUE,
    optimized_distribution,
    compute_interets,
    compute_commissions,
    load_history,
    append_history,
)

app = FastAPI(title="MellionCoin API")


class SimulationRequest(BaseModel):
    date: str   # format JJ-MM-AAAA
    montant: float  # montant en USD


@app.get("/")
def root():
    return {"message": "MellionCoin API en ligne", "status": "ok"}


def simulate_investment(date_str: str, X: float) -> dict:
    # 1) Validation de la date
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        raise ValueError("Format de date invalide. Utilise JJ-MM-AAAA.")
    date_norm = dt.strftime("%d-%m-%Y")

    # 2) Validation du montant
    if X <= 0:
        raise ValueError("Le montant doit être > 0.")
    if X % MEC_VALUE != 0:
        raise ValueError(f"Le montant doit être un multiple de {MEC_VALUE} USD.")

    # 3) Répartition optimisée
    n_opt, mec, caps = optimized_distribution(X)

    # 4) Intérêts et commissions
    interets = compute_interets(caps)
    commissions = compute_commissions(caps)

    total_I = sum(interets)
    total_C = sum(commissions)
    total_MEC_initial = sum(mec)

    # 5) Logique de réinvestissement (exactement celle de ton main())
    if X >= 3000:
        # Commission totale transformée en multiple de 500 -> C_tm
        C_tm = math.ceil(total_C / MEC_VALUE) * MEC_VALUE

        # MEC issues de la commission réinvestie
        mec_commission_reinvestie = C_tm / MEC_VALUE

        # Somme ajoutée pour atteindre ce multiple
        Sa = C_tm - total_C

        # Commission supplémentaire générée
        Com_supp = 1.24 * C_tm

        # Revenu global = intérêts + commission suppl.
        Revenu_global = Com_supp + total_I

        # MEC totales = MEC initiales + MEC issues du réinvestissement
        total_MEC_global = total_MEC_initial + mec_commission_reinvestie

        denom = X + Sa
    else:
        # Aucun réinvestissement quand X < 3000
        C_tm = 0.0
        Sa = 0.0
        Com_supp = 0.0
        mec_commission_reinvestie = 0.0

        # Revenu global = intérêts + commissions totales
        Revenu_global = total_I + total_C

        # Pas de MEC supplémentaires
        total_MEC_global = total_MEC_initial

        denom = X

    r = Revenu_global / denom if denom != 0 else 0.0

    # 6) Sauvegarde dans l'historique (comme ton script console)
    try:
        history = load_history()
    except Exception:
        history = []

    row = {
        "date": date_norm,
        "investissement": f"{X:,.2f}",
        "interets": f"{total_I:,.2f}",
        "commissions_totales": f"{total_C:,.2f}",
        "commission_supplementaire": f"{Com_supp:,.2f}",
        "revenu_global": f"{Revenu_global:,.2f}",
        "nombre_MEC": f"{total_MEC_global:,.0f}",
        "rendement": f"{r * 100:,.2f} %",
    }

    try:
        append_history(row)
    except Exception:
        # Sur Render, le système de fichiers est éphémère, ce n'est pas grave si ça échoue
        pass

    return {
        "date": date_norm,
        "investissement": X,
        "niveaux": n_opt,
        "mec_par_niveau": mec,
        "capital_par_niveau": caps,
        "interets_totaux": total_I,
        "commissions_totales": total_C,
        "commission_arrondie": C_tm,
        "somme_ajoutee_Sa": Sa,
        "commission_supplementaire": Com_supp,
        "mec_commission_reinvestie": mec_commission_reinvestie,
        "mec_total": total_MEC_global,
        "revenu_global": Revenu_global,
        "rendement_pourcent": r * 100,
    }


@app.post("/simulate")
def simulate(request: SimulationRequest):
    """
    Endpoint principal appelé par ton appli mobile.
    """
    try:
        return simulate_investment(request.date, request.montant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur serveur interne")
