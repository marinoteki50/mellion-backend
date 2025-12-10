# core.py
import math
from datetime import datetime

from mellioncoin import (
    MEC_VALUE,
    optimized_distribution,
    compute_interets,
    compute_commissions,
)

def simulate_investment(date_str: str, X: float) -> dict:
    """
    Logique principale : à partir d'une date et d'un montant X,
    calcule tous les résultats (intérêts, commissions, MEC, rendement, etc.).
    Retourne un dict prêt à être converti en JSON.
    """

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

    # 3) Répartition optimisée (tu as déjà cette fonction)
    n_opt, mec, caps = optimized_distribution(X)

    # 4) Intérêts et commissions par niveau
    interets = compute_interets(caps)
    commissions = compute_commissions(caps)

    total_I = sum(interets)
    total_C = sum(commissions)
    total_MEC_initial = sum(mec)

    # 5) Logique de réinvestissement identique à ton main()

    if X >= 3000:
        # Commission totale arrondie au multiple de 500 le plus proche au-dessus
        C_tm = math.ceil(total_C / MEC_VALUE) * MEC_VALUE

        mec_commission_reinvestie = C_tm / MEC_VALUE
        Sa = C_tm - total_C
        Com_supp = 1.24 * C_tm

        Revenu_global = Com_supp + total_I
        total_MEC_global = total_MEC_initial + mec_commission_reinvestie
        denom = X + Sa
    else:
        # Pas de réinvestissement
        C_tm = 0.0
        Sa = 0.0
        Com_supp = 0.0
        mec_commission_reinvestie = 0.0
        Revenu_global = total_I + total_C
        total_MEC_global = total_MEC_initial
        denom = X

    r = Revenu_global / denom if denom != 0 else 0.0

    # 6) Préparer un résultat propre
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
