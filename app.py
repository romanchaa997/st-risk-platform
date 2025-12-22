from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP

app = FastAPI(title="ST Risk PoC")

class CellInput(BaseModel):
    cell_id: int
    features: Dict[str, float | int]

class ScoreRequest(BaseModel):
    time: datetime
    horizon_sec: int
    cells: List[CellInput]
    n_scenarios: int = 5

class Scenario(BaseModel):
    scenario_id: int
    risk_value: float

class DistributionParams(BaseModel):
    p_event: float
    q05: float
    q50: float
    q95: float

class ZoneForecast(BaseModel):
    cell_id: int
    distribution_params: DistributionParams
    scenarios: List[Scenario]

class ScoreResponse(BaseModel):
    model_version: str
    time: datetime
    horizon_sec: int
    zones: List[ZoneForecast]

class ZoneRisk(BaseModel):
    cell_id: int
    p_event: float
    mean_risk: float
    q05: float
    q50: float
    q95: float

class RiskMapResponse(BaseModel):
    time: datetime
    horizon_sec: int
    aggregated: List[ZoneRisk]

@app.post("/score-snapshot", response_model=ScoreResponse)
async def score_snapshot(req: ScoreRequest) -> ScoreResponse:
    zones: List[ZoneForecast] = []
    for cell in req.cells:
        count_1h = float(cell.features.get("count_1h", 1))
        p = min(0.99, 0.01 * count_1h)
        zones.append(
            ZoneForecast(
                cell_id=cell.cell_id,
                distribution_params=DistributionParams(
                    p_event=p,
                    q05=p * 0.2,
                    q50=p * 0.7,
                    q95=min(1.0, p * 1.5),
                ),
                scenarios=[
                    Scenario(scenario_id=i, risk_value=p * (0.5 + i / req.n_scenarios))
                    for i in range(1, req.n_scenarios + 1)
                ],
            )
        )
    return ScoreResponse(
        model_version="poc_v1",
        time=req.time,
        horizon_sec=req.horizon_sec,
        zones=zones,
    )

@app.get("/risk-map", response_model=RiskMapResponse)
async def get_risk_map(time: datetime, horizon_sec: int) -> RiskMapResponse:
    aggregated = [
        ZoneRisk(cell_id=1, p_event=0.1, mean_risk=0.08, q05=0.01, q50=0.07, q95=0.2),
        ZoneRisk(cell_id=2, p_event=0.3, mean_risk=0.25, q05=0.10, q50=0.24, q95=0.5),
    ]
    return RiskMapResponse(time=time, horizon_sec=horizon_sec, aggregated=aggregated)

mcp = FastApiMCP(
    app,
    name="st-risk-mcp",
    description="Spatio-temporal risk PoC tools",
    base_url="http://localhost:8000"
)
mcp.mount_http()
