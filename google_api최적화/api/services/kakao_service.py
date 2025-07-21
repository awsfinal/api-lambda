import requests
import logging
from typing import Optional
from config import settings
from models import PlaceInfo

logger = logging.getLogger(__name__)

class KakaoMapService:
    def __init__(self):
        self.api_key = settings.KAKAO_REST_API_KEY
        self.base_url = "https://dapi.kakao.com/v2/local"
        self.headers = {
            "Authorization": f"KakaoAK {self.api_key}"
        }

    async def get_place_by_coordinates(self, latitude: float, longitude: float) -> Optional[PlaceInfo]:
        """
        GPS 좌표를 기반으로 장소 정보를 조회합니다.
        """
        try:
            # 좌표 -> 주소 변환
            coord_to_address_url = f"{self.base_url}/geo/coord2address.json"
            params = {
                "x": longitude,
                "y": latitude,
                "input_coord": "WGS84"
            }
            
            response = requests.get(coord_to_address_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            address_data = response.json()
            
            if not address_data.get('documents'):
                logger.warning(f"No address found for coordinates: {latitude}, {longitude}")
                return None
            
            # 주소 정보 추출
            address_info = address_data['documents'][0]
            address = address_info.get('address', {})
            road_address = address_info.get('road_address', {})
            
            # 도로명 주소 우선, 없으면 지번 주소 사용
            full_address = road_address.get('address_name') if road_address else address.get('address_name', '')
            
            # 주변 장소 검색
            place_info = await self._search_nearby_places(latitude, longitude)
            
            if place_info:
                place_info.address = full_address
                return place_info
            
            # 주변 장소가 없으면 기본 정보 반환
            return PlaceInfo(
                place_name=address.get('region_3depth_name', '알 수 없는 장소'),
                address=full_address,
                category="일반"
            )
            
        except requests.RequestException as e:
            logger.error(f"Kakao API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting place info: {e}")
            return None

    async def _search_nearby_places(self, latitude: float, longitude: float, radius: int = 500) -> Optional[PlaceInfo]:
        """
        주변 관심 장소를 검색합니다.
        """
        try:
            search_url = f"{self.base_url}/search/category.json"
            
            # 관광명소, 문화시설 등을 우선 검색
            categories = ["AT4", "CT1", "PK6"]  # 관광명소, 문화시설, 주차장
            
            for category in categories:
                params = {
                    "category_group_code": category,
                    "x": longitude,
                    "y": latitude,
                    "radius": radius,
                    "sort": "distance"
                }
                
                response = requests.get(search_url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                documents = data.get('documents', [])
                
                if documents:
                    place = documents[0]  # 가장 가까운 장소
                    return PlaceInfo(
                        place_name=place.get('place_name', ''),
                        address=place.get('address_name', ''),
                        category=place.get('category_name', '')
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching nearby places: {e}")
            return None

    async def search_place_by_keyword(self, keyword: str, latitude: float = None, longitude: float = None) -> Optional[PlaceInfo]:
        """
        키워드로 장소를 검색합니다.
        위치가 지정되지 않으면 서울 중심부를 기본으로 사용합니다.
        """
        try:
            search_url = f"{self.base_url}/search/keyword.json"
            params = {
                "query": keyword,
                "size": 1
            }
            
            # 위치가 지정되지 않으면 서울 중심부(시청) 좌표를 기본으로 사용
            if latitude is None or longitude is None:
                latitude = 37.5665  # 서울시청 위도
                longitude = 126.9780  # 서울시청 경도
                logger.info(f"위치 미지정으로 서울 중심부 기본 좌표 사용: {latitude}, {longitude}")
            
            params.update({
                "x": longitude,
                "y": latitude,
                "radius": 20000,  # 20km 반경으로 확장
                "sort": "distance"
            })
            
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            documents = data.get('documents', [])
            
            if documents:
                place = documents[0]
                return PlaceInfo(
                    place_name=place.get('place_name', ''),
                    address=place.get('address_name', ''),
                    category=place.get('category_name', '')
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching place by keyword: {e}")
            return None

kakao_service = KakaoMapService()
