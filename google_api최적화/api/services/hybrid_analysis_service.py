"""
하이브리드 이미지 분석 서비스
GenAI + 기존 Vision API + 카카오맵 최적 조합
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HybridAnalysisService:
    def __init__(self):
        self.analysis_strategies = {
            'landmark': self._analyze_landmark_strategy,
            'commercial': self._analyze_commercial_strategy,
            'residential': self._analyze_residential_strategy,
            'traditional': self._analyze_traditional_strategy
        }
    
    async def analyze_with_optimal_strategy(
        self, 
        image_bytes: bytes, 
        gps_info: Dict = None
    ) -> Dict[str, Any]:
        """
        최적 전략으로 이미지 분석
        """
        try:
            # 1단계: GenAI로 장소 유형 및 맥락 파악
            from services.genai_vision_service import genai_vision_service
            context_analysis = await genai_vision_service.analyze_place_context(image_bytes, gps_info)
            
            if not context_analysis.get('success'):
                return await self._fallback_analysis(image_bytes, gps_info)
            
            place_analysis = context_analysis['place_analysis']
            place_category = place_analysis.get('place_category', 'commercial')
            
            # 2단계: 장소 유형에 따른 최적 분석 전략 선택
            strategy_func = self.analysis_strategies.get(
                place_category, 
                self._analyze_commercial_strategy
            )
            
            detailed_analysis = await strategy_func(image_bytes, gps_info, place_analysis)
            
            return {
                'success': True,
                'analysis_approach': 'hybrid_optimal',
                'context_analysis': context_analysis,
                'detailed_analysis': detailed_analysis,
                'final_recommendation': self._generate_final_recommendation(
                    place_analysis, detailed_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"하이브리드 분석 실패: {e}")
            return await self._fallback_analysis(image_bytes, gps_info)
    
    async def _analyze_landmark_strategy(
        self, 
        image_bytes: bytes, 
        gps_info: Dict, 
        context: Dict
    ) -> Dict[str, Any]:
        """랜드마크 분석 전략"""
        # AWS Rekognition 중심 + GPS 보조
        from services.integrated_analysis_service import integrated_analysis_service
        
        result = await integrated_analysis_service.analyze_image_comprehensive(image_bytes, gps_info)
        
        return {
            'strategy': 'landmark_focused',
            'primary_method': 'aws_rekognition',
            'secondary_method': 'gps_location',
            'confidence': result.get('confidence_score', 0),
            'result': result
        }
    
    async def _analyze_commercial_strategy(
        self, 
        image_bytes: bytes, 
        gps_info: Dict, 
        context: Dict
    ) -> Dict[str, Any]:
        """상업지역 분석 전략 (상가거리, 쇼핑몰 등)"""
        # 텍스트 추출 + 카카오맵 검색 중심
        from services.vision_service import google_vision_service
        from services.kakao_service import kakao_service
        
        # 1. 텍스트 추출
        texts = await google_vision_service.extract_korean_text(image_bytes)
        business_names = google_vision_service.extract_business_names(texts)
        
        # 2. GPS 기반 위치 정보
        location_info = None
        if gps_info:
            location_info = await kakao_service.get_place_by_coordinates(
                gps_info['latitude'], gps_info['longitude']
            )
        
        # 3. 텍스트 기반 장소 검색
        text_based_places = []
        if business_names and gps_info:
            for name in business_names[:3]:
                place = await kakao_service.search_place_by_keyword(
                    name, gps_info['latitude'], gps_info['longitude']
                )
                if place:
                    text_based_places.append({
                        'search_text': name,
                        'place_info': place.dict()
                    })
        
        return {
            'strategy': 'commercial_focused',
            'primary_method': 'text_extraction_kakao_search',
            'secondary_method': 'gps_location',
            'confidence': 75,
            'extracted_texts': [t['text'] for t in texts],
            'business_names': business_names,
            'location_info': location_info.dict() if location_info else None,
            'text_based_places': text_based_places
        }
    
    async def _analyze_residential_strategy(
        self, 
        image_bytes: bytes, 
        gps_info: Dict, 
        context: Dict
    ) -> Dict[str, Any]:
        """주거지역 분석 전략"""
        # GPS 중심 + 주변 시설 검색
        from services.kakao_service import kakao_service
        
        location_info = None
        nearby_facilities = []
        
        if gps_info:
            # 기본 위치 정보
            location_info = await kakao_service.get_place_by_coordinates(
                gps_info['latitude'], gps_info['longitude']
            )
            
            # 주변 편의시설 검색
            facility_keywords = ['편의점', '마트', '병원', '학교', '공원']
            for keyword in facility_keywords:
                facility = await kakao_service.search_place_by_keyword(
                    keyword, gps_info['latitude'], gps_info['longitude']
                )
                if facility:
                    nearby_facilities.append({
                        'type': keyword,
                        'info': facility.dict()
                    })
        
        return {
            'strategy': 'residential_focused',
            'primary_method': 'gps_location',
            'secondary_method': 'nearby_facilities',
            'confidence': 80,
            'location_info': location_info.dict() if location_info else None,
            'nearby_facilities': nearby_facilities
        }
    
    async def _analyze_traditional_strategy(
        self, 
        image_bytes: bytes, 
        gps_info: Dict, 
        context: Dict
    ) -> Dict[str, Any]:
        """전통시장/문화재 분석 전략"""
        # 통합 분석 (모든 방법 조합)
        from services.integrated_analysis_service import integrated_analysis_service
        
        result = await integrated_analysis_service.analyze_image_comprehensive(image_bytes, gps_info)
        
        return {
            'strategy': 'traditional_comprehensive',
            'primary_method': 'integrated_analysis',
            'confidence': result.get('confidence_score', 0),
            'result': result
        }
    
    async def _fallback_analysis(self, image_bytes: bytes, gps_info: Dict) -> Dict[str, Any]:
        """GenAI 실패 시 대체 분석"""
        from services.integrated_analysis_service import integrated_analysis_service
        
        result = await integrated_analysis_service.analyze_image_comprehensive(image_bytes, gps_info)
        
        return {
            'success': True,
            'analysis_approach': 'fallback_traditional',
            'result': result
        }
    
    def _generate_final_recommendation(self, context: Dict, detailed: Dict) -> str:
        """최종 추천사항 생성"""
        place_type = context.get('place_type', '알 수 없음')
        strategy = detailed.get('strategy', 'unknown')
        
        recommendations = {
            'landmark_focused': f"{place_type}는 유명한 랜드마크입니다. AWS Rekognition 결과를 신뢰하고 GPS 정보로 정확한 위치를 확인하세요.",
            'commercial_focused': f"{place_type}는 상업지역입니다. 간판에서 추출한 상호명으로 카카오맵 검색을 통해 구체적인 상점 정보를 찾으세요.",
            'residential_focused': f"{place_type}는 주거지역입니다. GPS 기반 위치 정보와 주변 편의시설 정보를 활용하세요.",
            'traditional_comprehensive': f"{place_type}는 전통적인 장소입니다. 모든 분석 방법을 종합하여 문화적 맥락을 파악하세요."
        }
        
        return recommendations.get(strategy, "상황에 맞는 적절한 분석 방법을 선택하여 사용하세요.")

# 하이브리드 분석 서비스 인스턴스
hybrid_analysis_service = HybridAnalysisService()
