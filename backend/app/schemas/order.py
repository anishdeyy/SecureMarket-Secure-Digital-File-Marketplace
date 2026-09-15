from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from datetime import datetime
import uuid

class OrderItemCreate(BaseModel):
    product_id: str

    @field_validator("product_id", mode="before")
    @classmethod
    def convert_id(cls, v):
        return str(v)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    id: str
    product_id: str
    price_at_purchase: float
    currency: str
    download_count: int
    download_limit: int
    download_enabled: bool
    product: Optional[dict] = None

    model_config = {"from_attributes": True}

class OrderOut(BaseModel):
    id: str
    order_number: str
    status: str
    total_amount: float
    currency: str
    risk_score: int
    risk_level: str
    items: List[OrderItemOut] = []
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
