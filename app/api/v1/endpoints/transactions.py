from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
from datetime import datetime

from app.database import get_db
from app.services.transbank_service import TransbankService
from app.api.deps import get_transbank_service
from app.schemas.oneclick_schemas import (
    TransactionAuthorizeRequest,
    TransactionAuthorizeResponse,
    TransactionStatusResponse,
    TransactionCaptureRequest,
    TransactionCaptureResponse,
    TransactionRefundRequest,
    TransactionRefundResponse,
    TransactionHistoryResponse,
    TransactionDetailResponse
)
from app.schemas.response_models import ApiResponse
from app.models.oneclick_transaction import OneclickTransaction, OneclickTransactionDetail
from app.models.oneclick_inscription import OneclickInscription
from app.core.structured_logger import StructuredLogger
from app.core.exceptions import (
    UsuarioNoEncontradoException,
    InscripcionNoEncontradaException,
    OrdenCompraDuplicadaException
)

router = APIRouter()
logger = StructuredLogger(__name__)


@router.post("/authorize", response_model=ApiResponse[TransactionAuthorizeResponse])
async def authorize_transaction(
    request: TransactionAuthorizeRequest,
    transbank_service: TransbankService = Depends(get_transbank_service),
    db: Session = Depends(get_db)
):
    """Authorize mall transaction using inscribed card"""
    try:
        # Check if parent_buy_order already exists
        existing_transaction = db.query(OneclickTransaction).filter(
            OneclickTransaction.parent_buy_order == request.parent_buy_order
        ).first()
        
        if existing_transaction:
            raise OrdenCompraDuplicadaException(request.parent_buy_order)
        
        # Find inscription
        inscription = db.query(OneclickInscription).filter(
            OneclickInscription.username == request.username,
            OneclickInscription.tbk_user == request.tbk_user,
            OneclickInscription.is_active == True
        ).first()
        
        if not inscription:
            raise InscripcionNoEncontradaException(request.tbk_user)
        
        # Prepare transaction details for Transbank
        details = [
            {
                "commerce_code": detail.commerce_code,
                "buy_order": detail.buy_order,
                "amount": detail.amount,
                "installments_number": detail.installments_number
            }
            for detail in request.details
        ]
        
        # Authorize with Transbank
        result = await transbank_service.authorize_transaction(
            username=request.username,
            tbk_user=request.tbk_user,
            parent_buy_order=request.parent_buy_order,
            details=details
        )
        
        # Calculate total amount
        total_amount = sum(detail.amount for detail in request.details)
        
        # Save transaction to database
        transaction = OneclickTransaction(
            id=str(uuid.uuid4()),
            username=request.username,
            inscription_id=inscription.id,
            parent_buy_order=request.parent_buy_order,
            session_id=result["session_id"],
            transaction_date=datetime.fromisoformat(result["transaction_date"].replace("Z", "+00:00")),
            accounting_date=result["accounting_date"],
            total_amount=total_amount,
            card_number_masked=result["card_detail"]["card_number"],
            status="processed",
            raw_response=json.dumps(result)
        )
        
        db.add(transaction)
        db.flush()  # Get the transaction ID
        
        # Save transaction details
        for detail_data in result["details"]:
            detail = OneclickTransactionDetail(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                commerce_code=detail_data["commerce_code"],
                buy_order=detail_data["buy_order"],
                amount=detail_data["amount"],
                authorization_code=detail_data.get("authorization_code"),
                payment_type_code=detail_data.get("payment_type_code"),
                response_code=detail_data["response_code"],
                installments_number=detail_data["installments_number"],
                status=detail_data["status"],
                balance=detail_data.get("balance")
            )
            db.add(detail)
        
        db.commit()
        
        # Prepare response
        response_details = [
            TransactionDetailResponse(
                amount=detail["amount"],
                status=detail["status"],
                authorization_code=detail.get("authorization_code"),
                payment_type_code=detail.get("payment_type_code"),
                response_code=detail["response_code"],
                installments_number=detail["installments_number"],
                commerce_code=detail["commerce_code"],
                buy_order=detail["buy_order"],
                balance=detail.get("balance")
            )
            for detail in result["details"]
        ]
        
        response_data = TransactionAuthorizeResponse(
            parent_buy_order=result["parent_buy_order"],
            session_id=result["session_id"],
            card_detail=result["card_detail"],
            accounting_date=result["accounting_date"],
            transaction_date=result["transaction_date"],
            details=response_details
        )
        
        logger.with_contexts(username=request.username, transaction_id=transaction.id, parent_buy_order=request.parent_buy_order, total_amount=total_amount, details_count=len(details)).info(
            "Transaction authorized successfully"
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.with_context("username", request.username).error(
            f"Error authorizing transaction: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.get("/status/{child_buy_order}", response_model=ApiResponse[TransactionStatusResponse])
async def get_transaction_status(
    child_buy_order: str,
    child_commerce_code: str = Query(..., description="Child commerce code"),
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """Get transaction status from Transbank"""
    try:
        result = await transbank_service.get_transaction_status(
            child_buy_order=child_buy_order,
            child_commerce_code=child_commerce_code
        )
        
        response_details = [
            TransactionDetailResponse(
                amount=detail["amount"],
                status=detail["status"],
                authorization_code=detail.get("authorization_code"),
                payment_type_code=detail.get("payment_type_code"),
                response_code=detail["response_code"],
                installments_number=detail["installments_number"],
                commerce_code=detail["commerce_code"],
                buy_order=detail["buy_order"],
                balance=detail.get("balance")
            )
            for detail in result["details"]
        ]
        
        response_data = TransactionStatusResponse(
            buy_order=result["buy_order"],
            session_id=result["session_id"],
            card_detail=result["card_detail"],
            accounting_date=result["accounting_date"],
            transaction_date=result["transaction_date"],
            details=response_details
        )
        
        logger.info(
            "Transaction status retrieved successfully",
            context={
                "child_buy_order": child_buy_order,
                "child_commerce_code": child_commerce_code
            }
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error getting transaction status: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.put("/capture", response_model=ApiResponse[TransactionCaptureResponse])
async def capture_transaction(
    request: TransactionCaptureRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """Capture deferred transaction"""
    try:
        result = await transbank_service.capture_transaction(
            child_commerce_code=request.child_commerce_code,
            child_buy_order=request.child_buy_order,
            authorization_code=request.authorization_code,
            capture_amount=request.capture_amount
        )
        
        response_data = TransactionCaptureResponse(
            authorization_code=result["authorization_code"],
            authorization_date=result["authorization_date"],
            captured_amount=result["captured_amount"],
            response_code=result["response_code"]
        )
        
        logger.info(
            "Transaction captured successfully",
            context={
                "child_buy_order": request.child_buy_order,
                "captured_amount": request.capture_amount
            }
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error capturing transaction: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.post("/refund", response_model=ApiResponse[TransactionRefundResponse])
async def refund_transaction(
    request: TransactionRefundRequest,
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """Refund/reverse transaction"""
    try:
        result = await transbank_service.refund_transaction(
            child_commerce_code=request.child_commerce_code,
            child_buy_order=request.child_buy_order,
            amount=request.amount
        )
        
        response_data = TransactionRefundResponse(
            type=result["type"],
            response_code=result["response_code"],
            reversed_amount=result["reversed_amount"]
        )
        
        logger.info(
            "Transaction refunded successfully",
            context={
                "child_buy_order": request.child_buy_order,
                "reversed_amount": request.amount
            }
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error refunding transaction: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.get("/history/{username}", response_model=ApiResponse[TransactionHistoryResponse])
async def get_transaction_history(
    username: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    db: Session = Depends(get_db)
):
    """Get transaction history for a user"""
    try:
        # Build query
        query = db.query(OneclickTransaction).filter(
            OneclickTransaction.username == username
        )
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(OneclickTransaction.transaction_date >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(OneclickTransaction.transaction_date <= end_dt)
        
        if status:
            query = query.filter(OneclickTransaction.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        transactions = query.offset(offset).limit(limit).all()
        
        # Prepare response
        transaction_items = []
        for transaction in transactions:
            detail_responses = [
                TransactionDetailResponse(
                    amount=detail.amount,
                    status=detail.status,
                    authorization_code=detail.authorization_code,
                    payment_type_code=detail.payment_type_code,
                    response_code=detail.response_code,
                    installments_number=detail.installments_number,
                    commerce_code=detail.commerce_code,
                    buy_order=detail.buy_order,
                    balance=detail.balance
                )
                for detail in transaction.details
            ]
            
            transaction_items.append({
                "parent_buy_order": transaction.parent_buy_order,
                "transaction_date": transaction.transaction_date.isoformat(),
                "total_amount": transaction.total_amount,
                "card_number": transaction.card_number_masked,
                "status": transaction.status,
                "details": detail_responses
            })
        
        response_data = TransactionHistoryResponse(
            username=username,
            transactions=transaction_items,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        )
        
        logger.with_contexts(username=username, page=page, limit=limit, total=total).info(
            f"Retrieved {len(transaction_items)} transactions"
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.with_context("username", username).error(
            f"Error getting transaction history: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise