from fastapi import FastAPI

from app.routes import conversas, health
app = FastAPI(
    title="Mini Atendente",
    description="API de atendimento virtual que responde clientes com base em uma FAQ.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(conversas.router)