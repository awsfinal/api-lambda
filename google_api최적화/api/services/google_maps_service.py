import requests
import logging
from typing import Optional
from config import settings
from models import PlaceInfo

logger = logging.getLogger(__name__)

class GoogleMapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def get_place_by_coordinates(self, latitude: float, longitude: float) -> Optional[PlaceInfo]:
        """
        GPS 좌표를 기반으로 장소 정보를 조회합니다.
        """
        try:
            # 좌표 -> 주소 변환 (Reverse Geocoding)
            geocode_url = f"{self.base_url}/geocode/json"
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key
            }
            
            response = requests.get(geocode_url, params=params)
            response.raise_for_status()
            
            geocode_data = response.json()
            
            if geocode_data.get('status') != 'OK' or not geocode_data.get('results'):
                logger.warning(f"No address found for coordinates: {latitude}, {longitude}")
                return None
            
            # 주소 정보 추출
            address_info = geocode_data['results'][0]
            full_address = address_info.get('formatted_address', '')
            
            # 주변 장소 검색 (Places API - Nearby Search)
            place_info = await self._search_nearby_places(latitude, longitude)
            
            if place_info:
                place_info.address = full_address
                return place_info
            
            # 주변 장소가 없으면 기본 정보 반환
            # 주소 구성요소에서 지역명 추출
            place_name = "알 수 없는 장소"
            for component in address_info.get('address_components', []):
                if 'sublocality' in component.get('types', []) or 'locality' in component.get('types', []):
                    place_name = component.get('long_name', place_name)
                    break
            
            return PlaceInfo(
                place_name=place_name,
                address=full_address,
                category="일반"
            )
            
        except requests.RequestException as e:
            logger.error(f"Google Maps API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting place info: {e}")
            return None

    async def _search_nearby_places(self, latitude: float, longitude: float, radius: int = 500) -> Optional[PlaceInfo]:
        """
        주변 관심 장소를 검색합니다.
        """
        try:
            nearby_url = f"{self.base_url}/place/nearbysearch/json"
            
            # 관광명소, 문화시설 등을 우선 검색
            place_types = ["tourist_attraction", "museum", "park"]
            
            for place_type in place_types:
                params = {
                    "location": f"{latitude},{longitude}",
                    "radius": radius,
                    "type": place_type,
                    "key": self.api_key
                }
                
                response = requests.get(nearby_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    place = results[0]  # 가장 가까운 장소
                    
                    # 장소 상세 정보 조회
                    place_id = place.get('place_id')
                    if place_id:
                        details = await self._get_place_details(place_id)
                        if details:
                            return details
                    
                    # 상세 정보가 없으면 기본 정보 반환
                    return PlaceInfo(
                        place_name=place.get('name', ''),
                        address=place.get('vicinity', ''),
                        category=place.get('types', [''])[0].replace('_', ' ').title() if place.get('types') else ''
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching nearby places: {e}")
            return None

    async def _get_place_details(self, place_id: str) -> Optional[PlaceInfo]:
        """
        장소 ID로 상세 정보를 조회합니다.
        """
        try:
            details_url = f"{self.base_url}/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_address,types",
                "key": self.api_key
            }
            
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('result'):
                return None
            
            result = data.get('result', {})
            
            # 카테고리 변환
            category = ''
            if result.get('types'):
                # 첫 번째 타입을 카테고리로 사용
                category = result.get('types', [''])[0].replace('_', ' ').title()
            
            return PlaceInfo(
                place_name=result.get('name', ''),
                address=result.get('formatted_address', ''),
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return None

    async def search_place_by_keyword(self, keyword: str, latitude: float = None, longitude: float = None) -> Optional[PlaceInfo]:
        """
        키워드로 장소를 검색합니다.
        위치가 지정되지 않으면 서울 중심부를 기본으로 사용합니다.
        """
        try:
            # 위치가 지정되지 않으면 서울 중심부(시청) 좌표를 기본으로 사용
            if latitude is None or longitude is None:
                latitude = 37.5665  # 서울시청 위도
                longitude = 126.9780  # 서울시청 경도
                logger.info(f"위치 미지정으로 서울 중심부 기본 좌표 사용: {latitude}, {longitude}")
            
            # Text Search API 사용
            search_url = f"{self.base_url}/place/textsearch/json"
            params = {
                "query": keyword,
                "location": f"{latitude},{longitude}",
                "radius": 20000,  # 20km 반경
                "key": self.api_key
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                place = results[0]
                
                # 장소 상세 정보 조회
                place_id = place.get('place_id')
                if place_id:
                    details = await self._get_place_details(place_id)
                    if details:
                        return details
                
                # 상세 정보가 없으면 기본 정보 반환
                return PlaceInfo(
                    place_name=place.get('name', ''),
                    address=place.get('formatted_address', ''),
                    category=place.get('types', [''])[0].replace('_', ' ').title() if place.get('types') else ''
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching place by keyword: {e}")
            return None

google_maps_service = GoogleMapsService()