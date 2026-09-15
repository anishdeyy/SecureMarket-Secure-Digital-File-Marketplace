from pydantic import BaseModel, field_validator
from typing import Optional, List, Any, Dict, Union
from datetime import datetime
import uuid

class ProductCreate(BaseModel):
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = []
    keywords: Optional[List[str]] = []
    language: Optional[str] = "English"
    difficulty: Optional[str] = None
    price: float
    currency: Optional[str] = "INR"
    version: Optional[str] = "1.0"
    num_pages: Optional[int] = None

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        if v > 100000:
            raise ValueError("Price exceeds maximum allowed")
        return v

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    price: Optional[float] = None
    version: Optional[str] = None
    num_pages: Optional[int] = None

class SellerOut(BaseModel):
    id: Union[uuid.UUID, str]
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    seller_approved: bool

    model_config = {"from_attributes": True}

class ProductOut(BaseModel):
    id: Union[uuid.UUID, str]
    title: str
    short_description: Optional[str]
    description: Optional[str]
    summary: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    tags: Optional[List[str]]
    keywords: Optional[List[str]]
    language: Optional[str]
    difficulty: Optional[str]
    original_filename: Optional[str]
    file_extension: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    sha256_hash: Optional[str]
    version: Optional[str]
    num_pages: Optional[int]
    price: float
    currency: Optional[str]
    preview_image_url: Optional[str]
    status: str
    scan_status: str
    is_featured: bool
    total_sales: int
    total_downloads: int
    avg_rating: float
    review_count: int
    view_count: int
    ai_metadata_generated: bool
    seller_id: Union[uuid.UUID, str]
    seller: Optional[SellerOut] = None
    created_at: datetime
    published_at: Optional[datetime]

    model_config = {"from_attributes": True}

class ProductListOut(BaseModel):
    id: Union[uuid.UUID, str]
    title: str
    short_description: Optional[str]
    category: Optional[str]
    price: float
    currency: Optional[str]
    preview_image_url: Optional[str]
    scan_status: str
    sha256_hash: Optional[str]
    avg_rating: float
    review_count: int
    total_sales: int
    file_extension: Optional[str]
    seller: Optional[SellerOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}
