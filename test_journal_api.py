"""
운동 일지 조회 API 테스트 스크립트
"""

import asyncio
import httpx
from datetime import datetime


async def test_get_daily_log():
    """운동 일지 조회 API 테스트"""
    
    # 테스트 설정
    ai_server_url = "http://localhost:3000"  # AI 서버 주소 (CloudType 포트)
    test_date = "2025-10-08"  # 조회할 날짜
    
    # 실제 사용 시에는 유효한 토큰을 입력해야 합니다
    # 예: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    access_token = "YOUR_ACCESS_TOKEN_HERE"
    
    print("=" * 60)
    print("🧪 운동 일지 조회 API 테스트")
    print("=" * 60)
    print(f"📅 조회 날짜: {test_date}")
    print(f"🔑 토큰: {access_token[:20]}..." if len(access_token) > 20 else f"🔑 토큰: {access_token}")
    print()
    
    # HTTP 헤더 설정
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # 쿼리 파라미터 설정
    params = {
        "date": test_date
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📡 요청 전송 중...")
            print(f"   URL: {ai_server_url}/api/journals/by-date")
            print(f"   Method: GET")
            print(f"   Query: date={test_date}")
            print(f"   Headers: Authorization=Bearer ***")
            print()
            
            response = await client.get(
                f"{ai_server_url}/api/journals/by-date",
                params=params,
                headers=headers
            )
            
            print(f"✅ 응답 수신: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("📊 응답 데이터:")
                print("-" * 60)
                
                if data.get("success"):
                    original_data = data.get("original_data", {})
                    analysis = data.get("analysis", {})
                    
                    print(f"✅ 성공!")
                    print(f"   로그 ID: {original_data.get('logId')}")
                    print(f"   날짜: {original_data.get('date')}")
                    print(f"   메모: {original_data.get('memo')}")
                    print(f"   운동 개수: {len(original_data.get('exercises', []))}")
                    print()
                    
                    # AI 분석 결과 출력
                    if analysis:
                        print("🤖 AI 분석 결과:")
                        print(f"   📋 요약: {analysis.get('summary', 'N/A')}")
                        print()
                        
                        # 통계 정보
                        stats = analysis.get('statistics', {})
                        if stats:
                            print("   📊 통계:")
                            print(f"      - 총 운동 시간: {stats.get('total_time', 0)}분")
                            print(f"      - 운동당 평균 시간: {stats.get('avg_time_per_exercise', 0)}분")
                            
                            # 강도 분포
                            intensity_dist = stats.get('intensity_distribution', {})
                            if intensity_dist:
                                print(f"      - 강도 분포: 상({intensity_dist.get('상', 0)}) 중({intensity_dist.get('중', 0)}) 하({intensity_dist.get('하', 0)})")
                            
                            # 운동 부위
                            body_parts = stats.get('body_parts_trained', {})
                            if body_parts:
                                print(f"      - 운동 부위: {', '.join([f'{part}({count})' for part, count in body_parts.items()])}")
                        print()
                        
                        # 인사이트
                        insights = analysis.get('insights', [])
                        if insights:
                            print("   💡 인사이트:")
                            for insight in insights:
                                print(f"      - {insight}")
                            print()
                        
                        # 추천사항
                        recommendations = analysis.get('recommendations', [])
                        if recommendations:
                            print("   💪 추천사항:")
                            for rec in recommendations:
                                print(f"      - {rec}")
                            print()
                        
                        # 주의사항
                        warnings = analysis.get('warnings', [])
                        if warnings:
                            print("   ⚠️ 주의사항:")
                            for warning in warnings:
                                print(f"      - {warning}")
                            print()
                    
                    # 원본 운동 기록 출력 (간단히)
                    exercises = original_data.get("exercises", [])
                    if exercises:
                        print("💪 운동 기록 (요약):")
                        for idx, exercise in enumerate(exercises, 1):
                            ex_info = exercise.get("exercise", {})
                            print(f"   {idx}. {ex_info.get('title', 'N/A')} ({exercise.get('intensity')}강도, {exercise.get('exerciseTime')}분)")
                    else:
                        print("   운동 기록이 없습니다.")
                else:
                    print(f"❌ 실패: {data.get('error')}")
                    
            elif response.status_code == 404:
                error_data = response.json()
                print(f"❌ 404 Not Found")
                print(f"   {error_data.get('detail', '해당 날짜에 작성된 일지가 없습니다')}")
                
            elif response.status_code == 401:
                error_data = response.json()
                print(f"❌ 401 Unauthorized")
                print(f"   {error_data.get('detail', '인증이 필요합니다')}")
                print(f"   💡 유효한 Access Token을 제공해주세요")
                
            else:
                print(f"❌ 오류 발생: {response.status_code}")
                print(f"   응답: {response.text}")
                
    except httpx.ConnectError:
        print("❌ 연결 오류!")
        print("   AI 서버가 실행 중인지 확인해주세요.")
        print(f"   서버 주소: {ai_server_url}")
        print()
        print("💡 서버 시작 방법:")
        print("   python main.py")
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
    
    print()
    print("=" * 60)


async def test_direct_external_api():
    """외부 API 직접 테스트 (참고용)"""
    
    external_api_url = "http://52.54.123.236/api/journals"
    test_date = "2025-10-08"
    access_token = "YOUR_ACCESS_TOKEN_HERE"
    
    print()
    print("=" * 60)
    print("🌐 외부 API 직접 호출 테스트 (참고용)")
    print("=" * 60)
    print(f"📅 조회 날짜: {test_date}")
    print()
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "date": test_date
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📡 요청 전송 중...")
            print(f"   URL: {external_api_url}/by-date")
            print()
            
            response = await client.get(
                f"{external_api_url}/by-date",
                params=params,
                headers=headers
            )
            
            print(f"✅ 응답 수신: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("📊 응답 데이터 (외부 API 직접):")
                print("-" * 60)
                print(f"   로그 ID: {data.get('logId')}")
                print(f"   날짜: {data.get('date')}")
                print(f"   메모: {data.get('memo')}")
                print(f"   운동 개수: {len(data.get('exercises', []))}")
            else:
                print(f"❌ 오류: {response.status_code}")
                print(f"   응답: {response.text}")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    print("=" * 60)


async def main():
    """메인 테스트 함수"""
    print()
    print("🏋️ ExRecAI - 운동 일지 조회 API 테스트")
    print()
    
    # AI 서버를 통한 테스트
    await test_get_daily_log()
    
    # 직접 외부 API 호출 테스트 (선택사항)
    # await test_direct_external_api()
    
    print()
    print("✅ 테스트 완료!")
    print()
    print("💡 사용 방법:")
    print("   1. test_journal_api.py 파일의 access_token 변수에 유효한 토큰을 입력")
    print("   2. AI 서버를 실행: python main.py")
    print("   3. 테스트 실행: python test_journal_api.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())

