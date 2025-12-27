# FastAPI with UV Project

## 🚀 FastAPI คืออะไร?

**FastAPI** เป็น modern web framework สำหรับสร้าง API ด้วย Python ที่มีประสิทธิภาพสูง

### คุณสมบัติเด่นของ FastAPI

- **เร็วมาก** - ประสิทธิภาพเทียบเท่า NodeJS และ Go
- **Type Hints** - ใช้ Python type hints สำหรับ validation อัตโนมัติ
- **Auto Documentation** - สร้าง API docs (Swagger/OpenAPI) อัตโนมัติ
- **Easy to Learn** - เรียนรู้ง่าย syntax ชัดเจน
- **Production Ready** - พร้อมใช้งานจริง รองรับ async/await

### ตัวอย่าง FastAPI แบบครอบคลุม

```python
from fastapi import FastAPI, HTTPException, Query, Path, Body, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(
    title="My FastAPI Application",
    description="API สำหรับจัดการข้อมูล",
    version="1.0.0"
)

# ============================================
# Pydantic Models (Schema)
# ============================================

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="ชื่อสินค้า")
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0, description="ราคาต้องมากกว่า 0")
    tax: Optional[float] = Field(None, ge=0)
    tags: List[str] = []

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    tax: Optional[float] = None
    tags: Optional[List[str]] = None

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

# ============================================
# Fake Database
# ============================================

items_db = {}
item_counter = 1

# ============================================
# Dependency Functions
# ============================================

async def get_current_user(token: str = Query(..., description="Access token")):
    """ตรวจสอบ authentication (ตัวอย่าง)"""
    if token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(username="testuser", email="test@example.com")

# ============================================
# Basic Routes
# ============================================

@app.get("/", tags=["Root"])
async def read_root():
    """Homepage endpoint"""
    return {
        "message": "Welcome to FastAPI",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# Path Parameters
# ============================================

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def read_item(
    item_id: int = Path(..., gt=0, description="ID ของสินค้า")
):
    """ดึงข้อมูลสินค้าตาม ID"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.get("/users/{user_id}/items/{item_id}", tags=["Items"])
async def read_user_item(user_id: int, item_id: int):
    """Multiple path parameters"""
    return {"user_id": user_id, "item_id": item_id}

# ============================================
# Query Parameters
# ============================================

@app.get("/items/", response_model=List[ItemResponse], tags=["Items"])
async def list_items(
    skip: int = Query(0, ge=0, description="จำนวนที่ข้าม"),
    limit: int = Query(10, ge=1, le=100, description="จำนวนสูงสุด"),
    search: Optional[str] = Query(None, min_length=1, description="ค้นหาชื่อสินค้า"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    tags: List[str] = Query([], description="กรองตาม tags")
):
    """ดึงรายการสินค้าทั้งหมด พร้อม filter และ pagination"""
    result = list(items_db.values())
    
    # Filter by search
    if search:
        result = [item for item in result if search.lower() in item["name"].lower()]
    
    # Filter by price range
    if min_price is not None:
        result = [item for item in result if item["price"] >= min_price]
    if max_price is not None:
        result = [item for item in result if item["price"] <= max_price]
    
    # Filter by tags
    if tags:
        result = [item for item in result if any(tag in item["tags"] for tag in tags)]
    
    # Pagination
    return result[skip : skip + limit]

# ============================================
# POST (Create)
# ============================================

@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Items"]
)
async def create_item(item: ItemCreate):
    """สร้างสินค้าใหม่"""
    global item_counter
    
    new_item = {
        "id": item_counter,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "tax": item.tax,
        "tags": item.tags,
        "created_at": datetime.now()
    }
    
    items_db[item_counter] = new_item
    item_counter += 1
    
    return new_item

@app.post("/items/bulk/", tags=["Items"])
async def create_items_bulk(items: List[ItemCreate]):
    """สร้างหลายสินค้าพร้อมกัน"""
    created_items = []
    for item in items:
        result = await create_item(item)
        created_items.append(result)
    return {"created": len(created_items), "items": created_items}

# ============================================
# PUT (Update - Replace)
# ============================================

@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def update_item(
    item_id: int = Path(..., gt=0),
    item: ItemCreate = Body(...)
):
    """อัปเดตสินค้า (replace ทั้งหมด)"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = {
        "id": item_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "tax": item.tax,
        "tags": item.tags,
        "created_at": items_db[item_id]["created_at"]
    }
    
    items_db[item_id] = updated_item
    return updated_item

# ============================================
# PATCH (Partial Update)
# ============================================

@app.patch("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def partial_update_item(
    item_id: int = Path(..., gt=0),
    item: ItemUpdate = Body(...)
):
    """อัปเดตสินค้าบางส่วน"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    stored_item = items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        stored_item[field] = value
    
    items_db[item_id] = stored_item
    return stored_item

# ============================================
# DELETE
# ============================================

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
async def delete_item(item_id: int = Path(..., gt=0)):
    """ลบสินค้า"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items_db[item_id]
    return None

# ============================================
# Request Body Variations
# ============================================

@app.post("/items/{item_id}/tags/", tags=["Items"])
async def add_tags(
    item_id: int,
    tags: List[str] = Body(..., embed=True)
):
    """เพิ่ม tags ให้สินค้า"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    items_db[item_id]["tags"].extend(tags)
    return items_db[item_id]

@app.put("/items/{item_id}/price/", tags=["Items"])
async def update_price(
    item_id: int,
    price: float = Body(..., embed=True, gt=0)
):
    """อัปเดตเฉพาะราคา"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    items_db[item_id]["price"] = price
    return {"message": "Price updated", "new_price": price}

# ============================================
# Multiple Body Parameters
# ============================================

@app.post("/offers/", tags=["Advanced"])
async def create_offer(
    item: ItemCreate,
    user: User,
    importance: int = Body(..., gt=0, le=5)
):
    """รับหลาย body parameters"""
    return {
        "item": item,
        "user": user,
        "importance": importance
    }

# ============================================
# Dependency Injection
# ============================================

@app.get("/protected/", tags=["Auth"])
async def protected_route(current_user: User = Depends(get_current_user)):
    """Route ที่ต้อง authentication"""
    return {
        "message": f"Hello {current_user.username}",
        "user": current_user
    }

# ============================================
# Response Model และ Status Codes
# ============================================

@app.get("/items/{item_id}/summary/", tags=["Items"])
async def get_item_summary(item_id: int):
    """คืนค่าเฉพาะบางฟิลด์"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items_db[item_id]
    return {
        "id": item["id"],
        "name": item["name"],
        "price": item["price"]
    }

# ============================================
# Error Handling
# ============================================

@app.get("/items/{item_id}/error-demo/", tags=["Demo"])
async def error_demo(item_id: int):
    """ตัวอย่างการจัดการ error"""
    if item_id == 0:
        raise HTTPException(
            status_code=400,
            detail="Item ID cannot be zero"
        )
    if item_id < 0:
        raise HTTPException(
            status_code=400,
            detail="Item ID must be positive",
            headers={"X-Error": "Invalid-ID"}
        )
    return {"item_id": item_id}

# ============================================
# Async Operations
# ============================================

import asyncio

@app.get("/async-demo/", tags=["Demo"])
async def async_demo():
    """ตัวอย่างการใช้ async"""
    await asyncio.sleep(1)  # Simulate async operation
    return {"message": "Async operation completed"}

# ============================================
# Background Tasks
# ============================================

from fastapi import BackgroundTasks

def write_log(message: str):
    """Background task function"""
    with open("log.txt", "a") as f:
        f.write(f"{datetime.now()}: {message}\n")

@app.post("/send-notification/", tags=["Advanced"])
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    """ส่งงานไป background"""
    background_tasks.add_task(write_log, f"Notification sent to {email}")
    return {"message": "Notification sent in background"}

# ============================================
# File Upload
# ============================================

from fastapi import File, UploadFile

@app.post("/upload/", tags=["Files"])
async def upload_file(file: UploadFile = File(...)):
    """Upload ไฟล์"""
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }

@app.post("/upload-multiple/", tags=["Files"])
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload หลายไฟล์"""
    return {
        "files": [
            {"filename": file.filename, "size": len(await file.read())}
            for file in files
        ]
    }

# ============================================
# WebSocket
# ============================================

from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        await websocket.close()

# ============================================
# Startup และ Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """รันเมื่อ app เริ่มต้น"""
    print("Application starting up...")
    # Initialize database connection, load models, etc.

@app.on_event("shutdown")
async def shutdown_event():
    """รันเมื่อ app ปิด"""
    print("Application shutting down...")
    # Close database connections, cleanup resources, etc.
```

