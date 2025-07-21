from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uuid
import time
import logging
from datetime import datetime
from typing import Optional

# Local imports
from config import settings
from models import (
    GPSCoordinates, PhotoCaptureRequest, AnalysisStatus, 
    ErrorResponse, PlaceInfo, EXIFData, CameraInfo, PhotoAnalysisResponse
)
from services.s3_service import s3_service
from services.sqs_service import sqs_service
# Google Maps API 서비스 사용 (Mock 서비스 사용)
# from services.google_maps_service import google_maps_service  # 실제 API 키가 있을 때 사용
from services.google_maps_service_mock import google_maps_service_mock as google_maps_service  # 테스트용
from utils.validators import validate_image_file, validate_image_content, validate_gps_coordinates
from utils.responses import create_error_response, create_success_response, APIException
from utils.exif_processor import exif_processor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 메모리 기반 임시 저장소 (프로덕션에서는 Redis나 DynamoDB 사용 권장)
analysis_status_store = {}

@app.get("/demo")
async def demo_page():
    """
    프론트엔드 데모 페이지
    """
    return FileResponse("static/index.html")

@app.get("/")
async def root():
    """
    API 상태 확인
    """
    return {
        "message": "Historical Place Recognition API",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    """
    try:
        # SQS 큐 상태 확인
        queue_attrs = await sqs_service.get_queue_attributes()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "sqs": "connected",
                "s3": "connected",
                "google_maps": "connected" if settings.GOOGLE_MAPS_API_KEY else "not_configured"
            },
            "queue_info": queue_attrs
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post(f"{settings.API_V1_PREFIX}/capture-photo")
async def capture_photo(
    file: UploadFile = File(..., description="카메라로 촬영한 사진"),
    device_latitude: Optional[float] = Form(None, description="디바이스 GPS 위도"),
    device_longitude: Optional[float] = Form(None, description="디바이스 GPS 경도"),
):
    """
    카메라로 촬영한 사진을 분석합니다.
    EXIF GPS 정보를 우선 사용하고, 없으면 디바이스 GPS를 사용합니다.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 입력 검증
        validate_image_file(file)
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        validate_image_content(image_data)
        
        # EXIF 메타데이터 추출
        metadata = exif_processor.process_image_metadata(image_data)
        
        # GPS 좌표 결정 (우선순위: EXIF GPS > 디바이스 GPS)
        final_gps = None
        gps_source = "none"
        
        if metadata['has_gps'] and metadata['gps_coordinates']:
            # EXIF에서 GPS 정보 추출 성공
            final_gps = metadata['gps_coordinates']
            gps_source = "exif"
            logger.info(f"EXIF GPS 사용: {final_gps}")
        elif device_latitude is not None and device_longitude is not None:
            # 디바이스 GPS 사용
            validate_gps_coordinates(device_latitude, device_longitude)
            final_gps = {
                "latitude": device_latitude,
                "longitude": device_longitude
            }
            gps_source = "device"
            logger.info(f"디바이스 GPS 사용: {final_gps}")
        else:
            return create_error_response(
                status_code=400,
                error="NO_GPS_DATA",
                message="GPS 정보가 없습니다. 사진에 GPS 정보가 포함되어 있거나 디바이스 GPS 좌표를 제공해주세요.",
                request_id=request_id
            )
        
        # GPS 좌표 객체 생성
        gps_coords = GPSCoordinates(
            latitude=final_gps["latitude"],
            longitude=final_gps["longitude"],
            source=gps_source
        )
        
        # 1. Google Maps API로 장소 정보 조회
        place_info = await google_maps_service.get_place_by_coordinates(
            gps_coords.latitude, 
            gps_coords.longitude
        )
        
        if not place_info:
            place_info = PlaceInfo(
                place_name="알 수 없는 장소",
                address="주소 정보 없음",
                category="일반"
            )
        
        # 2. 로컬 저장소에 이미지 업로드 (S3 대신 임시 사용)
        from services.local_storage_service import local_storage_service
        
        upload_metadata = {
            'latitude': str(gps_coords.latitude),
            'longitude': str(gps_coords.longitude),
            'gps_source': gps_source,
            'has_exif': str(metadata['has_exif']),
            'camera_make': metadata['camera_info'].get('make', ''),
            'camera_model': metadata['camera_info'].get('model', ''),
            'capture_time': metadata['camera_info'].get('datetime', ''),
        }
        
        s3_url = await local_storage_service.upload_image(
            image_data, 
            file.content_type, 
            upload_metadata
        )
        
        # 3. 분석 요청 처리 (SQS 대신 즉시 완료로 처리)
        # analysis_request = {
        #     'request_id': request_id,
        #     's3_url': s3_url,
        #     'gps_coordinates': gps_coords.dict(),
        #     'place_info': place_info.dict(),
        #     'exif_metadata': metadata,
        #     'service_type': 'building_recognition'
        # }
        
        # await sqs_service.send_analysis_request(
        #     s3_url, 
        #     analysis_request, 
        #     request_id
        # )
        
        # 로컬 테스트용: 즉시 완료 처리
        logger.info(f"로컬 테스트: 분석 요청 생략, 즉시 완료 처리 - {request_id}")
        
        # 4. 분석 상태 저장 (로컬 테스트용: 즉시 완료)
        analysis_status_store[request_id] = AnalysisStatus(
            request_id=request_id,
            status="COMPLETED",
            message="사진 분석이 완료되었습니다. (로컬 테스트)",
            progress=100
        )
        
        processing_time = time.time() - start_time
        
        # EXIF 데이터 구성
        exif_data = EXIFData(
            has_exif=metadata['has_exif'],
            has_gps=metadata['has_gps'],
            camera_info=CameraInfo(**metadata['camera_info']),
            raw_exif=metadata.get('exif_data') if metadata['has_exif'] else None
        )
        
        return create_success_response({
            "request_id": request_id,
            "status": "PENDING",
            "message": "카메라 사진 분석이 시작되었습니다.",
            "gps_info": {
                "coordinates": gps_coords.dict(),
                "source": gps_source,
                "message": f"GPS 정보를 {gps_source}에서 가져왔습니다."
            },
            "place_info": place_info.dict(),
            "camera_info": metadata['camera_info'],
            "exif_info": {
                "has_exif": metadata['has_exif'],
                "has_gps": metadata['has_gps']
            },
            "s3_url": s3_url,
            "processing_time": processing_time,
            "estimated_completion": "2-5분 (건물 인식 및 역사 정보 생성)"
        }, 202)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"사진 분석 요청 실패 {request_id}: {e}")
        return create_error_response(
            status_code=500,
            error="CAPTURE_ANALYSIS_FAILED",
            message=f"사진 분석 요청 처리 중 오류가 발생했습니다: {str(e)}",
            request_id=request_id
        )

