#!/usr/bin/env python3
"""
카카오맵 API 테스트 스크립트
"""
import requests
import json
from config import settings

def test_kakao_api():
    """카카오 API 연결 테스트"""
    api_key = settings.KAKAO_REST_API_KEY
    headers = {'Authorization': f'KakaoAK {api_key}'}
    
    print(f"API 키: {api_key}")
    print("="*50)
    
    # 1. 키워드 검색 테스트
    print("1. 키워드 검색 테스트")
    try:
        url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
        params = {'query': '경복궁', 'size': 5}
        
        response = requests.get(url, headers=headers, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 키워드 검색 성공!")
            for i, place in enumerate(data.get('documents', [])[:3]):
                print(f"  {i+1}. {place.get('place_name')} - {place.get('address_name')}")
        else:
            print(f"❌ 키워드 검색 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 키워드 검색 오류: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. 좌표 → 주소 변환 테스트
    print("2. 좌표 → 주소 변환 테스트 (경복궁 좌표)")
    try:
        url = 'https://dapi.kakao.com/v2/local/geo/coord2address.json'
        params = {
            'x': 126.9770,  # 경복궁 경도
            'y': 37.5796,   # 경복궁 위도
            'input_coord': 'WGS84'
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 좌표 변환 성공!")
            for doc in data.get('documents', []):
                if doc.get('road_address'):
                    print(f"  도로명: {doc['road_address']['address_name']}")
                if doc.get('address'):
                    print(f"  지번: {doc['address']['address_name']}")
        else:
            print(f"❌ 좌표 변환 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 좌표 변환 오류: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 카테고리 검색 테스트
    print("3. 카테고리 검색 테스트 (관광명소)")
    try:
        url = 'https://dapi.kakao.com/v2/local/search/category.json'
        params = {
            'category_group_code': 'AT4',  # 관광명소
            'x': 126.9770,
            'y': 37.5796,
            'radius': 1000,
            'size': 3
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 카테고리 검색 성공!")
            for i, place in enumerate(data.get('documents', [])):
                print(f"  {i+1}. {place.get('place_name')} - {place.get('category_name')}")
        else:
            print(f"❌ 카테고리 검색 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 카테고리 검색 오류: {e}")

def check_api_permissions():
    """API 권한 확인"""
    api_key = settings.KAKAO_REST_API_KEY
    headers = {'Authorization': f'KakaoAK {api_key}'}
    
    print("API 권한 확인 중...")
    
    # 각 API 엔드포인트별 권한 확인
    endpoints = [
        ('키워드 검색', 'https://dapi.kakao.com/v2/local/search/keyword.json', {'query': '테스트'}),
        ('좌표 변환', 'https://dapi.kakao.com/v2/local/geo/coord2address.json', {'x': 127, 'y': 37}),
        ('카테고리 검색', 'https://dapi.kakao.com/v2/local/search/category.json', {'category_group_code': 'MT1', 'x': 127, 'y': 37})
    ]
    
    for name, url, params in endpoints:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                print(f"✅ {name}: 사용 가능")
            elif response.status_code == 403:
                error_data = response.json()
                print(f"❌ {name}: 권한 없음 - {error_data.get('message', '')}")
            else:
                print(f"⚠️ {name}: 상태 코드 {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: 오류 - {e}")

if __name__ == "__main__":
    print("카카오맵 API 테스트 시작")
    print("="*50)
    
    check_api_permissions()
    print("\n" + "="*50 + "\n")
    test_kakao_api()