---

## 📦 UV คืออะไร?

**UV** เป็น package และ project manager สำหรับ Python ที่เขียนด้วย Rust

### ทำไมต้องใช้ UV?

- **เร็วกว่า pip/poetry มาก** - เร็วกว่า 10-100 เท่า
- **จัดการ Python versions** - ติดตั้งและสลับ Python version ได้
- **แก้ปัญหา dependency** - แก้ไข dependency conflicts อัตโนมัติ
- **รวมทุกอย่างไว้ที่เดียว** - ไม่ต้องใช้ pip, virtualenv, pyenv แยกกัน
- **Compatible** - ใช้ได้กับ `pyproject.toml` มาตรฐาน

### คำสั่ง UV พื้นฐาน

```bash
# ติดตั้ง dependencies
uv sync

# เพิ่ม package
uv add fastapi uvicorn

# รันคำสั่งใน environment
uv run python script.py
uv run uvicorn main:app --reload

# เปิด Python REPL
uv run python

# อัปเดต dependencies
uv lock --upgrade
```

---

## 🛠️ การเริ่มต้นใช้งานโปรเจคนี้

### 1. ติดตั้ง UV (ถ้ายังไม่มี)

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**หรือใช้ pip:**
```bash
pip install uv
```

### 2. ติดตั้ง Dependencies