@app.get(f"{settings.API_V1_PREFIX}/analysis-status/{{request_id}}")
async def get_analysis_status(request_id: str):
    """
    분석 상태를 조회합니다.
    """
    try:
        if request_id not in analysis_status_store:
            return create_error_response(
                status_code=404,
                error="REQUEST_NOT_FOUND",
                message="Analysis request not found",
                request_id=request_id
            )
        
        status = analysis_status_store[request_id]
        return create_success_response(status.dict())
        
    except Exception as e:
        logger.error(f"Failed to get analysis status for {request_id}: {e}")
        return create_error_response(
            status_code=500,
            error="STATUS_CHECK_FAILED",
            message="Failed to check analysis status",
            request_id=request_id
        )

@app.post(f"{settings.API_V1_PREFIX}/analysis-result")
async def receive_analysis_result(result_data: dict):
    """
    Lambda에서 분석 결과를 받는 엔드포인트 (내부 사용)
    """
    try:
        request_id = result_data.get("request_id")
        if not request_id:
            raise HTTPException(status_code=400, detail="Missing request_id")
        
        # 분석 상태 업데이트
        if request_id in analysis_status_store:
            analysis_status_store[request_id].status = "COMPLETED"
            analysis_status_store[request_id].result = result_data
            analysis_status_store[request_id].message = "Analysis completed successfully"
        
        return {"status": "success", "message": "Result received"}
        
    except Exception as e:
        logger.error(f"Failed to receive analysis result: {e}")
        raise HTTPException(status_code=500, detail="Failed to process result")

