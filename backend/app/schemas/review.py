from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import uuid

class ReviewCreate(BaseModel):
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    comment: Optional[str] = None
    order_id: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_valid(cls, v):
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError("Rating must be an integer between 1 and 5")
        return v

    def get_comment_text(self) -> str:
        text = self.comment or self.body or ""
        return text.strip()

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_valid(cls, v):
        if v is not None and (not isinstance(v, int) or v < 1 or v > 5):
            raise ValueError("Rating must be an integer between 1 and 5")
        return v

    def get_comment_text(self) -> Optional[str]:
        if self.comment is not None:
            return self.comment.strip()
        if self.body is not None:
            return self.body.strip()
        return None

class ReviewOut(BaseModel):
    id: str
    user_id: str
    product_id: str
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    is_verified_purchase: bool = True
    status: str = "active"
    username: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