```bash
cd my_fastapi
uv sync
```

### 3. รัน FastAPI Server

```bash
uv run uvicorn main:app --reload
```

หรือ

```bash
uv run uvicorn src.app:app --reload
```

### 4. เปิดดู API Documentation

เปิดเบราว์เซอร์:
- **API Docs (Scalar)**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

---

## 📁 โครงสร้างโปรเจค

```
my_fastapi/
├── .python-version      # Python version สำหรับโปรเจค
├── pyproject.toml       # Dependencies และ project config
├── uv.lock             # Lock file สำหรับ dependencies
├── main.py             # Entry point หลัก
└── src/
    ├── app.py          # FastAPI application
    └── crud.py         # CRUD operations
```

---

## 🔧 คำสั่งที่ใช้บ่อย

### จัดการ Dependencies

```bash
# เพิ่ม package
uv add requests pandas

# เพิ่ม dev dependencies
uv add --dev pytest black

# ลบ package
uv remove requests

# แสดง dependencies ที่ติดตั้ง
uv pip list
```

### Development

```bash
# รัน Python script
uv run python script.py

# รัน tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .
```

---

## 🎯 คำสั่ง FastAPI ทั้งหมด

### สร้างโปรเจค FastAPI ใหม่

```bash
# สร้างโปรเจคด้วย uv
uv init my-fastapi-project
cd my-fastapi-project

# เพิ่ม FastAPI และ dependencies
uv add fastapi uvicorn[standard]
uv add --dev pytest httpx
```

### รัน Development Server

```bash
# รันแบบพื้นฐาน
uv run uvicorn main:app

# รันพร้อม auto-reload (สำหรับ development)
uv run uvicorn main:app --reload

# กำหนด host และ port
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# รันหลาย workers (สำหรับ production)
uv run uvicorn main:app --workers 4

# รันพร้อม log level
uv run uvicorn main:app --reload --log-level debug

# รัน ASGI server อื่นๆ
uv run hypercorn main:app --reload
uv run daphne main:app
```

### ตรวจสอบและ Validate

```bash
# ดู OpenAPI schema
uv run python -c "from main import app; import json; print(json.dumps(app.openapi(), indent=2))"

# ตรวจสอบ routes ทั้งหมด
uv run python -c "from main import app; print(app.routes)"

# แสดง metadata ของ app
uv run python -c "from main import app; print(f'Title: {app.title}'); print(f'Version: {app.version}')"
```

### Testing

```bash
# รัน tests ทั้งหมด
uv run pytest

# รัน tests พร้อม coverage
uv run pytest --cov=src --cov-report=html

# รัน tests เฉพาะไฟล์
uv run pytest tests/test_main.py

# รัน tests พร้อม output ละเอียด
uv run pytest -v

# รัน tests แบบ watch mode
uv run pytest-watch
```

### ตัวอย่าง Test File

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1}
```

### Code Quality

```bash
# Format code ด้วย Black
uv run black .
uv run black src/ tests/

