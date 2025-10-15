"""
ExRecAI API 테스트 스크립트
"""

import requests
import json
import time


def test_api():
    """API 기능 테스트"""
    base_url = "http://localhost:8000"
    
    print("🔥 ExRecAI API 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 서버 상태 확인
        print("\n1️⃣ 서버 상태 확인...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 서버 상태: {health_data['status']}")
            print(f"📊 운동 데이터: {health_data['total_exercises']}개")
            print(f"👥 사용자 수: {health_data['total_users']}명")
        else:
            print(f"❌ 서버 상태 확인 실패: {response.status_code}")
            return False
        
        # 2. 운동 목록 조회
        print("\n2️⃣ 운동 목록 조회...")
        response = requests.get(f"{base_url}/api/exercises?limit=5")
        if response.status_code == 200:
            exercises = response.json()
            print(f"✅ 운동 목록 조회 성공: {len(exercises)}개")
            for i, ex in enumerate(exercises[:3], 1):
                print(f"   {i}. {ex['name']} ({ex['body_part']} - {ex['difficulty']})")
        else:
            print(f"❌ 운동 목록 조회 실패: {response.status_code}")
        
        # 3. 운동 검색
        print("\n3️⃣ 운동 검색 테스트...")
        response = requests.get(f"{base_url}/api/exercises/search?q=벤치프레스")
        if response.status_code == 200:
            search_result = response.json()
            print(f"✅ 검색 결과: {search_result['count']}개")
            if search_result['results']:
                print(f"   첫 번째 결과: {search_result['results'][0]['name']}")
        else:
            print(f"❌ 검색 실패: {response.status_code}")
        
        # 4. 필터 옵션 조회
        print("\n4️⃣ 필터 옵션 조회...")
        response = requests.get(f"{base_url}/api/filters")
        if response.status_code == 200:
            filters = response.json()
            print(f"✅ 운동 부위: {len(filters['body_parts'])}개")
            print(f"✅ 카테고리: {len(filters['categories'])}개")
            print(f"   부위: {', '.join(filters['body_parts'])}")
        else:
            print(f"❌ 필터 조회 실패: {response.status_code}")
        
        # 5. AI 운동 추천 테스트
        print("\n5️⃣ AI 운동 추천 테스트...")
        recommendation_data = {
            "user_id": "test_user_demo",
            "weekly_frequency": 3,
            "split_type": "3분할",
            "primary_goal": "근육 증가",
            "experience_level": "중급",
            "available_time": 60,
            "preferred_equipment": "바벨, 덤벨"
        }
        
        response = requests.post(
            f"{base_url}/api/recommend",
            json=recommendation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            recommendation = response.json()
            if recommendation['success']:
                print(f"✅ 추천 생성 성공!")
                print(f"   총 시간: {recommendation['total_weekly_duration']}분")
                print(f"   난이도: {recommendation['difficulty_score']}/5")
                print(f"   일별 계획: {len(recommendation['recommendation'])}일")
                
                # 첫 번째 날 운동 보기
                first_day = list(recommendation['recommendation'].values())[0]
                print(f"   첫날 운동: {len(first_day['exercises'])}개")
                if first_day['exercises']:
                    print(f"     - {first_day['exercises'][0]['name']}")
            else:
                print(f"❌ 추천 생성 실패: {recommendation['message']}")
        else:
            print(f"❌ 추천 API 오류: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   응답 내용: {response.text}")
        
        # 6. 빠른 추천 테스트
        print("\n6️⃣ 빠른 추천 테스트...")
        response = requests.get(
            f"{base_url}/api/recommend/quick/quick_test_user?goal=체력 향상&frequency=3&time=45&level=초급"
        )
        
        if response.status_code == 200:
            quick_recommendation = response.json()
            if quick_recommendation['success']:
                print(f"✅ 빠른 추천 성공!")
                print(f"   계획 수: {len(quick_recommendation['recommendation'])}일")
            else:
                print(f"❌ 빠른 추천 실패: {quick_recommendation['message']}")
        else:
            print(f"❌ 빠른 추천 API 오류: {response.status_code}")
        
        # 7. 통계 조회
        print("\n7️⃣ 통계 조회 테스트...")
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 통계 조회 성공!")
            print(f"   총 운동: {stats['total_exercises']}개")
            print(f"   총 사용자: {stats['total_users']}명")
            print(f"   부위별 분포: {len(stats['body_part_distribution'])}개 부위")
        else:
            print(f"❌ 통계 조회 실패: {response.status_code}")
        
        print("\n🎉 모든 테스트 완료!")
        print("\n📍 웹 인터페이스: http://localhost:8000")
        print("📚 API 문서: http://localhost:8000/docs")
        
        return True
        
    except requests.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return False
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False


if __name__ == "__main__":
    # 서버 시작 대기
    print("⏳ 서버 시작을 위해 5초 대기중...")
    time.sleep(5)
    
    test_api()

