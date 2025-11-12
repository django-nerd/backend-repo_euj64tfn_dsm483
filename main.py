import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, BlogPost as BlogPostSchema, Order as OrderSchema, User as UserSchema

app = FastAPI(title="Ecommerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utils ----------
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id")) if doc.get("_id") else None
    return doc


# ---------- Seed Data on First Run ----------

def seed_database():
    if db is None:
        return
    # Products
    if db["product"].count_documents({}) == 0:
        sample_products = [
            {
                "title": "Glass Card Pro",
                "description": "Premium transparent credit card with NFC and rewards.",
                "price": 199.0,
                "category": "Cards",
                "stock": 50,
                "rating": 4.8,
                "images": [
                    "https://images.unsplash.com/photo-1556742393-d75f468bfcb0?auto=format&fit=crop&w=1200&q=60",
                    "https://images.unsplash.com/photo-1542744094-24638eff58bb?auto=format&fit=crop&w=1200&q=60",
                ],
                "thumbnail": "https://images.unsplash.com/photo-1556742393-d75f468bfcb0?auto=format&fit=crop&w=800&q=60",
                "featured": True,
            },
            {
                "title": "Metal Card X",
                "description": "Brushed metal card with concierge and lounge access.",
                "price": 299.0,
                "category": "Cards",
                "stock": 20,
                "rating": 4.9,
                "images": [
                    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1200&q=60",
                ],
                "thumbnail": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=60",
                "featured": True,
            },
            {
                "title": "Card Sleeve",
                "description": "Minimalist leather sleeve with RFID protection.",
                "price": 29.0,
                "category": "Accessories",
                "stock": 200,
                "rating": 4.6,
                "images": [
                    "https://images.unsplash.com/photo-1555529771-35a38c3c12c1?auto=format&fit=crop&w=1200&q=60",
                ],
                "thumbnail": "https://images.unsplash.com/photo-1555529771-35a38c3c12c1?auto=format&fit=crop&w=800&q=60",
                "featured": False,
            },
        ]
        db["product"].insert_many(sample_products)

    # Blog posts
    if db["blogpost"].count_documents({}) == 0:
        sample_posts = [
            {
                "title": "Designing the Future of Payments",
                "excerpt": "A look into glassmorphism and 3D in fintech UI.",
                "content": "Modern fintech combines security and delightful experiences...",
                "thumbnail": "https://images.unsplash.com/photo-1553729459-efe14ef6055d?auto=format&fit=crop&w=1000&q=60",
                "author": "Admin",
                "tags": ["design", "fintech"],
            },
            {
                "title": "How We Built Metal Card X",
                "excerpt": "Materials, durability, and sustainable sourcing.",
                "content": "The Metal Card X project started with a mission...",
                "thumbnail": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1000&q=60",
                "author": "Admin",
                "tags": ["hardware", "product"],
            },
        ]
        db["blogpost"].insert_many(sample_posts)

seed_database()


# ---------- Basic ----------
@app.get("/")
def read_root():
    return {"message": "Ecommerce Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response


# ---------- Products ----------
@app.get("/api/products")
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    featured: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    if db is None:
        return []
    filt = {}
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    if category:
        filt["category"] = category
    price_range = {}
    if min_price is not None:
        price_range["$gte"] = min_price
    if max_price is not None:
        price_range["$lte"] = max_price
    if price_range:
        filt["price"] = price_range
    if min_rating is not None:
        filt["rating"] = {"$gte": min_rating}
    if featured is not None:
        filt["featured"] = featured

    cursor = db["product"].find(filt).skip(skip).limit(limit)
    items = [serialize_doc(x) for x in cursor]
    return items

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return serialize_doc(doc)


# ---------- Blog ----------
@app.get("/api/blogs")
def list_blogs(limit: int = Query(20, ge=1, le=100), skip: int = Query(0, ge=0)):
    if db is None:
        return []
    cursor = db["blogpost"].find({}).sort("_id", -1).skip(skip).limit(limit)
    return [serialize_doc(x) for x in cursor]

@app.get("/api/blogs/{post_id}")
def get_blog(post_id: str):
    if db is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        doc = db["blogpost"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return serialize_doc(doc)


# ---------- Orders / Checkout ----------
class OrderIn(OrderSchema):
    pass

class OrderOut(BaseModel):
    order_id: str
    status: str
    payment_url: Optional[str] = None

@app.post("/api/orders", response_model=OrderOut)
def create_order(order: OrderIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    order_dict = order.model_dump()
    order_dict["payment"] = order_dict.get("payment", {"method": "cod", "status": "pending"})
    inserted_id = db["order"].insert_one(order_dict).inserted_id
    # Simulate payment URL
    payment_url = f"https://example-pay.test/checkout/{inserted_id}"
    return {"order_id": str(inserted_id), "status": "created", "payment_url": payment_url}


# ---------- Contact ----------
class ContactIn(BaseModel):
    name: str
    email: str
    message: str

@app.post("/api/contact")
def submit_contact(payload: ContactIn):
    if db is None:
        return {"status": "received"}
    _id = create_document("contact", payload.model_dump())
    return {"status": "ok", "id": _id}


# ---------- Auth (demo only) ----------
class RegisterIn(BaseModel):
    name: str
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
def register(user: RegisterIn):
    if db is None:
        return {"status": "ok"}
    existing = db["user"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    _id = create_document("user", user.model_dump())
    return {"status": "ok", "user_id": _id}

@app.post("/api/auth/login")
def login(payload: LoginIn):
    if db is None:
        return {"status": "ok", "token": "demo-token"}
    found = db["user"].find_one({"email": payload.email, "password": payload.password})
    if not found:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "ok", "token": "demo-token", "user": serialize_doc(found)}


# ---------- Schemas endpoint (optional helper) ----------
@app.get("/schema")
def schema_overview():
    return {
        "collections": [
            "user", "product", "blogpost", "order", "contact"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
