from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class GPSCoordinates(BaseModel):
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    source: str = Field(..., description="GPS 소스: 'exif', 'device', 'manual'")

class CameraInfo(BaseModel):
    make: Optional[str] = Field(None, description="카메라 제조사")
    model: Optional[str] = Field(None, description="카메라 모델")
    datetime: Optional[str] = Field(None, description="촬영 시간")
    width: Optional[int] = Field(None, description="이미지 너비")
    height: Optional[int] = Field(None, description="이미지 높이")
    iso: Optional[int] = Field(None, description="ISO 감도")
    focal_length: Optional[float] = Field(None, description="초점 거리")
    aperture: Optional[float] = Field(None, description="조리개 값")
    exposure_time: Optional[str] = Field(None, description="노출 시간")
    orientation: Optional[int] = Field(None, description="이미지 방향")

class EXIFData(BaseModel):
    has_exif: bool = Field(..., description="EXIF 데이터 존재 여부")
    has_gps: bool = Field(..., description="GPS 정보 존재 여부")
    camera_info: CameraInfo = Field(..., description="카메라 정보")
    raw_exif: Optional[Dict[str, Any]] = Field(None, description="원본 EXIF 데이터")

class PhotoCaptureRequest(BaseModel):
    """카메라로 촬영된 사진 분석 요청"""
    device_gps: Optional[GPSCoordinates] = Field(None, description="디바이스 GPS 좌표")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="요청 시간")

class PlaceInfo(BaseModel):
    place_name: str = Field(..., description="장소명")
    address: str = Field(..., description="주소")
    category: Optional[str] = Field(None, description="장소 카테고리")
    distance: Optional[float] = Field(None, description="GPS 좌표로부터의 거리(미터)")

class BuildingRecognitionResult(BaseModel):
    """건물 인식 결과"""
    building_name: str = Field(..., description="인식된 건물명")
    confidence: float = Field(..., description="인식 신뢰도 (0-1)")
    building_type: str = Field(..., description="건물 유형 (궁궐, 사찰, 교회, 현대건물 등)")
    architectural_style: Optional[str] = Field(None, description="건축 양식")

class ImageAnalysisResult(BaseModel):
    labels: List[str] = Field(..., description="Rekognition에서 추출된 라벨들")
    confidence_scores: List[float] = Field(..., description="각 라벨의 신뢰도")
    building_recognition: Optional[BuildingRecognitionResult] = Field(None, description="건물 인식 결과")

class HistoricalInfo(BaseModel):
    title: str = Field(..., description="장소/건물 제목")
    description: str = Field(..., description="역사적/철학적 설명")
    period: Optional[str] = Field(None, description="시대/시기")
    significance: Optional[str] = Field(None, description="역사적 의의")
    architectural_features: Optional[List[str]] = Field(None, description="건축적 특징")
    cultural_value: Optional[str] = Field(None, description="문화적 가치")

class PhotoAnalysisResponse(BaseModel):
    request_id: str = Field(..., description="요청 ID")
    
    # GPS 및 위치 정보
    final_gps: GPSCoordinates = Field(..., description="최종 사용된 GPS 좌표")
    place_info: PlaceInfo = Field(..., description="장소 정보")
    
    # 이미지 및 카메라 정보
    exif_data: EXIFData = Field(..., description="EXIF 메타데이터")
    image_analysis: ImageAnalysisResult = Field(..., description="이미지 분석 결과")
    
    # 역사적 정보
    historical_info: HistoricalInfo = Field(..., description="역사적/문화적 정보")
    
    # 처리 정보
    processing_time: float = Field(..., description="처리 시간(초)")
    created_at: datetime = Field(default_factory=datetime.now)

class AnalysisStatus(BaseModel):
    request_id: str
    status: str = Field(..., description="PENDING, PROCESSING, COMPLETED, FAILED")
    message: Optional[str] = None
    progress: Optional[int] = Field(None, description="진행률 (0-100)")
    result: Optional[PhotoAnalysisResponse] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None
