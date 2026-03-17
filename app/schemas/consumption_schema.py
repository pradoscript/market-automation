from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConsumptionCreate(BaseModel):
    product_name: str = Field(..., min_length=1, examples=["Frango"])
    quantity: float = Field(..., gt=0, examples=[0.5])
    unit: str = Field(..., min_length=1, max_length=20, examples=["kg"])


class ConsumptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: float
    unit: str
    created_at: datetime