@app.post(f"{settings.API_V1_PREFIX}/test-photo-upload")
async def test_photo_upload(
    file: UploadFile = File(..., description="테스트용 사진 업로드"),
    device_latitude: Optional[float] = Form(None, description="디바이스 GPS 위도"),
    device_longitude: Optional[float] = Form(None, description="디바이스 GPS 경도"),
):
    """
    사진 업로드 및 GPS/EXIF 처리 테스트 (로컬 저장)
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 입력 검증
        validate_image_file(file)
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        validate_image_content(image_data)
        
        # EXIF 메타데이터 추출
        metadata = exif_processor.process_image_metadata(image_data)
        
        # GPS 좌표 결정 (우선순위: EXIF GPS > 디바이스 GPS)
        final_gps = None
        gps_source = "none"
        
        if metadata['has_gps'] and metadata['gps_coordinates']:
            # EXIF에서 GPS 정보 추출 성공
            final_gps = metadata['gps_coordinates']
            gps_source = "exif"
            logger.info(f"EXIF GPS 사용: {final_gps}")
        elif device_latitude is not None and device_longitude is not None:
            # 디바이스 GPS 사용
            validate_gps_coordinates(device_latitude, device_longitude)
            final_gps = {
                "latitude": device_latitude,
                "longitude": device_longitude
            }
            gps_source = "device"
            logger.info(f"디바이스 GPS 사용: {final_gps}")
        else:
            return create_error_response(
                status_code=400,
                error="NO_GPS_DATA",
                message="GPS 정보가 없습니다. 사진에 GPS 정보가 포함되어 있거나 디바이스 GPS 좌표를 제공해주세요.",
                request_id=request_id
            )
        
        # GPS 좌표 객체 생성
        gps_coords = GPSCoordinates(
            latitude=final_gps["latitude"],
            longitude=final_gps["longitude"],
            source=gps_source
        )
        
        # Google Maps API로 장소 정보 조회
        place_info = await google_maps_service.get_place_by_coordinates(
            gps_coords.latitude, 
            gps_coords.longitude
        )
        
        if not place_info:
            place_info = PlaceInfo(
                place_name="알 수 없는 장소",
                address="주소 정보 없음",
                category="일반"
            )
        
        # 로컬 저장소에 이미지 업로드
        from services.local_storage_service import local_storage_service
        
        upload_metadata = {
            'latitude': str(gps_coords.latitude),
            'longitude': str(gps_coords.longitude),
            'gps_source': gps_source,
            'has_exif': str(metadata['has_exif']),
            'camera_make': metadata['camera_info'].get('make', ''),
            'camera_model': metadata['camera_info'].get('model', ''),
            'capture_time': metadata['camera_info'].get('datetime', ''),
            'place_name': place_info.place_name,
            'address': place_info.address
        }
        
        local_url = await local_storage_service.upload_image(
            image_data, 
            file.content_type, 
            upload_metadata
        )
        
        processing_time = time.time() - start_time
        
        # EXIF 데이터 구성
        exif_data = EXIFData(
            has_exif=metadata['has_exif'],
            has_gps=metadata['has_gps'],
            camera_info=CameraInfo(**metadata['camera_info']),
            raw_exif=metadata.get('exif_data') if metadata['has_exif'] else None
        )
        
        return create_success_response({
            "request_id": request_id,
            "status": "COMPLETED",
            "message": "사진 업로드 및 분석이 완료되었습니다.",
            "gps_info": {
                "coordinates": gps_coords.dict(),
                "source": gps_source,
                "message": f"GPS 정보를 {gps_source}에서 가져왔습니다."
            },
            "place_info": place_info.dict(),
            "camera_info": metadata['camera_info'],
            "exif_info": {
                "has_exif": metadata['has_exif'],
                "has_gps": metadata['has_gps']
            },
            "file_info": {
                "original_name": file.filename,
                "content_type": file.content_type,
                "file_size": len(image_data),
                "local_url": local_url
            },
            "processing_time": processing_time
        }, 200)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"테스트 사진 업로드 실패 {request_id}: {e}")
        return create_error_response(
            status_code=500,
            error="TEST_UPLOAD_FAILED",
            message=f"테스트 사진 업로드 중 오류가 발생했습니다: {str(e)}",
            request_id=request_id
        )

@app.post(f"{settings.API_V1_PREFIX}/compare-vision-approaches")
async def compare_vision_approaches(
    file: UploadFile = File(..., description="비교 분석할 이미지"),
    device_latitude: Optional[float] = Form(None, description="디바이스 GPS 위도"),
    device_longitude: Optional[float] = Form(None, description="디바이스 GPS 경도"),
):
    """
    GenAI vs 기존 Vision API 비교 분석
    """
    request_id = str(uuid.uuid4())
    
    try:
        # 입력 검증
        validate_image_file(file)
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        validate_image_content(image_data)
        
        # GPS 정보 준비
        gps_info = None
        if device_latitude and device_longitude:
            gps_info = {
                "latitude": device_latitude,
                "longitude": device_longitude
            }
        
        # 1. 기존 Vision API 방식 (구조화된 분석)
        from services.integrated_analysis_service import integrated_analysis_service
        traditional_result = await integrated_analysis_service.analyze_image_comprehensive(
            image_data, gps_info
        )
        
        # 2. GenAI 방식 (맥락적 분석)
        from services.genai_vision_service import genai_vision_service
        comparison_result = await genai_vision_service.compare_with_traditional_vision(
            image_data, traditional_result, gps_info
        )
        
        return create_success_response({
            "request_id": request_id,
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(image_data)
            },
            "gps_info": gps_info,
            "comparison_analysis": comparison_result,
            "summary": {
                "traditional_strength": "정확한 객체 인식, 구조화된 데이터",
                "genai_strength": "맥락 이해, 문화적 특성 파악, 자연어 설명",
                "best_approach": "두 방식을 조합하여 사용하는 것이 최적"
            }
        })
        
    except Exception as e:
        logger.error(f"Vision 비교 분석 실패: {e}")
        return create_error_response(
            status_code=500,
            error="VISION_COMPARISON_FAILED",
            message=f"Vision 비교 분석 중 오류: {str(e)}",
            request_id=request_id
        )

@app.post(f"{settings.API_V1_PREFIX}/analyze-image-comprehensive")
async def analyze_image_comprehensive(
    file: UploadFile = File(..., description="종합 분석할 이미지"),
    device_latitude: Optional[float] = Form(None, description="디바이스 GPS 위도"),
    device_longitude: Optional[float] = Form(None, description="디바이스 GPS 경도"),
):
    """
    종합적인 이미지 분석 (Rekognition + Textract + 카카오맵)
    """
    request_id = str(uuid.uuid4())
    
    try:
        # 입력 검증
        validate_image_file(file)
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        validate_image_content(image_data)
        
        # EXIF 메타데이터 추출
        metadata = exif_processor.process_image_metadata(image_data)
        
        # GPS 좌표 결정
        gps_coords = None
        gps_source = "none"
        
        if metadata['has_gps'] and metadata['gps_coordinates']:
            gps_coords = metadata['gps_coordinates']
            gps_source = "exif"
        elif device_latitude is not None and device_longitude is not None:
            validate_gps_coordinates(device_latitude, device_longitude)
            gps_coords = {
                "latitude": device_latitude,
                "longitude": device_longitude
            }
            gps_source = "device"
        
        # 통합 이미지 분석 실행
        from services.integrated_analysis_service import integrated_analysis_service
        
        analysis_result = await integrated_analysis_service.analyze_image_comprehensive(
            image_data, gps_coords
        )
        
        return create_success_response({
            "request_id": request_id,
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(image_data)
            },
            "gps_info": {
                "coordinates": gps_coords,
                "source": gps_source
            },
            "exif_info": {
                "has_exif": metadata['has_exif'],
                "has_gps": metadata['has_gps'],
                "camera_info": metadata['camera_info']
            },
            "analysis_result": analysis_result
        })
        
    except Exception as e:
        logger.error(f"종합 이미지 분석 실패: {e}")
        return create_error_response(
            status_code=500,
            error="COMPREHENSIVE_ANALYSIS_FAILED",
            message=f"종합 이미지 분석 중 오류: {str(e)}",
            request_id=request_id
        )

@app.post(f"{settings.API_V1_PREFIX}/test-photo-simple")
async def test_photo_simple(
    file: UploadFile = File(..., description="테스트용 사진"),
    device_latitude: Optional[float] = Form(None, description="디바이스 GPS 위도"),
    device_longitude: Optional[float] = Form(None, description="디바이스 GPS 경도"),
):
    """
    사진 업로드 및 GPS/EXIF 처리 테스트 (AWS 없이)
    """
    request_id = str(uuid.uuid4())
    
    try:
        # 입력 검증
        validate_image_file(file)
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        validate_image_content(image_data)
        
        # EXIF 메타데이터 추출
        metadata = exif_processor.process_image_metadata(image_data)
        
        # GPS 좌표 결정
        final_gps = None
        gps_source = "none"
        
        if metadata['has_gps'] and metadata['gps_coordinates']:
            final_gps = metadata['gps_coordinates']
            gps_source = "exif"
        elif device_latitude is not None and device_longitude is not None:
            validate_gps_coordinates(device_latitude, device_longitude)
            final_gps = {
                "latitude": device_latitude,
                "longitude": device_longitude
            }
            gps_source = "device"
        else:
            return create_error_response(
                status_code=400,
                error="NO_GPS_DATA",
                message="GPS 정보가 필요합니다.",
                request_id=request_id
            )
        
        # Google Maps API로 장소 정보 조회
        place_info = await google_maps_service.get_place_by_coordinates(
            final_gps["latitude"], 
            final_gps["longitude"]
        )
        
        if not place_info:
            place_info = PlaceInfo(
                place_name="알 수 없는 장소",
                address="주소 정보 없음",
                category="일반"
            )
        
        return create_success_response({
            "request_id": request_id,
            "status": "COMPLETED",
            "message": "사진 분석 완료",
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(image_data)
            },
            "gps_info": {
                "coordinates": final_gps,
                "source": gps_source
            },
            "place_info": place_info.dict(),
            "exif_info": {
                "has_exif": metadata['has_exif'],
                "has_gps": metadata['has_gps'],
                "camera_info": metadata['camera_info']
            }
        })
        
    except Exception as e:
        logger.error(f"사진 테스트 실패: {e}")
        return create_error_response(
            status_code=500,
            error="PHOTO_TEST_FAILED",
            message=f"사진 테스트 중 오류: {str(e)}",
            request_id=request_id
        )

@app.post(f"{settings.API_V1_PREFIX}/test-gps-location")
async def test_gps_location(
    latitude: float = Form(..., description="GPS 위도"),
    longitude: float = Form(..., description="GPS 경도")
):
    """
    GPS 좌표로 장소 정보만 테스트 (AWS 없이)
    """
    try:
        # GPS 좌표 검증
        validate_gps_coordinates(latitude, longitude)
        
        # Google Maps API로 장소 정보 조회
        place_info = await google_maps_service.get_place_by_coordinates(latitude, longitude)
        
        if not place_info:
            place_info = PlaceInfo(
                place_name="알 수 없는 장소",
                address="주소 정보 없음",
                category="일반"
            )
        
        return create_success_response({
            "gps_coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "place_info": place_info.dict(),
            "message": "GPS 기반 장소 정보 조회 성공"
        })
        
    except Exception as e:
        logger.error(f"GPS 장소 조회 실패: {e}")
        return create_error_response(
            status_code=500,
            error="GPS_LOCATION_FAILED",
            message=f"GPS 장소 조회 중 오류가 발생했습니다: {str(e)}"
        )

@app.get(f"{settings.API_V1_PREFIX}/search-place")
async def search_place(
    keyword: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    region: Optional[str] = None
):
    """
    키워드로 장소를 검색합니다.
    region 파라미터로 지역을 지정할 수 있습니다 (seoul, busan, daegu 등)
    """
    try:
        # 지역별 기본 좌표 설정
        region_coords = {
            'seoul': (37.5665, 126.9780),      # 서울시청
            'busan': (35.1796, 129.0756),      # 부산시청  
            'daegu': (35.8714, 128.6014),      # 대구시청
            'incheon': (37.4563, 126.7052),    # 인천시청
            'gwangju': (35.1595, 126.8526),    # 광주시청
            'daejeon': (36.3504, 127.3845),    # 대전시청
            'ulsan': (35.5384, 129.3114),      # 울산시청
            'sejong': (36.4800, 127.2890),     # 세종시청
        }
        
        # region이 지정되면 해당 지역 좌표 사용
        if region and region.lower() in region_coords:
            latitude, longitude = region_coords[region.lower()]
            logger.info(f"지역 '{region}' 좌표 사용: {latitude}, {longitude}")
        
        if latitude and longitude:
            validate_gps_coordinates(latitude, longitude)
        
        place_info = await google_maps_service.search_place_by_keyword(keyword, latitude, longitude)
        
        if not place_info:
            return create_error_response(
                status_code=404,
                error="PLACE_NOT_FOUND",
                message=f"No place found for keyword: {keyword}"
            )
        
        return create_success_response(place_info.dict())
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Place search failed: {e}")
        return create_error_response(
            status_code=500,
            error="SEARCH_FAILED",
            message="Failed to search place"
        )

# 예외 처리 핸들러
@app.exception_handler(APIException)
async def api_exception_handler(request, exc: APIException):
    return create_error_response(
        status_code=exc.status_code,
        error=exc.error,
        message=exc.message,
        request_id=exc.request_id
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return create_error_response(
        status_code=exc.status_code,
        error="HTTP_ERROR",
        message=exc.detail
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )