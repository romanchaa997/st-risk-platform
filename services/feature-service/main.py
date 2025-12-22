from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import datetime

app = FastAPI(title="Feature Service")

class FeatureRequest(BaseModel):
    cell_ids: List[int]
    timestamp: datetime.datetime
    features: List[str]

class FeatureValue(BaseModel):
    cell_id: int
    values: Dict[str, float]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/get-features", response_model=List[FeatureValue])
async def get_features(request: FeatureRequest):
    # Mock implementation of feature retrieval from ClickHouse/Postgres
    return [
        FeatureValue(cell_id=cid, values={f: 0.5 for f in request.features})
        for cid in request.cell_ids
    ]
