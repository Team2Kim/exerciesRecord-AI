"""
OpenAI 기반 운동 일지 분석 API 테스트
"""

import requests
import json

# 테스트 서버 URL
BASE_URL = "http://localhost:3000"

# 제공받은 로그 데이터
WORKOUT_LOG = {
    "logId": 3,
    "date": "2025-10-08",
    "memo": "근육을 추가한 후",
    "exercises": [
        {
            "logExerciseId": 8,
            "exercise": {
                "exerciseId": 1,
                "title": "팔굽혀펴기",
                "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00351.mp4",
                "description": "유소년 근력/근지구력을 위한 팔/어깨운동 중, 팔굽혀펴기운동을 설명한 운동처방 가이드 동영상",
                "trainingName": "팔 굽혀 펴기(매트)",
                "targetGroup": "유소년",
                "fitnessFactorName": "근력/근지구력",
                "fitnessLevelName": "중급",
                "bodyPart": None,
                "exerciseTool": "매트",
                "videoLengthSeconds": 91,
                "resolution": "1920*1080",
                "fpsCount": 29.96,
                "imageFileName": "0AUDLJ08S_00351_SC_00005.jpeg",
                "imageUrl": "http://openapi.kspo.or.kr/web/image/0AUDLJ08S_00351/",
                "fileSize": 15145209,
                "trainingAimName": None,
                "trainingPlaceName": "실내",
                "trainingSectionName": None,
                "trainingStepName": None,
                "trainingSequenceName": None,
                "trainingWeekName": None,
                "repetitionCountName": "",
                "setCountName": "",
                "operationName": None,
                "jobYmd": "20221010",
                "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"],
                "gookmin100": True
            },
            "intensity": "상",
            "exerciseTime": 0
        },
        {
            "logExerciseId": 9,
            "exercise": {
                "exerciseId": 1,
                "title": "팔굽혀펴기",
                "videoUrl": "http://openapi.kspo.or.kr/web/video/0AUDLJ08S_00351.mp4",
                "description": "유소년 근력/근지구력을 위한 팔/어깨운동 중, 팔굽혀펴기운동을 설명한 운동처방 가이드 동영상",
                "trainingName": "팔 굽혀 펴기(매트)",
                "targetGroup": "유소년",
                "fitnessFactorName": "근력/근지구력",
                "fitnessLevelName": "중급",
                "bodyPart": None,
                "exerciseTool": "매트",
                "videoLengthSeconds": 91,
                "resolution": "1920*1080",
                "fpsCount": 29.96,
                "imageFileName": "0AUDLJ08S_00351_SC_00005.jpeg",
                "imageUrl": "http://openapi.kspo.or.kr/web/image/0AUDLJ08S_00351/",
                "fileSize": 15145209,
                "trainingAimName": None,
                "trainingPlaceName": "실내",
                "trainingSectionName": None,
                "trainingStepName": None,
                "trainingSequenceName": None,
                "trainingWeekName": None,
                "repetitionCountName": "",
                "setCountName": "",
                "operationName": None,
                "jobYmd": "20221010",
                "muscles": ["어깨세모근", "큰가슴근", "위팔세갈래근"],
                "gookmin100": True
            },
            "intensity": "상",
            "exerciseTime": 0
        }
    ]
}


def test_analyze_workout_log():
    """운동 일지 분석 테스트"""
    print("\n" + "="*80)
    print("🧪 OpenAI 기반 운동 일지 분석 테스트")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/workout-log/analyze",
            json=WORKOUT_LOG,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API 응답 성공!")
            print(f"\n📊 날짜: {result.get('date')}")
            print(f"🤖 모델: {result.get('model', 'N/A')}")
            print(f"✅ 성공 여부: {result.get('success')}")
            
            print("\n" + "-"*80)
            print("🤖 AI 분석 결과:")
            print("-"*80)
            if result.get('ai_analysis'):
                print(result.get('ai_analysis'))
            else:
                print("AI 분석 결과가 없습니다.")
            
            print("\n" + "-"*80)
            print("📊 기본 분석 결과:")
            print("-"*80)
            basic_analysis = result.get('basic_analysis', {})
            print(f"요약: {basic_analysis.get('summary', 'N/A')}")
            print(f"총 운동 개수: {basic_analysis.get('statistics', {}).get('total_exercises', 'N/A')}")
            
            # JSON 파일로 저장
            with open("test_result_analyze.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 결과가 'test_result_analyze.json' 파일에 저장되었습니다.")
            
        else:
            print(f"\n❌ API 응답 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")


def test_recommend_workout_routine():
    """운동 루틴 추천 테스트"""
    print("\n" + "="*80)
    print("🧪 OpenAI 기반 운동 루틴 추천 테스트")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/workout-log/recommend",
            json=WORKOUT_LOG,
            params={
                "days": 7,
                "frequency": 4
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API 응답 성공!")
            print(f"🤖 모델: {result.get('model')}")
            print(f"✅ 성공 여부: {result.get('success')}")
            print(f"📅 루틴 기간: {result.get('routine_period', {}).get('days')}일")
            print(f"📊 주간 운동 빈도: {result.get('routine_period', {}).get('frequency')}회")
            
            print("\n" + "-"*80)
            print("🤖 AI 루틴 추천 결과:")
            print("-"*80)
            if result.get('ai_routine'):
                print(result.get('ai_routine'))
            else:
                print("AI 루틴이 생성되지 않았습니다.")
            
            print("\n" + "-"*80)
            print("📊 기본 요약:")
            print("-"*80)
            basic_summary = result.get('basic_summary', {})
            print(f"날짜: {basic_summary.get('date')}")
            print(f"총 운동 개수: {basic_summary.get('total_exercises')}")
            print(f"요약: {basic_summary.get('summary')}")
            
            # JSON 파일로 저장
            with open("test_result_recommend.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 결과가 'test_result_recommend.json' 파일에 저장되었습니다.")
            
        else:
            print(f"\n❌ API 응답 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")


def main():
    """메인 함수"""
    print("\n" + "🚀 OpenAI 기반 운동 일지 분석 및 루틴 추천 API 테스트 시작")
    print("="*80)
    
    # 헬스 체크
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"\n✅ 서버 상태: {health_data.get('status')}")
            print(f"📊 총 운동: {health_data.get('total_exercises')}개")
        else:
            print(f"\n⚠️ 헬스 체크 실패: {health_response.status_code}")
    except Exception as e:
        print(f"\n❌ 서버 연결 실패: {str(e)}")
        print("서버를 먼저 실행해주세요: python main.py")
        return
    
    # OpenAI API 키 확인
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("OpenAI 기능을 사용하려면 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        print("\n계속 진행하시겠습니까? (OpenAI 기능 없이 기본 분석만 수행됩니다)")
        choice = input("계속? (y/n): ")
        if choice.lower() != 'y':
            return
    
    # 테스트 실행
    test_analyze_workout_log()
    print("\n" + "="*80)
    input("계속하려면 Enter를 누르세요...")
    print()
    
    test_recommend_workout_routine()
    print("\n" + "="*80)
    print("✅ 모든 테스트 완료!")
    print("="*80)


if __name__ == "__main__":
    main()

