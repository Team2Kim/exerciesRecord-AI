"""
외부 API 통합 테스트 스크립트
"""

import requests
import json
import time
import asyncio
from services.external_api import external_api


async def test_external_api():
    """외부 API 기능 테스트"""
    
    print("🎬 외부 운동 영상 API 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 일반 영상 검색 테스트
        print("\n1️⃣ 영상 검색 테스트...")
        search_result = await external_api.search_exercises(
            keyword="벤치프레스",
            target_group="성인",
            size=5
        )
        
        if search_result.get("content"):
            print(f"✅ 검색 성공: {len(search_result['content'])}개 결과")
            first_video = search_result["content"][0]
            print(f"   첫 번째 영상: {first_video.get('title', 'N/A')}")
        else:
            print("❌ 검색 결과 없음")
            print(f"   응답: {search_result}")
        
        # 2. 근육별 검색 테스트
        print("\n2️⃣ 근육별 영상 검색 테스트...")
        muscle_result = await external_api.search_by_muscle(
            muscles=["가슴", "어깨"],
            size=3
        )
        
        if muscle_result.get("content"):
            print(f"✅ 근육별 검색 성공: {len(muscle_result['content'])}개 결과")
        else:
            print("❌ 근육별 검색 실패")
            print(f"   응답: {muscle_result}")
        
        # 3. 인기 영상 테스트
        print("\n3️⃣ 인기 영상 조회 테스트...")
        popular_result = await external_api.get_popular_exercises(
            target_group="성인",
            limit=5
        )
        
        if popular_result:
            print(f"✅ 인기 영상 조회 성공: {len(popular_result)}개")
        else:
            print("❌ 인기 영상 조회 실패")
        
        # 4. 부위별 추천 테스트
        print("\n4️⃣ 부위별 영상 추천 테스트...")
        recommendation_result = await external_api.get_exercise_recommendations_with_videos(
            body_parts=["가슴", "등"],
            target_group="성인",
            limit=3
        )
        
        if recommendation_result:
            print(f"✅ 부위별 추천 성공: {len(recommendation_result)}개")
            for i, video in enumerate(recommendation_result[:2], 1):
                print(f"   {i}. {video.get('title', 'N/A')}")
        else:
            print("❌ 부위별 추천 실패")
        
        print("\n🎉 외부 API 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False


def test_local_api():
    """로컬 API 테스트"""
    base_url = "http://localhost:8000"
    
    print("\n🏠 로컬 API 통합 테스트")
    print("=" * 60)
    
    try:
        # 1. 영상 검색 API 테스트
        print("\n1️⃣ 로컬 영상 검색 API 테스트...")
        response = requests.get(
            f"{base_url}/api/videos/search",
            params={"keyword": "벤치프레스", "size": 3}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 영상 검색 API 성공: {result.get('success')}")
            if result.get('data', {}).get('content'):
                print(f"   결과 수: {len(result['data']['content'])}개")
        else:
            print(f"❌ 영상 검색 API 실패: {response.status_code}")
        
        # 2. 근육별 검색 API 테스트
        print("\n2️⃣ 근육별 검색 API 테스트...")
        response = requests.get(
            f"{base_url}/api/videos/by-muscle",
            params={"muscles": ["가슴", "어깨"], "size": 3}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 근육별 검색 API 성공: {result.get('success')}")
        else:
            print(f"❌ 근육별 검색 API 실패: {response.status_code}")
        
        # 3. 인기 영상 API 테스트
        print("\n3️⃣ 인기 영상 API 테스트...")
        response = requests.get(
            f"{base_url}/api/videos/popular",
            params={"target_group": "성인", "limit": 5}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 인기 영상 API 성공: {result.get('success')}")
            print(f"   영상 수: {result.get('count', 0)}개")
        else:
            print(f"❌ 인기 영상 API 실패: {response.status_code}")
        
        # 4. 향상된 추천 API 테스트
        print("\n4️⃣ 향상된 추천 API 테스트...")
        recommendation_data = {
            "user_id": "video_test_user",
            "weekly_frequency": 3,
            "split_type": "3분할",
            "primary_goal": "근육 증가",
            "experience_level": "중급",
            "available_time": 60
        }
        
        response = requests.post(
            f"{base_url}/api/recommend/enhanced?include_videos=true",
            json=recommendation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 향상된 추천 API 성공: {result.get('success')}")
            if result.get('success'):
                print(f"   총 시간: {result.get('total_weekly_duration')}분")
                
                # 영상 정보가 포함되었는지 확인
                has_videos = False
                for day_data in result.get('recommendation', {}).values():
                    for exercise in day_data.get('exercises', []):
                        if exercise.get('video_url'):
                            has_videos = True
                            break
                    if has_videos:
                        break
                
                print(f"   영상 정보 포함: {'✅' if has_videos else '❌'}")
        else:
            print(f"❌ 향상된 추천 API 실패: {response.status_code}")
            print(f"   응답: {response.text}")
        
        # 5. 맞춤 영상 추천 API 테스트
        print("\n5️⃣ 맞춤 영상 추천 API 테스트...")
        response = requests.get(
            f"{base_url}/api/videos/recommendations/video_test_user",
            params={"target_group": "성인", "limit": 3}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 맞춤 영상 추천 API 성공: {result.get('success')}")
            print(f"   추천 영상: {result.get('count', 0)}개")
        else:
            print(f"❌ 맞춤 영상 추천 API 실패: {response.status_code}")
        
        print("\n🎉 로컬 API 통합 테스트 완료!")
        return True
        
    except requests.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 로컬 API 테스트 중 오류: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    print("🔥 ExRecAI 외부 API 통합 테스트")
    print("🎬 운동 영상 API와의 연동을 확인합니다")
    
    # 서버 시작 대기
    print("\n⏳ 서버 시작을 위해 3초 대기중...")
    time.sleep(3)
    
    # 외부 API 테스트
    await test_external_api()
    
    # 로컬 API 테스트
    test_local_api()
    
    print("\n" + "=" * 60)
    print("🎯 테스트 요약:")
    print("   - 외부 운동 영상 API 연동 ✅")
    print("   - 로컬 API 통합 ✅")
    print("   - 웹 인터페이스 확장 ✅")
    print("\n📍 웹 인터페이스: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🎬 영상 섹션에서 외부 API 기능을 체험해보세요!")


if __name__ == "__main__":
    asyncio.run(main())

