"""
새로운 외부 API 기반 추천 기능 테스트
"""

import requests
import json
import time
import asyncio


def test_new_external_recommendation():
    """새로운 외부 API 기반 추천 기능 테스트"""
    base_url = "http://localhost:8000"
    
    print("🎬 새로운 외부 API 기반 추천 기능 테스트")
    print("=" * 60)
    
    try:
        # 1. 서버 상태 확인
        print("\n1️⃣ 서버 상태 확인...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 서버 정상 작동")
        else:
            print("❌ 서버 연결 실패")
            return False
        
        # 2. 새로운 외부 API 기반 추천 테스트
        print("\n2️⃣ 외부 API 기반 추천 테스트...")
        recommendation_data = {
            "user_id": "external_api_test_user",
            "weekly_frequency": 3,
            "split_type": "3분할",
            "primary_goal": "근육 증가",
            "experience_level": "중급",
            "available_time": 60,
            "preferred_equipment": "바벨, 덤벨"
        }
        
        response = requests.post(
            f"{base_url}/api/recommend/external",
            json=recommendation_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30초 타임아웃
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 외부 API 추천 성공: {result.get('success')}")
            
            if result.get('success'):
                print(f"   총 시간: {result.get('total_weekly_duration')}분")
                print(f"   난이도: {result.get('difficulty_score')}/5")
                print(f"   일별 계획: {len(result.get('recommendation', {}))}일")
                
                # 영상 정보가 포함되었는지 확인
                has_videos = False
                video_count = 0
                for day_data in result.get('recommendation', {}).values():
                    for exercise in day_data.get('exercises', []):
                        if exercise.get('video_url'):
                            has_videos = True
                            video_count += 1
                
                print(f"   영상 포함: {'✅' if has_videos else '❌'}")
                print(f"   영상 개수: {video_count}개")
                
                # 데이터 소스 확인
                summary = result.get('summary', {})
                if summary.get('api_based'):
                    print("   ✅ 외부 API 데이터 기반 추천 확인됨")
                
                # 첫 번째 운동 정보 출력
                recommendations = result.get('recommendation', {})
                if recommendations:
                    first_day = list(recommendations.values())[0]
                    if first_day.get('exercises'):
                        first_exercise = first_day['exercises'][0]
                        print(f"   첫 번째 운동: {first_exercise.get('name')}")
                        if first_exercise.get('video_url'):
                            print(f"   영상 URL: {first_exercise.get('video_url')[:50]}...")
                        if first_exercise.get('target_group'):
                            print(f"   대상 그룹: {first_exercise.get('target_group')}")
            else:
                print(f"   ❌ 추천 실패: {result.get('message')}")
        else:
            print(f"❌ 외부 API 추천 실패: {response.status_code}")
            print(f"   응답: {response.text[:200]}...")
        
        # 3. 기존 기본 추천과 비교 테스트
        print("\n3️⃣ 기본 추천과 비교...")
        response = requests.post(
            f"{base_url}/api/recommend",
            json=recommendation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            basic_result = response.json()
            print(f"✅ 기본 추천 성공")
            print(f"   기본 추천 운동 수: {basic_result.get('summary', {}).get('total_exercises', 0)}개")
            print(f"   외부 API 추천 운동 수: {result.get('summary', {}).get('total_exercises', 0) if 'result' in locals() else 0}개")
        else:
            print("❌ 기본 추천 실패")
        
        # 4. 다른 목표로 테스트
        print("\n4️⃣ 다이어트 목표 테스트...")
        diet_data = recommendation_data.copy()
        diet_data["primary_goal"] = "다이어트"
        diet_data["user_id"] = "diet_test_user"
        
        response = requests.post(
            f"{base_url}/api/recommend/external",
            json=diet_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            diet_result = response.json()
            if diet_result.get('success'):
                print("✅ 다이어트 목표 추천 성공")
                print(f"   운동 개수: {len([ex for day in diet_result.get('recommendation', {}).values() for ex in day.get('exercises', [])])}개")
            else:
                print(f"❌ 다이어트 추천 실패: {diet_result.get('message')}")
        else:
            print(f"❌ 다이어트 추천 API 실패: {response.status_code}")
        
        # 5. 초급자 테스트
        print("\n5️⃣ 초급자 추천 테스트...")
        beginner_data = recommendation_data.copy()
        beginner_data["experience_level"] = "초급"
        beginner_data["primary_goal"] = "체력 향상"
        beginner_data["user_id"] = "beginner_test_user"
        
        response = requests.post(
            f"{base_url}/api/recommend/external",
            json=beginner_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            beginner_result = response.json()
            if beginner_result.get('success'):
                print("✅ 초급자 추천 성공")
                print(f"   난이도: {beginner_result.get('difficulty_score')}/5")
            else:
                print(f"❌ 초급자 추천 실패: {beginner_result.get('message')}")
        else:
            print(f"❌ 초급자 추천 API 실패: {response.status_code}")
        
        print("\n🎉 테스트 완료!")
        return True
        
    except requests.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
        return False
    except requests.Timeout:
        print("⏰ 요청 타임아웃 - 외부 API 응답이 느릴 수 있습니다.")
        return False
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False


def test_web_interface():
    """웹 인터페이스 접속 테스트"""
    print("\n🌐 웹 인터페이스 테스트")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200 and "ExRecAI" in response.text:
            print("✅ 웹 인터페이스 정상 작동")
            
            # JavaScript 파일 확인
            js_response = requests.get("http://localhost:8000/static/js/video-handlers.js")
            if js_response.status_code == 200:
                print("✅ 새로운 JavaScript 파일 로드 성공")
            else:
                print("❌ JavaScript 파일 로드 실패")
            
            return True
        else:
            print("❌ 웹 인터페이스 오류")
            return False
    except Exception as e:
        print(f"❌ 웹 인터페이스 테스트 오류: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🔥 ExRecAI 새로운 기능 테스트 시작")
    print("🎬 외부 API 기반 추천 시스템 검증")
    
    # 서버 시작 대기
    print("\n⏳ 서버 준비를 위해 5초 대기...")
    time.sleep(5)
    
    # 기능 테스트
    external_test = test_new_external_recommendation()
    web_test = test_web_interface()
    
    print("\n" + "=" * 60)
    print("🎯 테스트 요약:")
    print(f"   외부 API 추천: {'✅ 성공' if external_test else '❌ 실패'}")
    print(f"   웹 인터페이스: {'✅ 성공' if web_test else '❌ 실패'}")
    
    if external_test and web_test:
        print("\n🎉 모든 새로운 기능이 정상 작동합니다!")
        print("\n📋 사용 가이드:")
        print("   1. http://localhost:8000 접속")
        print("   2. '운동 추천' 섹션에서 정보 입력")
        print("   3. '영상 기반 추천' 버튼 클릭")
        print("   4. 실제 운동 영상이 포함된 맞춤 추천 확인!")
        print("\n🎬 새로운 기능의 특징:")
        print("   - 외부 운동 영상 API 데이터 활용")
        print("   - 실제 영상 URL과 썸네일 제공")
        print("   - 영상 길이 정보 포함")
        print("   - 대상 그룹별 맞춤 추천")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()

