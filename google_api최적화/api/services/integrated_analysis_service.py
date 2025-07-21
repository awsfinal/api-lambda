"""
통합 이미지 분석 서비스
Rekognition + Textract + 카카오맵 + Google Vision 결합
"""
import logging
from typing import Dict, List, Optional, Any
from services.vision_service import google_vision_service
from services.kakao_service import kakao_service

logger = logging.getLogger(__name__)

class IntegratedAnalysisService:
    def __init__(self):
        self.confidence_threshold = 80
    
    async def analyze_image_comprehensive(
        self, 
        image_bytes: bytes, 
        gps_coords: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        종합적인 이미지 분석
        """
        analysis_result = {
            'landmarks': [],
            'objects': [],
            'texts': [],
            'business_names': [],
            'location_info': None,
            'analysis_methods': []
        }
        
        try:
            # 1. AWS Rekognition으로 랜드마크 및 객체 인식
            landmarks = await self._detect_landmarks_mock(image_bytes)
            if landmarks:
                analysis_result['landmarks'] = landmarks
                analysis_result['analysis_methods'].append('rekognition_landmarks')
            
            objects = await self._detect_objects_mock(image_bytes)
            if objects:
                analysis_result['objects'] = objects
                analysis_result['analysis_methods'].append('rekognition_objects')
            
            # 2. 텍스트 추출 (Google Vision 우선, Textract 보조)
            texts = await google_vision_service.extract_korean_text(image_bytes)
            if texts:
                analysis_result['texts'] = texts
                analysis_result['analysis_methods'].append('google_vision_text')
                
                # 상호명 추출
                business_names = google_vision_service.extract_business_names(texts)
                analysis_result['business_names'] = business_names
            
            # 3. GPS 기반 위치 정보
            if gps_coords:
                location_info = await kakao_service.get_place_by_coordinates(
                    gps_coords['latitude'], 
                    gps_coords['longitude']
                )
                if location_info:
                    analysis_result['location_info'] = location_info.dict()
                    analysis_result['analysis_methods'].append('kakao_gps')
            
            # 4. 텍스트 기반 장소 검색 (상호명이 있는 경우)
            if analysis_result['business_names'] and gps_coords:
                text_based_places = await self._search_places_by_text(
                    analysis_result['business_names'], 
                    gps_coords
                )
                if text_based_places:
                    analysis_result['text_based_places'] = text_based_places
                    analysis_result['analysis_methods'].append('kakao_text_search')
            
            # 5. 종합 결과 생성
            final_result = self._generate_comprehensive_result(analysis_result)
            
            logger.info(f"통합 분석 완료: {analysis_result['analysis_methods']}")
            return final_result
            
        except Exception as e:
            logger.error(f"통합 이미지 분석 실패: {e}")
            return {'error': str(e), 'analysis_methods': []}
    
    async def _detect_landmarks_mock(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Mock 랜드마크 인식 (실제로는 AWS Rekognition 사용)"""
        # 실제 구현에서는 AWS Rekognition detect_labels 사용
        return [
            {'name': '동방명주', 'confidence': 95.5, 'type': 'landmark'},
            {'name': '상하이타워', 'confidence': 88.2, 'type': 'landmark'}
        ]
    
    async def _detect_objects_mock(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Mock 객체 인식"""
        return [
            {'name': 'Building', 'confidence': 92.1},
            {'name': 'Street', 'confidence': 87.3},
            {'name': 'Sign', 'confidence': 84.6}
        ]
    
    async def _search_places_by_text(
        self, 
        business_names: List[str], 
        gps_coords: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """텍스트 기반 장소 검색"""
        places = []
        
        for name in business_names[:3]:  # 최대 3개까지만
            try:
                place_info = await kakao_service.search_place_by_keyword(
                    name, 
                    gps_coords['latitude'], 
                    gps_coords['longitude']
                )
                if place_info:
                    places.append({
                        'search_text': name,
                        'place_info': place_info.dict()
                    })
            except Exception as e:
                logger.warning(f"텍스트 '{name}' 장소 검색 실패: {e}")
        
        return places
    
    def _generate_comprehensive_result(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """종합 결과 생성"""
        result = {
            'success': True,
            'primary_location': None,
            'alternative_locations': [],
            'detected_texts': analysis.get('texts', []),
            'business_names': analysis.get('business_names', []),
            'landmarks': analysis.get('landmarks', []),
            'objects': analysis.get('objects', []),
            'analysis_methods': analysis.get('analysis_methods', []),
            'confidence_score': 0
        }
        
        # 우선순위: 랜드마크 > GPS 위치 > 텍스트 기반 검색
        if analysis.get('landmarks'):
            result['primary_location'] = {
                'type': 'landmark',
                'name': analysis['landmarks'][0]['name'],
                'confidence': analysis['landmarks'][0]['confidence']
            }
            result['confidence_score'] = analysis['landmarks'][0]['confidence']
        
        elif analysis.get('location_info'):
            result['primary_location'] = {
                'type': 'gps_location',
                **analysis['location_info']
            }
            result['confidence_score'] = 85  # GPS 기반은 85점
        
        elif analysis.get('text_based_places'):
            result['primary_location'] = {
                'type': 'text_based',
                **analysis['text_based_places'][0]['place_info']
            }
            result['alternative_locations'] = analysis['text_based_places'][1:]
            result['confidence_score'] = 70  # 텍스트 기반은 70점
        
        return result

# 통합 분석 서비스 인스턴스
integrated_analysis_service = IntegratedAnalysisService()
