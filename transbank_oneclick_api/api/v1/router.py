from fastapi import APIRouter
from .endpoints import inscriptions, transactions, callbacks

api_router = APIRouter()

api_router.include_router(
    inscriptions.router,
    prefix="/oneclick/mall/inscription",
    tags=["inscriptions"]
)

api_router.include_router(
    transactions.router,
    prefix="/oneclick/mall/transaction",
    tags=["transactions"]
)

api_router.include_router(
    callbacks.router,
    prefix="/callbacks",
    tags=["testing", "callbacks"]
)