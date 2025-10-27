"""
배포된 서버 테스트
"""
import requests
import json
from datetime import datetime

# 배포된 서버 URL
BASE_URL = "https://port-0-exerciesrecord-ai-m09uz3m21c03af28.sel4.cloudtype.app"

# 테스트용 운동 일지 데이터
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
            "exerciseTime": 20
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
            "exerciseTime": 20
        }
    ]
}


def test_health_check():
    """서버 헬스 체크"""
    print("\n" + "="*80)
    print("🏥 서버 헬스 체크")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data.get('status')}")
            print(f"📊 총 운동: {data.get('total_exercises')}개")
            print(f"👥 사용자 수: {data.get('total_users')}")
            print(f"⏱️  업타임: {data.get('uptime')}")
            return True
        else:
            print(f"❌ 서버 응답 실패: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        return False


def test_workout_log_analyze():
    """OpenAI 기반 운동 일지 분석 테스트"""
    print("\n" + "="*80)
    print("🤖 OpenAI 기반 운동 일지 분석 테스트")
    print("="*80)
    
    try:
        print(f"\n📤 요청 전송: {BASE_URL}/api/workout-log/analyze")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(
            f"{BASE_URL}/api/workout-log/analyze",
            json=WORKOUT_LOG,
            headers={"Content-Type": "application/json"},
            timeout=30  # OpenAI API 호출 때문에 타임아웃 증가
        )
        
        print(f"\n📥 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API 응답 성공!")
            print(f"\n📊 날짜: {result.get('date')}")
            print(f"🤖 모델: {result.get('model', 'N/A')}")
            print(f"✅ 성공 여부: {result.get('success')}")
            
            print("\n" + "-"*80)
            print("🤖 AI 분석 결과:")
            print("-"*80)
            ai_analysis = result.get('ai_analysis')
            if ai_analysis:
                print(ai_analysis[:500] + "...")  # 처음 500자만 출력
            else:
                print("AI 분석 결과가 없습니다.")
            
            print("\n" + "-"*80)
            print("📊 기본 분석 결과:")
            print("-"*80)
            basic_analysis = result.get('basic_analysis', {})
            print(f"요약: {basic_analysis.get('summary', 'N/A')[:100]}...")
            
            # 결과 저장
            with open("deployed_test_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 결과가 'deployed_test_result.json' 파일에 저장되었습니다.")
            
            return True
        else:
            print(f"\n❌ API 응답 실패: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        return False


def test_workout_log_recommend():
    """운동 루틴 추천 테스트"""
    print("\n" + "="*80)
    print("🏋️ OpenAI 기반 운동 루틴 추천 테스트")
    print("="*80)
    
    try:
        print(f"\n📤 요청 전송: {BASE_URL}/api/workout-log/recommend")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(
            f"{BASE_URL}/api/workout-log/recommend?days=7&frequency=4",
            json=WORKOUT_LOG,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📥 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API 응답 성공!")
            print(f"🤖 모델: {result.get('model')}")
            print(f"✅ 성공 여부: {result.get('success')}")
            print(f"📅 루틴 기간: {result.get('routine_period', {}).get('days')}일")
            
            print("\n" + "-"*80)
            print("🤖 AI 루틴 추천:")
            print("-"*80)
            ai_routine = result.get('ai_routine')
            if ai_routine:
                print(ai_routine[:500] + "...")
            else:
                print("AI 루틴이 생성되지 않았습니다.")
            
            # 결과 저장
            with open("deployed_test_routine.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 결과가 'deployed_test_routine.json' 파일에 저장되었습니다.")
            
            return True
        else:
            print(f"\n❌ API 응답 실패: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        return False


def main():
    """메인 함수"""
    print("\n" + "🚀 배포된 ExRecAI 서버 테스트 시작")
    print("🌐 URL:", BASE_URL)
    print("="*80)
    
    # 1. 헬스 체크
    if not test_health_check():
        print("\n❌ 서버가 응답하지 않습니다. 배포 상태를 확인해주세요.")
        return
    
    # 2. OpenAI 분석 테스트
    input("\n⚡ 엔터를 눌러 OpenAI 기반 운동 일지 분석 테스트를 시작하세요...")
    test_workout_log_analyze()
    
    # 3. 루틴 추천 테스트
    input("\n⚡ 엔터를 눌러 OpenAI 기반 운동 루틴 추천 테스트를 시작하세요...")
    test_workout_log_recommend()
    
    print("\n" + "="*80)
    print("✅ 모든 테스트 완료!")
    print("="*80)


if __name__ == "__main__":
    main()


