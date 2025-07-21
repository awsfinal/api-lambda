from fastapi import HTTPException, UploadFile
from PIL import Image
import io
from config import settings

def validate_image_file(file: UploadFile) -> None:
    """
    업로드된 이미지 파일의 유효성을 검사합니다.
    """
    # 파일 크기 검사
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Content-Type 검사
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )

def validate_image_content(image_data: bytes) -> None:
    """
    이미지 데이터의 내용을 검증합니다.
    """
    try:
        # PIL로 이미지 열기 시도
        image = Image.open(io.BytesIO(image_data))
        image.verify()  # 이미지 무결성 검사
        
        # 이미지 크기 제한 (선택사항)
        if image.size[0] > 4096 or image.size[1] > 4096:
            raise HTTPException(
                status_code=413,
                detail="Image dimensions too large. Maximum size is 4096x4096 pixels"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file: {str(e)}"
        )

def validate_gps_coordinates(latitude: float, longitude: float) -> None:
    """
    GPS 좌표의 유효성을 검사합니다.
    """
    if not (-90 <= latitude <= 90):
        raise HTTPException(
            status_code=400,
            detail="Invalid latitude. Must be between -90 and 90"
        )
    
    if not (-180 <= longitude <= 180):
        raise HTTPException(
            status_code=400,
            detail="Invalid longitude. Must be between -180 and 180"
        )
    
    # 한국 영역 대략적 검사 (선택사항)
    if not (33 <= latitude <= 39 and 124 <= longitude <= 132):
        # 경고만 로그에 남기고 처리는 계속
        import logging
        logging.warning(f"GPS coordinates outside Korea region: {latitude}, {longitude}")

def validate_request_id(request_id: str) -> None:
    """
    요청 ID의 형식을 검증합니다.
    """
    if not request_id or len(request_id) < 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid request ID format"
        )
