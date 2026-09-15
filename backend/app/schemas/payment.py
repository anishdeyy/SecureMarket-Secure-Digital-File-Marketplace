from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from datetime import datetime
import uuid

class PaymentCreate(BaseModel):
    order_id: Union[uuid.UUID, str]

class PaymentVerify(BaseModel):
    order_id: Union[uuid.UUID, str]
    payment_data: Dict[str, Any]

class PaymentOut(BaseModel):
    id: Union[uuid.UUID, str]
    order_id: Union[uuid.UUID, str]
    amount: float
    currency: str
    status: str
    gateway: str
    is_mock: bool
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
