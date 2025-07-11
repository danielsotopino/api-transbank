from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from transbank_oneclick_api.database import get_db
from transbank_oneclick_api.services.transbank_service import TransbankService
from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.schemas.oneclick_schemas import (
    InscriptionStartRequest,
    InscriptionStartResponse,
    InscriptionFinishRequest,
    InscriptionFinishResponse,
    InscriptionDeleteRequest,
    InscriptionDeleteResponse,
    InscriptionListResponse,
    InscriptionInfo
)
from transbank_oneclick_api.schemas.response_models import ApiResponse
from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription
from transbank_oneclick_api.core.structured_logger import StructuredLogger
from transbank_oneclick_api.core.exceptions import (
    UserNotFoundedException,
    InscriptionNotFoundException
)
from transbank_oneclick_api.config import settings

router = APIRouter()
logger = StructuredLogger(__name__)


@router.post("/start", response_model=ApiResponse[InscriptionStartResponse])
async def start_inscription(
    request: InscriptionStartRequest,
    transbank_service: TransbankService = Depends(get_transbank_service),
    db: Session = Depends(get_db)
):
    """Start card inscription process"""
    try:
        result = await transbank_service.start_inscription(
            username=request.username,
            email=request.email,
            response_url=request.response_url
        )
        
        response_data = InscriptionStartResponse(
            token=result["token"],
            url_webpay=result["url_webpay"]
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error starting inscription: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.put("/finish", response_model=ApiResponse[InscriptionFinishResponse])
async def finish_inscription(
    request: InscriptionFinishRequest,
    transbank_service: TransbankService = Depends(get_transbank_service),
    db: Session = Depends(get_db)
):
    """Finish card inscription process"""
    try:
        result = await transbank_service.finish_inscription(token=request.token)
        
        # Save inscription to database
        inscription = OneclickInscription(
            id=str(uuid.uuid4()),
            username=request.username,
            email=None,  # No disponible en el resultado, requiere refactor para persistir desde start
            tbk_user=result["tbk_user"],
            card_type=result["card_type"],
            card_number_masked=result["card_number"],
            authorization_code=result["authorization_code"],
            inscription_date=datetime.utcnow(),
            is_active=True,
            is_default=False
        )
        
        db.add(inscription)
        db.commit()
        db.refresh(inscription)
        
        response_data = InscriptionFinishResponse(
            tbk_user=result["tbk_user"],
            response_code=result["response_code"],
            authorization_code=result["authorization_code"],
            card_type=result["card_type"],
            card_number=result["card_number"]
        )
        
        logger.info(
            "Inscription completed successfully",
            context={
                "inscription_id": inscription.id,
                "card_type": result["card_type"],
                "card_number": result["card_number"]
            }
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error finishing inscription: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise


@router.delete("/delete", response_model=ApiResponse[InscriptionDeleteResponse])
async def delete_inscription(
    request: InscriptionDeleteRequest,
    transbank_service: TransbankService = Depends(get_transbank_service),
    db: Session = Depends(get_db)
):
    """Delete card inscription"""
    try:
        # Find inscription in database
        inscription = db.query(OneclickInscription).filter(
            OneclickInscription.tbk_user == request.tbk_user,
            OneclickInscription.username == request.username,
            OneclickInscription.is_active == True
        ).first()
        
        if not inscription:
            raise InscriptionNotFoundException(request.tbk_user)
        
        # Delete from Transbank
        await transbank_service.delete_inscription(
            tbk_user=request.tbk_user,
            username=request.username
        )
        
        # Mark as inactive in database
        inscription.is_active = False
        setattr(inscription, 'updated_at', datetime.utcnow())
        db.commit()
        
        response_data = InscriptionDeleteResponse(
            tbk_user=request.tbk_user,
            username=request.username,
            status="deleted",
            deletion_date=datetime.utcnow()
        )
        
        logger.info(
            "Inscription deleted successfully",
            context={"inscription_id": inscription.id}
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error deleting inscription: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise



@router.get("/{username}", response_model=ApiResponse[InscriptionListResponse])
async def list_user_inscriptions(
    username: str,
    db: Session = Depends(get_db)
):
    """Get all active inscriptions for a user"""
    try:
        inscriptions = db.query(OneclickInscription).filter(
            OneclickInscription.username == username,
            OneclickInscription.is_active == True
        ).all()
        
        inscription_list = [
            InscriptionInfo(
                tbk_user=inscription.tbk_user,
                card_type=inscription.card_type,
                card_number=inscription.card_number_masked,
                inscription_date=inscription.inscription_date,
                status="active",
                is_default=inscription.is_default
            )
            for inscription in inscriptions
        ]
        
        response_data = InscriptionListResponse(
            username=username,
            inscriptions=inscription_list,
            total_inscriptions=len(inscription_list)
        )
        
        logger.info(
            f"Retrieved {len(inscription_list)} inscriptions",
            context={"username": username, "total_inscriptions": len(inscription_list)}
        )
        
        return ApiResponse.success_response(response_data)
        
    except Exception as e:
        logger.error(
            f"Error retrieving inscriptions: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        raise