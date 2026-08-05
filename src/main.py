from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="Interactive FastAPI Docs",
    version="1.0.0",
)




@app.get("/")
def root():
    return {"message": "API is running"}

