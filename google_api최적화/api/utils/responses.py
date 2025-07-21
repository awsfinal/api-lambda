from fastapi import HTTPException
from fastapi.responses import JSONResponse
from models import ErrorResponse
import logging

logger = logging.getLogger(__name__)

def create_error_response(status_code: int, error: str, message: str, request_id: str = None) -> JSONResponse:
    """
    표준화된 에러 응답을 생성합니다.
    """
    error_response = ErrorResponse(
        error=error,
        message=message,
        request_id=request_id
    )
    
    logger.error(f"Error response: {error} - {message} (Request ID: {request_id})")
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )

def create_success_response(data: dict, status_code: int = 200) -> JSONResponse:
    """
    성공 응답을 생성합니다.
    """
    return JSONResponse(
        status_code=status_code,
        content=data
    )

class APIException(HTTPException):
    """
    커스텀 API 예외 클래스
    """
    def __init__(self, status_code: int, error: str, message: str, request_id: str = None):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.request_id = request_id
        super().__init__(status_code=status_code, detail=message)
