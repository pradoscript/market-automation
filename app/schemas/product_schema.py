from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Frango"])
    quantity: float = Field(..., gt=0, examples=[2.0])
    unit: str = Field(..., min_length=1, max_length=20, examples=["kg"])
    minimum_quantity: float = Field(..., ge=0, examples=[0.5])


class ProductUpdate(BaseModel):
    quantity: float = Field(..., gt=0, examples=[1.5])
    unit: str = Field(..., min_length=1, max_length=20, examples=["kg"])


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    quantity: float
    unit: str
    minimum_quantity: float
    created_at: datetime
    is_low_stock: bool = False
