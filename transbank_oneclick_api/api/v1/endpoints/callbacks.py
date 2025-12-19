from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from datetime import datetime
import structlog

from transbank_oneclick_api.schemas.oneclick_schemas import InscriptionFinishRequest
from transbank_oneclick_api.services.transbank_service import TransbankService
from transbank_oneclick_api.api.deps import get_transbank_service
from transbank_oneclick_api.core.exceptions import TransactionRejectedException

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/inscription/result", response_class=HTMLResponse)
async def inscription_result_callback(
    TBK_TOKEN: str = Query(..., description="Token returned by Transbank"),
    transbank_service: TransbankService = Depends(get_transbank_service)
):
    """
    Handle the inscription result callback from Transbank.

    Router responsibilities:
    - Validate input (TBK_TOKEN)
    - Call service to complete inscription
    - Return HTML response for user

    NO database operations - Service handles everything.
    """
    try:
        logger.info("Processing inscription result from Transbank", token_prefix=TBK_TOKEN[:10])

        inscriptionFinishRequest = InscriptionFinishRequest(token=TBK_TOKEN, username="test_username")
        result = await transbank_service.finish_inscription(inscriptionFinishRequest)

        logger.info(
            "Inscription completed successfully",
            username=result.username,
            tbk_user_prefix=result.tbk_user[:10] if result.tbk_user else "",
            card_type=result.card_type,
            card_number=result.card_number
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
                    <p><strong>Usuario:</strong> {result.username}</p>
                    <p><strong>Tipo de tarjeta:</strong> {result.card_type}</p>
                    <p><strong>Número:</strong> {result.card_number}</p>
                    <p><strong>Código de autorización:</strong> {result.authorization_code}</p>
                    <p><strong>TBK User:</strong> {result.tbk_user[:15] if result.tbk_user else "N/A"}...</p>
                </div>
                <p><em>Este es un endpoint de testing para callbacks de Transbank.</em></p>
                <p>Ya puedes cerrar esta ventana.</p>
            </div>
        </body>
        </html>
        """

        return html_content

    except TransactionRejectedException as e:
        logger.warning(
            "Inscription rejected by Transbank",
            token_prefix=TBK_TOKEN[:10],
            error_code=e.code,
            error_message=e.message
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
                <p><strong>Error:</strong> {e.message}</p>
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
            "Error processing inscription result",
            error_type=type(e).__name__,
            error=str(e),
            token_prefix=TBK_TOKEN[:10],
            exc_info=True
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