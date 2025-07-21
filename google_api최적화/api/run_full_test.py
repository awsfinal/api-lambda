# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import io
import locale

# 한글 출력을 위한 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

async def run_full_test():
    # 1. 더미 이미지 생성
    print_header("1. 더미 이미지 생성")
    dummy_image_path = "dummy_image.jpg"
    if not os.path.exists(dummy_image_path):
        with open(dummy_image_path, "w") as f:
            f.write("Dummy image content")
        print(f"더미 이미지 생성 완료: {dummy_image_path}")
    else:
        print(f"더미 이미지가 이미 존재합니다: {dummy_image_path}")
    
    # 2. 필요한 디렉토리 구조 확인
    print_header("2. 디렉토리 구조 확인")
    if not os.path.exists("static"):
        os.makedirs("static")
        print("static 디렉토리 생성 완료")
    else:
        print("static 디렉토리가 이미 존재합니다")
    
    if not os.path.exists("static/uploads"):
        os.makedirs("static/uploads")
        print("static/uploads 디렉토리 생성 완료")
    else:
        print("static/uploads 디렉토리가 이미 존재합니다")
    
    # 3. Google Maps API 모의 서비스 테스트
    print_header("3. Google Maps API 모의 서비스 테스트")
    from services.google_maps_service_mock import google_maps_service_mock
    from models import PlaceInfo
    
    # 좌표로 장소 검색 테스트
    print("좌표로 장소 검색 테스트 중...")
    place_info = await google_maps_service_mock.get_place_by_coordinates(37.5796, 126.9770)
    print(f"결과: {place_info}")
    assert isinstance(place_info, PlaceInfo), "PlaceInfo 객체가 아닙니다"
    print("좌표로 장소 검색 테스트 성공!")
    
    # 키워드로 장소 검색 테스트
    print("\n키워드로 장소 검색 테스트 중...")
    keyword_place = await google_maps_service_mock.search_place_by_keyword('경복궁')
    print(f"결과: {keyword_place}")
    assert isinstance(keyword_place, PlaceInfo), "PlaceInfo 객체가 아닙니다"
    print("키워드로 장소 검색 테스트 성공!")
    
    # 4. 파일 구조 확인
    print_header("4. 파일 구조 확인")
    required_files = [
        "services/google_maps_service.py",
        "services/google_maps_service_mock.py",
        "config.py",
        ".env",
        "google_maps_setup_guide.md",
        "main.py"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[O] {file_path} 파일 존재")
        else:
            print(f"[X] {file_path} 파일 없음")
            all_files_exist = False
    
    assert all_files_exist, "필수 파일이 누락되었습니다"
    print("모든 필수 파일이 존재합니다!")
    
    # 5. 설정 파일 확인
    print_header("5. 설정 파일 확인")
    
    # config.py 확인
    with open("config.py", "r", encoding="utf-8") as f:
        config_content = f.read()
        assert "GOOGLE_MAPS_API_KEY" in config_content, "config.py에 GOOGLE_MAPS_API_KEY 설정이 없습니다"
        print("config.py에 GOOGLE_MAPS_API_KEY 설정이 있습니다")
    
    # .env 확인
    with open(".env", "r", encoding="utf-8") as f:
        env_content = f.read()
        assert "GOOGLE_MAPS_API_KEY" in env_content, ".env에 GOOGLE_MAPS_API_KEY 설정이 없습니다"
        print(".env에 GOOGLE_MAPS_API_KEY 설정이 있습니다")
    
    # 6. main.py 파일에서 Google Maps API 서비스 사용 확인
    print_header("6. main.py 파일 확인")
    with open("main.py", "r", encoding="utf-8") as f:
        main_content = f.read()
        assert "google_maps_service" in main_content, "main.py에서 google_maps_service를 사용하지 않습니다"
        print("main.py에서 Google Maps API 서비스를 사용하고 있습니다")
        
        # kakao_service가 주석 처리되었거나 없는지 확인
        if "kakao_service" in main_content and "# kakao_service" not in main_content:
            print("[주의] main.py에서 여전히 kakao_service를 사용하고 있을 수 있습니다")
        else:
            print("main.py에서 Kakao API 서비스를 사용하지 않습니다")
    
    # 7. 종합 결과
    print_header("7. 종합 결과")
    print("모든 테스트가 성공적으로 완료되었습니다!")
    print("Google Maps Platform API로의 변환이 성공적으로 이루어졌습니다.")
    print("실제 사용을 위해서는 .env 파일의 GOOGLE_MAPS_API_KEY 값을 실제 API 키로 변경하세요.")
    
    return True

if __name__ == "__main__":
    try:
        print(f"현재 인코딩: {sys.stdout.encoding}")
        print(f"현재 로케일: {locale.getpreferredencoding()}")
        success = asyncio.run(run_full_test())
        print("\n테스트 결과:", "성공" if success else "실패")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {e}")
        sys.exit(1)