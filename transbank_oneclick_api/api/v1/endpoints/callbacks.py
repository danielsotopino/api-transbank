from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import structlog
from transbank_oneclick_api.database import get_db
from transbank_oneclick_api.services.transbank_service import TransbankService
from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/inscription/result", response_class=HTMLResponse)
async def inscription_result_callback(
    TBK_TOKEN: str = Query(..., description="Token returned by Transbank"),
    transbank_service: TransbankService = Depends(get_transbank_service),
    db: Session = Depends(get_db)
):
    """
    Handle the inscription result callback from Transbank.
    This endpoint receives the TBK_TOKEN and processes the inscription completion.
    This is primarily used for testing and callback handling.
    """
    try:
        logger.info(
            "Processing inscription result from Transbank",
            context={"token": TBK_TOKEN[:10] + "..."}
        )
        
        # Call the transbank service to finish the inscription
        result = await transbank_service.finish_inscription(token=TBK_TOKEN)
        
        # Check if the inscription was successful
        if result["response_code"] == 0:
            # Save inscription to database
            inscription = OneclickInscription(
                id=str(uuid.uuid4()),
                username="test_user",  # For testing purposes, using a default username
                email=None,
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
            
            logger.info(
                "Inscription completed successfully",
                context={
                    "inscription_id": inscription.id,
                    "tbk_user": result["tbk_user"][:10] + "...",
                    "card_type": result["card_type"],
                    "card_number": result["card_number"]
                }
            )
            
            # Return success HTML page
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Inscripción Exitosa - Testing</title>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background-color: #f5f5f5;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 10px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        max-width: 500px;
                        margin: 0 auto;
                    }}
                    .success {{ color: #28a745; }}
                    .card-info {{ 
                        background: #f8f9fa; 
                        padding: 15px; 
                        border-radius: 5px; 
                        margin: 20px 0;
                    }}
                    .test-badge {{
                        background: #007bff;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        margin-bottom: 20px;
                        display: inline-block;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="test-badge">TEST ENDPOINT</div>
                    <h1 class="success">✅ Inscripción Exitosa</h1>
                    <p>Tu tarjeta ha sido registrada correctamente en nuestro sistema.</p>
                    <div class="card-info">
                        <p><strong>Tipo de tarjeta:</strong> {result["card_type"]}</p>
                        <p><strong>Número:</strong> {result["card_number"]}</p>
                        <p><strong>Código de autorización:</strong> {result["authorization_code"]}</p>
                        <p><strong>TBK User:</strong> {result["tbk_user"][:15]}...</p>
                    </div>
                    <p><em>Este es un endpoint de testing para callbacks de Transbank.</em></p>
                    <p>Ya puedes cerrar esta ventana.</p>
                </div>
            </body>
            </html>
            """
            
        else:
            logger.warning(
                "Inscription failed",
                context={
                    "token": TBK_TOKEN[:10] + "...",
                    "response_code": result["response_code"]
                }
            )
            
            # Return error HTML page
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error en Inscripción - Testing</title>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background-color: #f5f5f5;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 10px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        max-width: 500px;
                        margin: 0 auto;
                    }}
                    .error {{ color: #dc3545; }}
                    .test-badge {{
                        background: #007bff;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        margin-bottom: 20px;
                        display: inline-block;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="test-badge">TEST ENDPOINT</div>
                    <h1 class="error">❌ Error en Inscripción</h1>
                    <p>Hubo un problema al procesar el registro de tu tarjeta.</p>
                    <p><strong>Código de respuesta:</strong> {result["response_code"]}</p>
                    <p><strong>Token:</strong> {TBK_TOKEN[:15]}...</p>
                    <p><em>Este es un endpoint de testing para callbacks de Transbank.</em></p>
                    <p>Por favor, intenta nuevamente o contacta a soporte.</p>
                </div>
            </body>
            </html>
            """
        
        return html_content
        
    except Exception as e:
        logger.error(
            f"Error processing inscription result: {str(e)}",
            error={"type": type(e).__name__, "message": str(e)}
        )
        
        # Return error HTML page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error del Sistema - Testing</title>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .error {{ color: #dc3545; }}
                .test-badge {{
                    background: #007bff;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 12px;
                    margin-bottom: 20px;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="test-badge">TEST ENDPOINT</div>
                <h1 class="error">❌ Error del Sistema</h1>
                <p>Ocurrió un error inesperado al procesar tu solicitud.</p>
                <p><strong>Token:</strong> {TBK_TOKEN[:15]}...</p>
                <p><em>Este es un endpoint de testing para callbacks de Transbank.</em></p>
                <p>Por favor, contacta a soporte técnico.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content


@router.get("/inscription/status")
async def inscription_test_status():
    """
    Simple health check endpoint for testing callback infrastructure.
    """
    return {
        "status": "active",
        "service": "inscription_callback",
        "message": "Callback endpoint is ready to receive Transbank responses",
        "timestamp": datetime.utcnow().isoformat()
    } 