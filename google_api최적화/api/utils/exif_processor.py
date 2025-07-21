from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class EXIFProcessor:
    """
    이미지 EXIF 정보를 추출하고 처리하는 클래스
    """
    
    @staticmethod
    def extract_exif_data(image_data: bytes) -> Dict:
        """
        이미지에서 EXIF 데이터를 추출합니다.
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            exif_data = {}
            
            # 기본 EXIF 정보 추출
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
            
            return exif_data
            
        except Exception as e:
            logger.error(f"EXIF 데이터 추출 실패: {e}")
            return {}
    
    @staticmethod
    def extract_gps_from_exif(exif_data: Dict) -> Optional[Tuple[float, float]]:
        """
        EXIF 데이터에서 GPS 좌표를 추출합니다.
        """
        try:
            gps_info = exif_data.get('GPSInfo')
            if not gps_info:
                return None
            
            def convert_to_degrees(value):
                """DMS(도분초)를 십진도로 변환"""
                d, m, s = value
                return float(d) + float(m)/60 + float(s)/3600
            
            # 위도 추출
            lat = gps_info.get(2)  # GPSLatitude
            lat_ref = gps_info.get(1)  # GPSLatitudeRef
            
            # 경도 추출
            lon = gps_info.get(4)  # GPSLongitude
            lon_ref = gps_info.get(3)  # GPSLongitudeRef
            
            if lat and lon and lat_ref and lon_ref:
                latitude = convert_to_degrees(lat)
                longitude = convert_to_degrees(lon)
                
                # 남반구/서반구 처리
                if lat_ref != 'N':
                    latitude = -latitude
                if lon_ref != 'E':
                    longitude = -longitude
                
                return (latitude, longitude)
            
            return None
            
        except Exception as e:
            logger.error(f"GPS 좌표 추출 실패: {e}")
            return None
    
    @staticmethod
    def extract_camera_info(exif_data: Dict) -> Dict:
        """
        카메라 정보를 추출합니다.
        """
        camera_info = {}
        
        try:
            # 카메라 제조사 및 모델
            camera_info['make'] = exif_data.get('Make', '알 수 없음')
            camera_info['model'] = exif_data.get('Model', '알 수 없음')
            
            # 촬영 시간
            datetime_str = exif_data.get('DateTime')
            if datetime_str:
                try:
                    camera_info['datetime'] = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S').isoformat()
                except:
                    camera_info['datetime'] = datetime_str
            
            # 이미지 크기
            camera_info['width'] = exif_data.get('ExifImageWidth', 0)
            camera_info['height'] = exif_data.get('ExifImageHeight', 0)
            
            # 카메라 설정
            camera_info['iso'] = exif_data.get('ISOSpeedRatings')
            camera_info['focal_length'] = exif_data.get('FocalLength')
            camera_info['aperture'] = exif_data.get('FNumber')
            camera_info['exposure_time'] = exif_data.get('ExposureTime')
            
            # 방향 정보 (나침반)
            camera_info['orientation'] = exif_data.get('Orientation')
            
        except Exception as e:
            logger.error(f"카메라 정보 추출 실패: {e}")
        
        return camera_info
    
    @staticmethod
    def process_image_metadata(image_data: bytes) -> Dict:
        """
        이미지에서 모든 메타데이터를 추출하고 처리합니다.
        """
        result = {
            'has_exif': False,
            'has_gps': False,
            'gps_coordinates': None,
            'camera_info': {},
            'exif_data': {}
        }
        
        try:
            # EXIF 데이터 추출
            exif_data = EXIFProcessor.extract_exif_data(image_data)
            
            if exif_data:
                result['has_exif'] = True
                result['exif_data'] = exif_data
                
                # GPS 좌표 추출
                gps_coords = EXIFProcessor.extract_gps_from_exif(exif_data)
                if gps_coords:
                    result['has_gps'] = True
                    result['gps_coordinates'] = {
                        'latitude': gps_coords[0],
                        'longitude': gps_coords[1]
                    }
                
                # 카메라 정보 추출
                result['camera_info'] = EXIFProcessor.extract_camera_info(exif_data)
            
            return result
            
        except Exception as e:
            logger.error(f"이미지 메타데이터 처리 실패: {e}")
            return result

exif_processor = EXIFProcessor()
