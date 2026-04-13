from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.health import router as health_router 
from routers.predict import router as predict_router

app = FastAPI(
    title="BDE AIRLINES"
)

# CORS API 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      
        "http://127.0.0.1:5173",           
        "http://flight_predictor_front:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(health_router)
app.include_router(predict_router)