# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core import simulate_investment

app = FastAPI(title="MellionCoin API")

class SimulationRequest(BaseModel):
    date: str = Field(..., example="10-12-2025", description="Format JJ-MM-AAAA")
    montant: float = Field(..., gt=0, example=5000, description="Montant en USD")

class SimulationResponse(BaseModel):
    date: str
    investissement: float
    niveaux: int
    mec_par_niveau: list[int]
    capital_par_niveau: list[float]
    interets_totaux: float
    commissions_totales: float
    commission_supplementaire: float
    revenu_global: float
    mec_total: float
    rendement_pourcent: float

@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    try:
        result = simulate_investment(request.date, request.montant)
        # On sélectionne ce qu'on renvoie au mobile (pas obligé de tout exposer)
        return SimulationResponse(
            date=result["date"],
            investissement=result["investissement"],
            niveaux=result["niveaux"],
            mec_par_niveau=result["mec_par_niveau"],
            capital_par_niveau=result["capital_par_niveau"],
            interets_totaux=result["interets_totaux"],
            commissions_totales=result["commissions_totales"],
            commission_supplementaire=result["commission_supplementaire"],
            revenu_global=result["revenu_global"],
            mec_total=result["mec_total"],
            rendement_pourcent=result["rendement_pourcent"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur serveur interne")
