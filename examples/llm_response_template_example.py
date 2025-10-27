"""
LLM 응답 형식 고정 예제
운동 분석 시 고정된 JSON 형식으로 응답을 받는 예제입니다.
"""

import json
from services.openai_service import openai_service

def example_workout_analysis():
    """운동 분석 예제"""
    # 샘플 운동 일지 데이터
    workout_log = {
        "date": "2024-01-15",
        "memo": "오늘 등 운동을 집중적으로 했습니다.",
        "exercises": [
            {
                "exercise": {
                    "title": "덤벨 로우",
                    "muscles": ["등"],
                    "exerciseTool": "덤벨"
                },
                "intensity": "상",
                "exerciseTime": 45
            },
            {
                "exercise": {
                    "title": "풀업",
                    "muscles": ["등", "팔"],
                    "exerciseTool": "철봉"
                },
                "intensity": "상",
                "exerciseTime": 30
            }
        ]
    }
    
    # 운동 분석 실행
    result = openai_service.analyze_workout_log(workout_log)
    
    if result["success"]:
        # JSON 형식의 구조화된 응답
        analysis = result["analysis"]
        
        print("=" * 60)
        print("운동 분석 결과")
        print("=" * 60)
        
        # JSON 응답 전체 출력
        print("\n[전체 JSON 응답]")
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
        
        # 개별 필드 접근
        print("\n[운동 평가]")
        print(analysis.get("workout_evaluation", "N/A"))
        
        print("\n[타겟 근육 분석]")
        print(analysis.get("target_muscles", "N/A"))
        
        print("\n[추천사항]")
        recommendations = analysis.get("recommendations", {})
        print(f"- 다음 운동: {recommendations.get('next_workout', 'N/A')}")
        print(f"- 개선 포인트: {recommendations.get('improvements', 'N/A')}")
        print(f"- 주의사항: {recommendations.get('precautions', 'N/A')}")
        
        print("\n[격려 메시지]")
        print(analysis.get("encouragement", "N/A"))
        
    else:
        print(f"오류 발생: {result['message']}")


def example_workout_routine():
    """운동 루틴 추천 예제"""
    workout_log = {
        "date": "2024-01-15",
        "exercises": [
            {
                "exercise": {
                    "title": "벤치프레스",
                    "muscles": ["가슴", "팔"],
                    "exerciseTool": "바벨"
                },
                "intensity": "상",
                "exerciseTime": 60
            }
        ]
    }
    
    # 7일간 주 4회 루틴 추천
    result = openai_service.recommend_workout_routine(
        workout_log, 
        days=7, 
        frequency=4
    )
    
    if result["success"]:
        routine = result["routine"]
        
        print("=" * 60)
        print("운동 루틴 추천")
        print("=" * 60)
        
        print(f"\n[운동 목표]")
        print(routine.get("workout_goal", "N/A"))
        
        print(f"\n[주간 개요]")
        overview = routine.get("weekly_overview", {})
        for day, description in overview.items():
            print(f"{day}: {description}")
        
        print(f"\n[일별 상세 루틴]")
        daily_routines = routine.get("daily_routines", [])
        for day_plan in daily_routines:
            print(f"\nDay {day_plan.get('day')}: {day_plan.get('target_body_parts')}")
            exercises = day_plan.get("exercises", [])
            for i, exercise in enumerate(exercises, 1):
                print(f"  {i}. {exercise.get('name')}")
                print(f"     세트: {exercise.get('sets')}, 횟수: {exercise.get('reps')}")
                print(f"     휴식: {exercise.get('rest')}")
        
        print(f"\n[팁 및 주의사항]")
        print(routine.get("tips_and_precautions", "N/A"))
    
    else:
        print(f"오류 발생: {result['message']}")


def example_custom_template():
    """커스텀 템플릿 사용 예제"""
    # system message를 직접 수정하여 원하는 형식 지정
    custom_system_message = """당신은 전문 운동 코치입니다. 반드시 다음 JSON 형식으로만 응답하세요:

{
    "summary": "짧은 요약",
    "details": {
        "strength": "강점",
        "weakness": "약점"
    },
    "action_items": [
        "액션 아이템1",
        "액션 아이템2"
    ]
}

위 구조를 따르세요."""
    
    # 실제로는 openai_service 클래스를 상속하거나 
    # 별도의 메서드를 만들어서 사용하면 됩니다.
    print("커스텀 템플릿은 openai_service.py를 수정하여 사용하세요.")


if __name__ == "__main__":
    print("LLM 응답 형식 고정 예제 실행\n")
    
    # 예제 1: 운동 분석
    print("\n[예제 1: 운동 분석]")
    example_workout_analysis()
    
    # 예제 2: 운동 루틴 추천
    print("\n\n[예제 2: 운동 루틴 추천]")
    example_workout_routine()
    
    # 예제 3: 커스텀 템플릿
    print("\n\n[예제 3: 커스텀 템플릿]")
    example_custom_template()
