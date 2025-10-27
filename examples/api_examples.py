"""
ExRecAI API 사용 예시

이 파일은 ExRecAI API를 사용하는 다양한 예시를 제공합니다.
"""

import requests
import json
from typing import Dict, Any

# 배포된 서버 URL
BASE_URL = "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app"


# ==================== 예시 1: 운동 일지 AI 분석 ====================

def analyze_workout_log_example():
    """운동 일지 AI 분석 예시"""
    
    # 운동 일지 데이터
    workout_log = {
        "logId": 3,
        "date": "2025-10-08",
        "memo": "오늘은 고강도로 팔굽혀펴기를 했습니다",
        "exercises": [
            {
                "logExerciseId": 8,
                "exercise": {
                    "exerciseId": 1,
                    "title": "팔굽혀펴기",
                    "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"],
                    "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00351.mp4",
                    "trainingName": "팔 굽혀 펴기(매트)",
                    "exerciseTool": "매트",
                    "trainingPlaceName": "실내"
                },
                "intensity": "상",
                "exerciseTime": 20
            },
            {
                "logExerciseId": 9,
                "exercise": {
                    "exerciseId": 2,
                    "title": "스쿼트",
                    "muscles": ["넙다리네갈래근", "둔근"],
                    "exerciseTool": "맨몸",
                    "trainingPlaceName": "실내"
                },
                "intensity": "중",
                "exerciseTime": 15
            }
        ]
    }
    
    # API 호출
    response = requests.post(
        f"{BASE_URL}/api/workout-log/analyze?model=gpt-4o-mini",
        json=workout_log,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 운동 일지 분석 성공!")
        print(f"AI 분석 결과:\n{result['ai_analysis'][:200]}...")
        print(f"\n기본 통계: {result['basic_analysis']['summary']}")
        return result
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        print(response.text)
        return None


# ==================== 예시 2: 운동 루틴 AI 추천 ====================

def recommend_workout_routine_example():
    """운동 루틴 AI 추천 예시"""
    
    # 최근 운동 기록
    recent_workout = {
        "date": "2025-10-08",
        "exercises": [
            {
                "exercise": {
                    "title": "팔굽혀펴기",
                    "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"]
                },
                "intensity": "상",
                "exerciseTime": 20
            }
        ]
    }
    
    # API 호출
    response = requests.post(
        f"{BASE_URL}/api/workout-log/recommend",
        json=recent_workout,
        params={
            "days": 7,      # 7일간 루틴
            "frequency": 4,  # 주 4회
            "model": "gpt-4o-mini"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 운동 루틴 추천 성공!")
        print(f"루틴 기간: {result['routine_period']['days']}일")
        print(f"주간 빈도: {result['routine_period']['frequency']}회")
        print(f"\nAI 루틴:\n{result['ai_routine'][:300]}...")
        return result
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        print(response.text)
        return None


# ==================== 예시 3: 서버 헬스 체크 ====================

def health_check_example():
    """서버 헬스 체크 예시"""
    
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 서버 상태:", data['status'])
        print(f"📊 총 운동: {data['total_exercises']}개")
        print(f"👥 사용자 수: {data['total_users']}")
        print(f"⏱️  업타임: {data['uptime']}")
        return data
    else:
        print(f"❌ 서버 오류: {response.status_code}")
        return None


# ==================== 예시 4: 운동 목록 조회 ====================

def get_exercises_example():
    """운동 목록 조회 예시"""
    
    # 기본 조회
    response = requests.get(
        f"{BASE_URL}/api/exercises",
        params={
            "skip": 0,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        exercises = response.json()
        print(f"✅ 운동 목록 조회 성공! ({len(exercises)}개)")
        
        for i, exercise in enumerate(exercises[:3], 1):
            print(f"{i}. {exercise['name']} ({exercise['body_part']})")
        
        return exercises
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        return None


# ==================== 예시 5: 운동 검색 ====================

def search_exercises_example():
    """운동 검색 예시"""
    
    response = requests.get(
        f"{BASE_URL}/api/exercises/search",
        params={
            "q": "벤치",
            "limit": 5
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 검색 결과: '{result['query']}' ({result['count']}개)")
        
        for exercise in result['results'][:3]:
            print(f"- {exercise['name']}")
        
        return result
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        return None


# ==================== 예시 6: 운동 영상 검색 ====================

def search_videos_example():
    """운동 영상 검색 예시"""
    
    response = requests.get(
        f"{BASE_URL}/api/videos/search",
        params={
            "keyword": "벤치프레스",
            "target_group": "성인",
            "size": 5
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            videos = result['data']
            print(f"✅ 영상 검색 성공! ({len(videos)}개)")
            
            for i, video in enumerate(videos[:3], 1):
                print(f"{i}. {video.get('title', 'N/A')}")
        
        return result
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        return None


# ==================== 메인 실행 함수 ====================

def main():
    """모든 예시 실행"""
    
    print("=" * 80)
    print("🚀 ExRecAI API 사용 예시")
    print("=" * 80)
    
    examples = [
        ("1. 헬스 체크", health_check_example),
        ("2. 운동 목록 조회", get_exercises_example),
        ("3. 운동 검색", search_exercises_example),
        ("4. 영상 검색", search_videos_example),
        ("5. 운동 일지 AI 분석", analyze_workout_log_example),
        ("6. 운동 루틴 AI 추천", recommend_workout_routine_example),
    ]
    
    for name, func in examples:
        print(f"\n{'='*80}")
        print(f"📝 {name}")
        print('='*80)
        try:
            func()
        except Exception as e:
            print(f"❌ 실행 중 오류: {str(e)}")
        
        print("\n" + "─" * 80)
        input("다음 예시를 보려면 Enter를 누르세요...")
    
    print("\n" + "=" * 80)
    print("✅ 모든 예시 완료!")
    print("=" * 80)


if __name__ == "__main__":
    # 개별 함수 실행하려면 주석 해제
    # health_check_example()
    # analyze_workout_log_example()
    # recommend_workout_routine_example()
    
    # 모든 예시 실행
    main()