# Check code style ด้วย Ruff
uv add --dev ruff
uv run ruff check .
uv run ruff check --fix .

# Type checking ด้วย mypy
uv add --dev mypy
uv run mypy src/

# Security scan
uv add --dev bandit
uv run bandit -r src/
```

### Database Migrations (ถ้าใช้ Alembic)

```bash
# ติดตั้ง Alembic
uv add alembic sqlalchemy

# สร้าง alembic config
uv run alembic init alembic

# สร้าง migration
uv run alembic revision --autogenerate -m "Create users table"

# รัน migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# ดู migration history
uv run alembic history
```

### Production Deployment

```bash
# รัน production server ด้วย Gunicorn + Uvicorn workers
uv add gunicorn
uv run gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# สร้าง Docker image
docker build -t my-fastapi-app .
docker run -d -p 8000:8000 my-fastapi-app

# ใช้ Docker Compose
docker-compose up -d
docker-compose logs -f

# Deploy to cloud platforms
# Heroku
heroku create my-fastapi-app
git push heroku main

# Railway
railway up

# Render
# Push to GitHub และเชื่อมต่อกับ Render
```

### API Documentation

```bash
# เปิด Swagger UI
# ไปที่ http://localhost:8000/docs

# เปิด ReDoc
# ไปที่ http://localhost:8000/redoc

# ดาวน์โหลด OpenAPI JSON
curl http://localhost:8000/openapi.json > openapi.json

# สร้าง API client จาก OpenAPI spec
npx openapi-generator-cli generate -i openapi.json -g python -o client/
```

### Environment Management

```bash
# สร้าง .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here
DEBUG=True
EOF

# โหลด environment variables
uv add python-dotenv

# ในโค้ด
# from dotenv import load_dotenv
# load_dotenv()
```

### Monitoring และ Logging

```bash
# เพิ่ม logging
uv add loguru

# เพิ่ม monitoring
uv add prometheus-fastapi-instrumentator

# Health check endpoint
# GET /health
```

### Performance Testing

```bash
# ติดตั้ง tools
pip install locust httpie wrk

# ทดสอบด้วย httpie
http GET http://localhost:8000/

# ทดสอบด้วย Locust
uv add locust
uv run locust -f locustfile.py

# Load testing ด้วย wrk
wrk -t12 -c400 -d30s http://localhost:8000/
```

### ตัวอย่าง Locustfile

```python
# locustfile.py
from locust import HttpUser, task, between

class FastAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_root(self):
        self.client.get("/")
    
    @task(3)
    def get_items(self):
        self.client.get("/items/1")
```

### Debug Mode

```bash
# รันพร้อม debugger
uv run python -m debugpy --listen 5678 -m uvicorn main:app --reload

# ใช้ pdb
import pdb; pdb.set_trace()

# ใช้ ipdb (ดีกว่า pdb)
uv add --dev ipdb
import ipdb; ipdb.set_trace()
```

### Generate Code

```bash
# สร้าง models จาก database
uv add sqlacodegen
uv run sqlacodegen postgresql://user:pass@localhost/db

# สร้าง Pydantic models
uv add datamodel-code-generator
datamodel-code-generator --input schema.json --output models.py
```

### Useful FastAPI Packages

```bash
# Authentication
uv add fastapi-users[sqlalchemy]
uv add python-jose[cryptography] passlib[bcrypt]

# CORS
# (built-in in FastAPI)

# Rate limiting
uv add slowapi

# Caching
uv add fastapi-cache2[redis]

# File upload
uv add python-multipart

# WebSocket
# (built-in in FastAPI)

# Background tasks
uv add celery[redis]

# Admin panel
uv add sqladmin

# GraphQL
uv add strawberry-graphql[fastapi]
```

---

## 📚 Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### UV
- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [UV vs pip/poetry Comparison](https://docs.astral.sh/uv/pip/compatibility/)

---

## 💡 Tips

1. **ใช้ `uv run` เสมอ** - ให้แน่ใจว่าใช้ Python version ที่ถูกต้อง
2. **Auto-reload** - ใช้ `--reload` flag เมื่อ dev เพื่อรีสตาร์ทอัตโนมัติ
3. **Type hints** - ใช้ type hints ใน FastAPI เพื่อ validation อัตโนมัติ
4. **Environment Variables** - เก็บค่าสำคัญใน `.env` ไฟล์

---

## 📝 License

MIT License
