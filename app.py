from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey, select, func
from sqlalchemy.orm import declarative_base, Session
from decimal import Decimal
import math

DATABASE_URL = "postgresql+psycopg2://postgres:5252@localhost:5432/practik_db"
engine = create_engine(DATABASE_URL, echo=True, future=True)
Base = declarative_base()

# ======== Models ========
class ProductType(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    coefficient = Column(Numeric(10, 2), nullable=False)

class MaterialType(Base):
    __tablename__ = "material_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    loss_percent = Column(Numeric(10, 6), nullable=False)

class Workshop(Base):
    __tablename__ = "workshops"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    workshop_type = Column(String, nullable=False)
    people_count = Column(Integer, nullable=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id"), nullable=False)
    material_type_id = Column(Integer, ForeignKey("material_types.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    article = Column(String, unique=True, nullable=False)
    min_partner_cost = Column(Numeric(14, 2), nullable=False)

class ProductWorkshop(Base):
    __tablename__ = "product_workshops"
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id"), primary_key=True)
    time_minutes = Column(Integer, nullable=False)

# ======== Schemas ========
class ProductOut(BaseModel):
    id: int
    name: str
    article: str
    min_partner_cost: Decimal
    product_type_id: int
    material_type_id: int
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    article: str
    min_partner_cost: Decimal = Field(..., ge=0)
    product_type_id: int = Field(..., ge=1)
    material_type_id: int = Field(..., ge=1)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    article: Optional[str] = None
    min_partner_cost: Optional[Decimal] = Field(default=None, ge=0)
    product_type_id: Optional[int] = Field(default=None, ge=1)
    material_type_id: Optional[int] = Field(default=None, ge=1)

class WorkshopOut(BaseModel):
    id: int
    name: str
    workshop_type: str
    people_count: int
    class Config:
        from_attributes = True

class ProductWorkshopOut(BaseModel):
    product_id: int
    workshop_id: int
    workshop_name: str
    workshop_type: str
    people_count: int
    time_minutes: int

class TotalTimeOut(BaseModel):
    product_id: int
    total_time_minutes: int
    total_time_hours_int: int

class MaterialCalcIn(BaseModel):
    product_type_id: int
    material_type_id: int
    count: int = Field(..., gt=0)

class MaterialCalcOut(BaseModel):
    required_amount: int

# ======== Utils ========
def calc_total_time_minutes(db: Session, product_id: int) -> int:
    total = db.execute(select(func.coalesce(func.sum(ProductWorkshop.time_minutes), 0)).where(ProductWorkshop.product_id == product_id)).scalar_one()
    return int(total)

def calc_required_material(db: Session, product_type_id: int, material_type_id: int, count: int) -> int:
    pt = db.get(ProductType, product_type_id)
    mt = db.get(MaterialType, material_type_id)
    if pt is None or mt is None:
        return -1
    return int(math.ceil(float(pt.coefficient) * count * (1 + float(mt.loss_percent))))

# ======== App ========
app = FastAPI(title="Furniture Products API")

# ======== CORS Middleware ========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "API работает"}

# ======== Products ========
@app.get("/products", response_model=List[ProductOut])
def list_products():
    with Session(engine) as db:
        return db.execute(select(Product)).scalars().all()

@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate):
    with Session(engine) as db:
        if db.get(ProductType, payload.product_type_id) is None:
            raise HTTPException(400, "product_type_id not found")
        if db.get(MaterialType, payload.material_type_id) is None:
            raise HTTPException(400, "material_type_id not found")
        product = Product(**payload.dict())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate):
    with Session(engine) as db:
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(404, "product not found")
        for field, value in payload.dict(exclude_none=True).items():
            setattr(product, field, value)
        db.commit()
        db.refresh(product)
        return product

# ======== Workshops ========
@app.get("/workshops", response_model=List[WorkshopOut])
def list_workshops():
    with Session(engine) as db:
        return db.execute(select(Workshop)).scalars().all()

@app.get("/products/{product_id}/workshops", response_model=List[ProductWorkshopOut])
def workshops_for_product(product_id: int):
    with Session(engine) as db:
        if db.get(Product, product_id) is None:
            raise HTTPException(404, "product not found")
        rows = db.execute(select(ProductWorkshop, Workshop).join(Workshop, Workshop.id == ProductWorkshop.workshop_id).where(ProductWorkshop.product_id == product_id)).all()
        return [ProductWorkshopOut(
            product_id=pw.product_id,
            workshop_id=pw.workshop_id,
            workshop_name=w.name,
            workshop_type=w.workshop_type,
            people_count=w.people_count,
            time_minutes=pw.time_minutes
        ) for pw, w in rows]

# ======== Total Time ========
@app.get("/products/{product_id}/total-time", response_model=TotalTimeOut)
def product_total_time(product_id: int):
    with Session(engine) as db:
        if db.get(Product, product_id) is None:
            raise HTTPException(404, "product not found")
        total_minutes = calc_total_time_minutes(db, product_id)
        hours = math.ceil(total_minutes / 60)
        return TotalTimeOut(
            product_id=product_id,
            total_time_minutes=total_minutes,
            total_time_hours_int=hours,
        )

# ======== Materials ========
@app.post("/materials/calc", response_model=MaterialCalcOut)
def materials_calc(payload: MaterialCalcIn):
    with Session(engine) as db:
        val = calc_required_material(db, payload.product_type_id, payload.material_type_id, payload.count)
        if val == -1:
            raise HTTPException(400, "invalid params")
        return MaterialCalcOut(required_amount=val)
