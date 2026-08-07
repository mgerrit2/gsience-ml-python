from fastapi import FastAPI

from src.routes import animals

app = FastAPI(
    title="GScience API",
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

@app.get("/")
def root():
    return {"message": "API is running"}

