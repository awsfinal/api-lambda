"""
Google Maps Platform API Mock 서비스 (테스트용)
실제 API 권한이 활성화될 때까지 사용
"""
import logging
from typing import Optional
from models import PlaceInfo

logger = logging.getLogger(__name__)

class GoogleMapsServiceMock:
    """Google Maps API Mock 서비스"""
    
    def __init__(self):
        # 테스트용 장소 데이터
        self.mock_places = {
            "경복궁": PlaceInfo(
                place_name="경복궁",
                address="서울특별시 종로구 사직로 161",
                category="Tourist Attraction"
            ),
            "창덕궁": PlaceInfo(
                place_name="창덕궁",
                address="서울특별시 종로구 율곡로 99",
                category="Tourist Attraction"
            ),
            "남산타워": PlaceInfo(
                place_name="N서울타워",
                address="서울특별시 용산구 남산공원길 105",
                category="Point Of Interest"
            ),
            "한강공원": PlaceInfo(
                place_name="한강공원",
                address="서울특별시 영등포구 여의동로 330",
                category="Park"
            )
        }
        
        # GPS 좌표별 장소 정보 (대략적인 위치)
        self.coordinate_places = [
            {
                "lat_range": (37.575, 37.585),
                "lng_range": (126.970, 126.985),
                "place": PlaceInfo(
                    place_name="경복궁",
                    address="서울특별시 종로구 사직로 161",
                    category="Tourist Attraction"
                )
            },
            {
                "lat_range": (37.570, 37.580),
                "lng_range": (126.985, 127.000),
                "place": PlaceInfo(
                    place_name="창덕궁",
                    address="서울특별시 종로구 율곡로 99",
                    category="Tourist Attraction"
                )
            },
            {
                "lat_range": (37.545, 37.555),
                "lng_range": (126.985, 127.000),
                "place": PlaceInfo(
                    place_name="N서울타워",
                    address="서울특별시 용산구 남산공원길 105",
                    category="Point Of Interest"
                )
            }
        ]

    async def get_place_by_coordinates(self, latitude: float, longitude: float) -> Optional[PlaceInfo]:
        """
        GPS 좌표를 기반으로 장소 정보를 조회합니다. (Mock)
        """
        logger.info(f"Mock: GPS 좌표로 장소 검색 - 위도: {latitude}, 경도: {longitude}")
        
        # 좌표 범위에 따른 장소 반환
        for coord_place in self.coordinate_places:
            lat_min, lat_max = coord_place["lat_range"]
            lng_min, lng_max = coord_place["lng_range"]
            
            if (lat_min <= latitude <= lat_max and 
                lng_min <= longitude <= lng_max):
                logger.info(f"Mock: 찾은 장소 - {coord_place['place'].place_name}")
                return coord_place["place"]
        
        # 기본 장소 반환
        return PlaceInfo(
            place_name="서울시 일반 지역",
            address=f"서울특별시 (위도: {latitude:.4f}, 경도: {longitude:.4f})",
            category="General"
        )

    async def search_place_by_keyword(self, keyword: str, latitude: float = None, longitude: float = None) -> Optional[PlaceInfo]:
        """
        키워드로 장소를 검색합니다. (Mock)
        """
        logger.info(f"Mock: 키워드 검색 - {keyword}")
        
        # 키워드 매칭 (부분 일치)
        for place_key, place_info in self.mock_places.items():
            if keyword in place_key or keyword in place_info.place_name:
                logger.info(f"Mock: 키워드 매칭 성공 - {place_info.place_name}")
                return place_info
        
        # 카테고리별 검색
        category_keywords = {
            "궁": ["경복궁", "창덕궁"],
            "타워": ["남산타워"],
            "공원": ["한강공원"],
            "관광": ["경복궁", "창덕궁", "남산타워"]
        }
        
        for category, places in category_keywords.items():
            if category in keyword:
                place_key = places[0]  # 첫 번째 장소 반환
                return self.mock_places[place_key]
        
        # 검색 결과 없음
        logger.info(f"Mock: 키워드 '{keyword}'에 대한 검색 결과 없음")
        return None

    async def _get_place_details(self, place_id: str) -> Optional[PlaceInfo]:
        """
        장소 ID로 상세 정보를 조회합니다. (Mock)
        """
        # 테스트용 ID 매핑
        place_id_map = {
            "gbg": "경복궁",
            "cdg": "창덕궁",
            "nst": "남산타워",
            "hgp": "한강공원"
        }
        
        if place_id in place_id_map:
            return self.mock_places[place_id_map[place_id]]
        
        return None

    async def _search_nearby_places(self, latitude: float, longitude: float, radius: int = 500) -> Optional[PlaceInfo]:
        """
        주변 관심 장소를 검색합니다. (Mock)
        """
        return await self.get_place_by_coordinates(latitude, longitude)

# Mock 서비스 인스턴스
google_maps_service_mock = GoogleMapsServiceMock()