"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
- Order -> "order" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Hashed password or placeholder (demo)")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Full description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    stock: int = Field(0, ge=0, description="Items in stock")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    images: List[str] = Field(default_factory=list, description="Gallery image URLs")
    thumbnail: Optional[str] = Field(None, description="Primary image URL")
    featured: bool = Field(False, description="Featured on homepage")

class BlogPost(BaseModel):
    title: str = Field(..., description="Post title")
    excerpt: str = Field(..., description="Short excerpt")
    content: str = Field(..., description="Full content (markdown/plain)")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    author: str = Field("Admin", description="Author name")
    tags: List[str] = Field(default_factory=list)

class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    thumbnail: Optional[str] = None

class ShippingInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    postal_code: str
    country: str
    shipping_method: str = "standard"

class PaymentInfo(BaseModel):
    method: str = Field("cod", description="Payment method: cod, card, transfer (demo)")
    status: str = Field("pending", description="Payment status")

class Order(BaseModel):
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float
    total: float
    shipping: ShippingInfo
    payment: PaymentInfo
    status: str = Field("created", description="Order status")
