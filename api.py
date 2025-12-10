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


# =========================
# Schémas de données
# =========================

class SimulationRequest(BaseModel):
    date: str      # format JJ-MM-AAAA
    montant: float # X en USD


class SimulationResponse(BaseModel):
    date: str
    investissement: float
    niveaux: int
    mec_par_niveau: list[int]
    capital_par_niveau: list[float]
    interets_par_niveau: list[float]
    commissions_par_niveau: list[float]

    interets_totaux: float
    commissions_totales: float

    commission_arrondie: float
    somme_ajoutee_Sa: float
    commission_supplementaire: float
    mec_commission_reinvestie: float

    mec_total: float
    revenu_global: float
    rendement_pourcent: float


class HistoryRow(BaseModel):
    date: str
    investissement: str
    interets: str
    commissions_totales: str
    commission_supplementaire: str
    revenu_global: str
    nombre_MEC: str
    rendement: str


# =========================
# Logic métier (à partir du main())
# =========================

def simulate_investment(date_str: str, X: float) -> dict:
    # 1) Validation date
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        raise ValueError("Format de date invalide. Utilise JJ-MM-AAAA.")
    date_norm = dt.strftime("%d-%m-%Y")

    # 2) Validation montant
    if X <= 0:
        raise ValueError("Le montant doit être strictement positif.")
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

    # 5) Réinvestissement selon ta nouvelle logique
    if X >= 3000:
        # Commission totale transformée en multiple de 500 -> C_tm
        C_tm = math.ceil(total_C / MEC_VALUE) * MEC_VALUE

        # Commission à réinvestir en MEC
        mec_commission_reinvestie = C_tm / MEC_VALUE

        # Somme ajoutée pour atteindre ce multiple
        Sa = C_tm - total_C

        # Commission supplémentaire générée
        Com_supp = 1.24 * C_tm

        # Revenu Global = intérêts + commission suppl. (comme dans main())
        Revenu_global = Com_supp + total_I

        # Nombre total de MEC (initial + MEC issues du réinvestissement)
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

    # 6) Enregistrement historique (mêmes champs que dans main())
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
        # Sur Render, le système de fichiers est éphémère → on ne bloque pas l’API
        pass

    return {
        "date": date_norm,
        "investissement": X,
        "niveaux": n_opt,
        "mec_par_niveau": mec,
        "capital_par_niveau": caps,
        "interets_par_niveau": interets,
        "commissions_par_niveau": commissions,
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


# =========================
# Endpoints FastAPI
# =========================

@app.get("/")
def root():
    return {"message": "MellionCoin API en ligne", "status": "ok"}


@app.get("/ping")
def ping():
    return {"ping": "pong"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    try:
        result = simulate_investment(request.date, request.montant)
        return SimulationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erreur serveur interne lors du calcul MellionCoin."
        )


@app.get("/history", response_model=list[HistoryRow])
def history():
    try:
        data = lo
