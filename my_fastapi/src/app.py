# นำเข้า FastAPI จากไลบรารี fastapi
from fastapi import FastAPI

# นำเข้า BaseModel จากไลบรารี pydantic สำหรับการสร้าง Schema
from pydantic import BaseModel

# สำหรับ Scalar API reference
from scalar_fastapi import get_scalar_api_reference

# สร้างอินสแตนซ์ของแอปพลิเคชัน FastAPI
app = FastAPI()


# สร้าง Schema (พิมพ์เขียว) ของข้อมูลที่คาดว่าจะได้รับใน Request Body
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


# เส้นทาง API สำหรับดู Scalar API reference
# Path: /scalar
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        # title="Scalar FastAPI API Reference",
        title=app.title,
    )


# สร้างเส้นทางสำหรับแสดงข้อความ "Hello, World!"
# สร้าง Method GET ที่เส้นทาง "/"
@app.get("/")
def read_root():
    return {"message": "Hello, World from FastAPI!"}


@app.get("/about")
def read_about():
    return {"message": "This is simple About path api"}


@app.get("/products")
def read_products():
    return {"message": "List of products"}


@app.post("/products")
def create_product():
    return {"message": "Create a new product"}


@app.put("/products")
def update_product():
    return {"message": "Update an existing product"}


@app.patch("/products")
def partial_update_product():
    return {"message": "Partially update a product"}


@app.delete("/products")
def delete_product():
    return {"message": "Delete a product"}


# Route แบบมี parameter
@app.get("/users/{user_id}")
def get_user(user_id: int):  # FastAPI จะแปลงเป็น int ให้เอง
    return {"user_id": user_id + 1}


# Route แบบมี Query String
@app.get("/items/")
def get_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}


# สร้างเส้นทาง (route) สำหรับสร้างไอเท็มใหม่จากข้อมูลใน request body
@app.post("/items/")
def create_item(item: Item):
    return {"item_name": item.name, "price_with_tax": item.price * 1.07}
