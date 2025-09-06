import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session

from app.api import auth, sessions, favorites, reviews, categories, promotions, products,notifications,orders, checkout, debug, models, vectors
from app.core.database import engine
from app.initial_data import seed_initial_data
from app.services.ai_service import model_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup...")
    # Tạo session và seed dữ liệu
    with Session(engine) as session:
        seed_initial_data(session)
    
    # Lên lịch cho việc tải model AI chạy ở chế độ nền
    # Server sẽ không chờ tác vụ này hoàn thành
    asyncio.create_task(model_manager.load_models_background())

    print("Startup complete. Server is now online and accepting requests.")
    print("AI models are being loaded in the background...")
    yield
    # Đây là phần shutdown, nếu muốn thêm logic shutdown thì đặt ở đây
    print("Application shutdown...")

app = FastAPI(
    title="Smart Cart Backend API",
    description="Backend services for the Smart Cart system.",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers from the api module
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(favorites.router)
app.include_router(reviews.router)
app.include_router(categories.router)
app.include_router(promotions.router)
app.include_router(products.router)
app.include_router(notifications.router)
app.include_router(orders.router)
app.include_router(checkout.router)
app.include_router(debug.router) # Thêm router debug
app.include_router(models.router) # Thêm router cho AI Models
app.include_router(vectors.router)

@app.get("/", tags=["Root"])
async def root():
    """A simple welcome message to verify the server is running."""
    return {"message": "Welcome to the Smart Cart Backend API!"}