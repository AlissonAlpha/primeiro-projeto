from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.agents import router as agents_router
from api.routes.meta import router as meta_router
from api.routes.copy import router as copy_router
from api.routes.creatives import router as creatives_router

app = FastAPI(
    title="AI Marketing Agency",
    description="SaaS platform powered by AI agents for full-stack digital marketing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
app.include_router(copy_router, prefix="/api/v1")
app.include_router(creatives_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
