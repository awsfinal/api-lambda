"""
Google Vision API 서비스 - 한글 텍스트 인식에 특화
"""
import base64
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GoogleVisionService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"
    
    async def extract_korean_text(self, image_bytes: bytes) -> List[Dict[str, str]]:
        """
        Google Vision API로 한글 텍스트 추출
        """
        if not self.api_key:
            logger.warning("Google Vision API 키가 없어 Mock 데이터 반환")
            return self._mock_korean_text()
        
        try:
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # API 요청 데이터
            request_data = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 50
                            }
                        ],
                        "imageContext": {
                            "languageHints": ["ko", "en"]  # 한국어, 영어 우선
                        }
                    }
                ]
            }
            
            # API 호출
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_vision_response(result)
            else:
                logger.error(f"Google Vision API 오류: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Google Vision API 호출 실패: {e}")
            return []
    
    def _parse_vision_response(self, response: dict) -> List[Dict[str, str]]:
        """Vision API 응답 파싱"""
        texts = []
        
        if 'responses' in response and response['responses']:
            text_annotations = response['responses'][0].get('textAnnotations', [])
            
            for annotation in text_annotations[1:]:  # 첫 번째는 전체 텍스트이므로 제외
                text = annotation.get('description', '').strip()
                if text and len(text) >= 2:  # 최소 2글자 이상
                    texts.append({
                        'text': text,
                        'confidence': 90,  # Google Vision은 신뢰도를 직접 제공하지 않음
                        'type': 'word'
                    })
        
        return texts
    
    def _mock_korean_text(self) -> List[Dict[str, str]]:
        """Mock 한글 텍스트 데이터"""
        return [
            {'text': '홍대맛집', 'confidence': 95, 'type': 'word'},
            {'text': '24시간', 'confidence': 88, 'type': 'word'},
            {'text': '카페베네', 'confidence': 92, 'type': 'word'},
            {'text': '치킨집', 'confidence': 87, 'type': 'word'},
            {'text': '편의점', 'confidence': 90, 'type': 'word'}
        ]
    
    def extract_business_names(self, texts: List[Dict[str, str]]) -> List[str]:
        """상호명으로 보이는 텍스트 추출"""
        import re
        
        business_patterns = [
            r'.*카페.*', r'.*커피.*', r'.*식당.*', r'.*맛집.*',
            r'.*치킨.*', r'.*피자.*', r'.*중국.*', r'.*일식.*',
            r'.*편의점.*', r'.*마트.*', r'.*약국.*', r'.*병원.*',
            r'.*미용.*', r'.*노래방.*', r'.*PC방.*', r'.*학원.*'
        ]
        
        business_names = []
        korean_pattern = re.compile(r'[가-힣]')
        
        for text_info in texts:
            text = text_info['text']
            
            # 한글이 포함되어 있고
            if korean_pattern.search(text):
                # 비즈니스 패턴과 매칭되거나
                if any(re.match(pattern, text) for pattern in business_patterns):
                    business_names.append(text)
                # 적절한 길이의 한글 상호명으로 보이는 경우
                elif 2 <= len(text) <= 15 and not re.search(r'[0-9]{3,}', text):
                    business_names.append(text)
        
        return list(set(business_names))  # 중복 제거

# Mock 서비스 인스턴스
google_vision_service = GoogleVisionService()
