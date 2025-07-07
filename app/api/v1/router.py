from fastapi import APIRouter
from .endpoints import inscriptions, transactions

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