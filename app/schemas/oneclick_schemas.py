from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


# Inscription Schemas
class InscriptionStartRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=256, description="Unique user identifier")
    email: EmailStr = Field(..., description="User email for notifications")
    response_url: str = Field(..., description="URL to return after inscription process")


class InscriptionStartResponse(BaseModel):
    token: str = Field(..., description="Session token for inscription process")
    url_webpay: str = Field(..., description="URL to redirect to Transbank")


class InscriptionFinishRequest(BaseModel):
    token: str = Field(..., description="TBK_TOKEN received from Transbank")


class InscriptionFinishResponse(BaseModel):
    tbk_user: str = Field(..., description="Permanent user token")
    response_code: int = Field(..., description="Response code (0 = success)")
    authorization_code: str = Field(..., description="Authorization code")
    card_type: str = Field(..., description="Card type (VISA, MASTERCARD, etc.)")
    card_number: str = Field(..., description="Masked card number (last 4 digits)")


class InscriptionDeleteRequest(BaseModel):
    tbk_user: str = Field(..., description="User token to delete")
    username: str = Field(..., description="Username associated with inscription")


class InscriptionDeleteResponse(BaseModel):
    tbk_user: str
    username: str
    status: str = "deleted"
    deletion_date: datetime


class InscriptionListResponse(BaseModel):
    username: str
    inscriptions: List['InscriptionInfo']
    total_inscriptions: int


class InscriptionInfo(BaseModel):
    tbk_user: str
    card_type: str
    card_number: str
    inscription_date: datetime
    status: str = "active"
    is_default: bool


# Transaction Schemas
class TransactionDetail(BaseModel):
    commerce_code: str = Field(..., description="Child commerce code")
    buy_order: str = Field(..., description="Child buy order")
    amount: int = Field(..., gt=0, description="Amount in Chilean pesos")
    installments_number: int = Field(default=1, ge=1, le=48, description="Number of installments")


class TransactionAuthorizeRequest(BaseModel):
    username: str = Field(..., description="User owner of the card")
    tbk_user: str = Field(..., description="User token obtained in finish")
    parent_buy_order: str = Field(..., description="Unique parent buy order")
    details: List[TransactionDetail] = Field(..., min_items=1, description="Transaction details")


class TransactionDetailResponse(BaseModel):
    amount: int
    status: str
    authorization_code: Optional[str]
    payment_type_code: Optional[str]
    response_code: int
    installments_number: int
    commerce_code: str
    buy_order: str
    balance: Optional[int] = None


class TransactionAuthorizeResponse(BaseModel):
    parent_buy_order: str
    session_id: str
    card_detail: dict
    accounting_date: str
    transaction_date: str
    details: List[TransactionDetailResponse]


class TransactionStatusResponse(BaseModel):
    buy_order: str
    session_id: str
    card_detail: dict
    accounting_date: str
    transaction_date: str
    details: List[TransactionDetailResponse]


class TransactionCaptureRequest(BaseModel):
    child_commerce_code: str = Field(..., description="Child commerce code")
    child_buy_order: str = Field(..., description="Child buy order")
    authorization_code: str = Field(..., description="Authorization code to capture")
    capture_amount: int = Field(..., gt=0, description="Amount to capture")


class TransactionCaptureResponse(BaseModel):
    authorization_code: str
    authorization_date: str
    captured_amount: int
    response_code: int


class TransactionRefundRequest(BaseModel):
    child_commerce_code: str = Field(..., description="Child commerce code")
    child_buy_order: str = Field(..., description="Child buy order to refund")
    amount: int = Field(..., gt=0, description="Amount to refund")


class TransactionRefundResponse(BaseModel):
    type: str
    response_code: int
    reversed_amount: int


class TransactionHistoryResponse(BaseModel):
    username: str
    transactions: List['TransactionHistoryItem']
    pagination: dict


class TransactionHistoryItem(BaseModel):
    parent_buy_order: str
    transaction_date: str
    total_amount: int
    card_number: str
    status: str
    details: List[TransactionDetailResponse]


# Update forward references
InscriptionListResponse.update_forward_refs()
TransactionHistoryResponse.update_forward_refs()