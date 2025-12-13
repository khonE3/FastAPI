# นำเข้า FastAPI จากไลบรารี fastapi
from fastapi import FastAPI, HTTPException

# นำเข้า BaseModel จากไลบรารี pydantic สำหรับการสร้าง Schema
from pydantic import BaseModel

# นำเข้า List และ Optional จากไลบรารี typing
from typing import List, Optional

# สำหรับ Scalar API reference
from scalar_fastapi import get_scalar_api_reference

# สร้างอินสแตนซ์ของแอปพลิเคชัน FastAPI
app = FastAPI()


# 1. จำลอง Database (In-memory)
fake_db = [
    {"id": 1, "name": "Laptop", "price": 25000, "stock": 5},
    {"id": 2, "name": "Mouse", "price": 500, "stock": 20}
]


# 2. สร้าง Schema สำหรับรับ/ส่งข้อมูล
class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int


class ProductUpdate(BaseModel): # สำหรับการอัปเดต (เลือกส่งบางค่าได้)
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


# เส้นทาง API สำหรับดู Scalar API reference
# Path: /scalar
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        # title="Scalar FastAPI API Reference",
        title=app.title,
    )

# --- API Endpoints ---
# สร้างเส้นทางสำหรับแสดงข้อความ "Hello, World!"
# สร้าง Method GET ที่เส้นทาง "/"
@app.get("/")
def read_root():
    return {"message": "CRUD Operations with FastAPI"}


# Read All: ดูสินค้าทั้งหมด
@app.get("/products", response_model=List[Product])
def get_products():
    return fake_db


# Read One: ดูสินค้าตาม ID
@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    # วนลูปหา ID ที่ตรงกัน
    for product in fake_db:
        if product["id"] == product_id:
            return product
    # ถ้าหาไม่เจอ ให้โยน Error 404
    # raise คือการโยนข้อผิดพลาด ต่างจาก return ที่เป็นการส่งค่าปกติ
    raise HTTPException(status_code=404, detail="Product not found")


# Create: เพิ่มสินค้าใหม่
@app.post("/products", response_model=Product, status_code=201)
def create_product(product: Product):
    # เช็คว่า ID ซ้ำไหม
    for p in fake_db:
        if p["id"] == product.id:
            raise HTTPException(status_code=400, detail="ID already exists")
    
    fake_db.append(product.model_dump()) # แปลง Pydantic เป็น Dict แล้วเก็บ
    return product


# Update: แก้ไขสินค้า
@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, update_data: ProductUpdate):
    for index, product in enumerate(fake_db): # enumerate เพื่อให้ได้ index ด้วย
        if product["id"] == product_id:
            # Copy ข้อมูลเดิมมา แล้วทับด้วยข้อมูลใหม่เฉพาะที่ส่งมา
            stored_item_model = Product(**product) # ** เพื่อแตก Dict เป็น keyword arguments
            update_data_dict = update_data.model_dump(exclude_unset=True)
            updated_item = stored_item_model.model_copy(update=update_data_dict)
            
            # บันทึกลง DB
            fake_db[index] = updated_item.model_dump()
            return updated_item
            
    raise HTTPException(status_code=404, detail="Product not found")


# Delete: ลบสินค้า
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for index, product in enumerate(fake_db):
        if product["id"] == product_id:
            fake_db.pop(index)
            return {"message": "Product deleted successfully"}
    raise HTTPException(status_code=404, detail="Product not found")