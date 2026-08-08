from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import animals

app = FastAPI(
    title="GScience API for testing AI models",
    description="Interactive FastAPI Docs",
    version="1.0.0",
)

# 2. Include endpoint routes (best practice: add prefix and tags)
# 2. Include the animals router
app.include_router(
    animals.router,
    prefix="/animals",
    tags=["Animals"],
)

# Specify the origins that are allowed to make requests to your API
origins = [
    "http://localhost:4200",  # Default Angular dev server
    "https://gscience-ai-ui.onrender.com", # dev python server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # List of allowed origins
    allow_credentials=True,           # Allow cookies / authentication headers
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Allow all headers
)

@app.get("/")
def root():
    return {"message": "API is running"}

