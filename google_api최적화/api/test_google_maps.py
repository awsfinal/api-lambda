#!/usr/bin/env python3
"""
Google Maps Platform API 테스트 스크립트
"""
import requests
import json
from config import settings

def test_google_maps_api():
    """Google Maps API 연결 테스트"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    
    print(f"API 키: {api_key}")
    print("="*50)
    
    # 1. 장소 검색 테스트 (Places API - Text Search)
    print("1. 장소 검색 테스트")
    try:
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        params = {
            'query': '경복궁',
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print("✅ 장소 검색 성공!")
                for i, place in enumerate(data.get('results', [])[:3]):
                    print(f"  {i+1}. {place.get('name')} - {place.get('formatted_address')}")
            else:
                print(f"❌ 장소 검색 실패: {data.get('status')}")
        else:
            print(f"❌ 장소 검색 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 장소 검색 오류: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. 좌표 → 주소 변환 테스트 (Geocoding API)
    print("2. 좌표 → 주소 변환 테스트 (경복궁 좌표)")
    try:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'latlng': '37.5796,126.9770',  # 경복궁 좌표
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print("✅ 좌표 변환 성공!")
                if data.get('results'):
                    print(f"  주소: {data['results'][0].get('formatted_address')}")
                    
                    # 주소 구성요소 출력
                    components = data['results'][0].get('address_components', [])
                    for component in components[:3]:  # 처음 3개만 출력
                        print(f"  구성요소: {component.get('long_name')} ({', '.join(component.get('types', []))})")
            else:
                print(f"❌ 좌표 변환 실패: {data.get('status')}")
        else:
            print(f"❌ 좌표 변환 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 좌표 변환 오류: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 주변 장소 검색 테스트 (Places API - Nearby Search)
    print("3. 주변 장소 검색 테스트 (관광명소)")
    try:
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'location': '37.5796,126.9770',  # 경복궁 좌표
            'radius': 1000,
            'type': 'tourist_attraction',
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print("✅ 주변 장소 검색 성공!")
                for i, place in enumerate(data.get('results', [])[:3]):
                    print(f"  {i+1}. {place.get('name')} - {place.get('vicinity')}")
            else:
                print(f"❌ 주변 장소 검색 실패: {data.get('status')}")
        else:
            print(f"❌ 주변 장소 검색 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 주변 장소 검색 오류: {e}")

def check_api_permissions():
    """API 권한 확인"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    
    print("API 권한 확인 중...")
    
    # 각 API 엔드포인트별 권한 확인
    endpoints = [
        ('장소 검색 (Text Search)', 'https://maps.googleapis.com/maps/api/place/textsearch/json', {'query': '테스트', 'key': api_key}),
        ('좌표 변환 (Geocoding)', 'https://maps.googleapis.com/maps/api/geocode/json', {'latlng': '37.5796,126.9770', 'key': api_key}),
        ('주변 장소 검색 (Nearby Search)', 'https://maps.googleapis.com/maps/api/place/nearbysearch/json', {'location': '37.5796,126.9770', 'radius': 1000, 'key': api_key})
    ]
    
    for name, url, params in endpoints:
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                if data.get('status') == 'OK':
                    print(f"[OK] {name}: 사용 가능")
                elif data.get('status') == 'REQUEST_DENIED':
                    print(f"[ERROR] {name}: 권한 없음 - {data.get('error_message', '')}")
                else:
                    print(f"[WARNING] {name}: 상태 {data.get('status')}")
            else:
                print(f"[ERROR] {name}: HTTP 오류 {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {name}: 오류 - {e}")

if __name__ == "__main__":
    print("Google Maps Platform API 테스트 시작")
    print("="*50)
    
    check_api_permissions()
    print("\n" + "="*50 + "\n")
    test_google_maps_api()