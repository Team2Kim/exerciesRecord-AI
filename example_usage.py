"""
운동 일지 조회 API 사용 예시

이 파일은 클라이언트에서 AI 서버로 요청을 보내는 다양한 예시를 보여줍니다.
"""

import asyncio
import httpx
from datetime import datetime, timedelta


# ============================================================
# 예시 1: 기본 사용법
# ============================================================

async def example_basic_usage():
    """기본적인 운동 일지 조회 예시"""
    
    print("\n" + "="*60)
    print("예시 1: 기본 사용법")
    print("="*60)
    
    # 설정
    ai_server = "http://localhost:3000"  # CloudType 포트 3000
    access_token = "YOUR_ACCESS_TOKEN"  # 실제 토큰으로 변경 필요
    date = "2025-10-08"
    
    # 요청
    url = f"{ai_server}/api/journals/by-date"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"date": date}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공! 일지 ID: {data['data']['logId']}")
            print(f"   운동 개수: {len(data['data']['exercises'])}")
        else:
            print(f"❌ 실패: {response.status_code}")


# ============================================================
# 예시 2: 여러 날짜의 일지 조회
# ============================================================

async def example_multiple_dates():
    """여러 날짜의 운동 일지를 순차적으로 조회"""
    
    print("\n" + "="*60)
    print("예시 2: 여러 날짜 조회")
    print("="*60)
    
    ai_server = "http://localhost:3000"  # CloudType 포트 3000
    access_token = "YOUR_ACCESS_TOKEN"
    
    # 최근 7일간의 일지 조회
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    async with httpx.AsyncClient() as client:
        for date in dates:
            url = f"{ai_server}/api/journals/by-date"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"date": date}
            
            try:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    exercise_count = len(data['data']['exercises'])
                    print(f"📅 {date}: {exercise_count}개 운동")
                elif response.status_code == 404:
                    print(f"📅 {date}: 일지 없음")
                else:
                    print(f"📅 {date}: 오류 ({response.status_code})")
                    
            except Exception as e:
                print(f"📅 {date}: 에러 - {e}")


# ============================================================
# 예시 3: 응답 데이터 파싱 및 분석
# ============================================================

async def example_parse_and_analyze():
    """응답 데이터를 파싱하여 통계 생성"""
    
    print("\n" + "="*60)
    print("예시 3: 데이터 파싱 및 분석")
    print("="*60)
    
    ai_server = "http://localhost:3000"  # CloudType 포트 3000
    access_token = "YOUR_ACCESS_TOKEN"
    date = "2025-10-08"
    
    url = f"{ai_server}/api/journals/by-date"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"date": date}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()['data']
            exercises = data['exercises']
            
            # 통계 계산
            total_time = sum(ex['exerciseTime'] for ex in exercises)
            body_parts = {}
            intensities = {'상': 0, '중': 0, '하': 0}
            
            for ex in exercises:
                # 신체 부위별 집계
                body_part = ex['exercise']['bodyPart']
                body_parts[body_part] = body_parts.get(body_part, 0) + 1
                
                # 강도별 집계
                intensity = ex['intensity']
                intensities[intensity] = intensities.get(intensity, 0) + 1
            
            # 결과 출력
            print(f"📊 {date} 운동 통계")
            print(f"   총 운동 시간: {total_time}분")
            print(f"   총 운동 개수: {len(exercises)}개")
            print(f"\n   신체 부위별:")
            for part, count in body_parts.items():
                print(f"      - {part}: {count}개")
            print(f"\n   강도별:")
            for intensity, count in intensities.items():
                print(f"      - {intensity}: {count}개")
        else:
            print(f"❌ 조회 실패: {response.status_code}")


# ============================================================
# 예시 4: 에러 처리
# ============================================================

async def example_error_handling():
    """다양한 에러 상황 처리"""
    
    print("\n" + "="*60)
    print("예시 4: 에러 처리")
    print("="*60)
    
    ai_server = "http://localhost:3000"  # CloudType 포트 3000
    access_token = "YOUR_ACCESS_TOKEN"
    date = "2025-10-08"
    
    url = f"{ai_server}/api/journals/by-date"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"date": date}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                print("✅ 성공!")
                data = response.json()
                return data
                
            elif response.status_code == 404:
                print("📭 해당 날짜에 일지가 없습니다")
                print("   💡 다른 날짜를 시도해보세요")
                
            elif response.status_code == 401:
                print("🔒 인증 실패")
                print("   💡 유효한 Access Token을 사용하세요")
                
            else:
                print(f"❌ 예상치 못한 오류: {response.status_code}")
                print(f"   응답: {response.text}")
                
    except httpx.TimeoutException:
        print("⏱️ 요청 시간 초과")
        print("   💡 네트워크 연결을 확인하세요")
        
    except httpx.ConnectError:
        print("🔌 서버 연결 실패")
        print("   💡 AI 서버가 실행 중인지 확인하세요")
        
    except Exception as e:
        print(f"❌ 알 수 없는 오류: {e}")


# ============================================================
# 예시 5: workout_analysis와 연동하여 사용
# ============================================================

async def example_with_analysis():
    """운동 일지 조회 후 분석 API 호출"""
    
    print("\n" + "="*60)
    print("예시 5: 분석 API와 연동")
    print("="*60)
    
    ai_server = "http://localhost:3000"  # CloudType 포트 3000
    access_token = "YOUR_ACCESS_TOKEN"
    user_id = "user123"
    date = "2025-10-08"
    
    async with httpx.AsyncClient() as client:
        # 1. 일지 조회
        print("1️⃣ 운동 일지 조회...")
        journal_response = await client.get(
            f"{ai_server}/api/journals/by-date",
            params={"date": date},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if journal_response.status_code == 200:
            journal_data = journal_response.json()['data']
            print(f"   ✅ 일지 조회 성공: {len(journal_data['exercises'])}개 운동")
            
            # 2. 운동 패턴 분석 조회
            print("\n2️⃣ 운동 패턴 분석 조회...")
            analysis_response = await client.get(
                f"{ai_server}/api/analysis/workout-pattern/{user_id}",
                params={"days": 30}
            )
            
            if analysis_response.status_code == 200:
                analysis_data = analysis_response.json()
                print(f"   ✅ 분석 성공")
                print(f"   총 운동 일수: {analysis_data['total_workouts']}일")
                print(f"   평균 운동 시간: {analysis_data['avg_workout_time']}분")
                
                # 3. 인사이트 조회
                print("\n3️⃣ 맞춤 인사이트 조회...")
                insight_response = await client.get(
                    f"{ai_server}/api/analysis/insights/{user_id}",
                    params={"days": 30}
                )
                
                if insight_response.status_code == 200:
                    insight_data = insight_response.json()
                    print(f"   ✅ 인사이트 생성 완료")
                    print(f"   균형 점수: {insight_data['balance_score']}/100")
                    print(f"   추천사항:")
                    for rec in insight_data['recommendations']:
                        print(f"      - {rec}")
        else:
            print(f"   ❌ 일지 조회 실패: {journal_response.status_code}")


# ============================================================
# 예시 6: 클라이언트 헬퍼 클래스
# ============================================================

class JournalAPIClient:
    """운동 일지 API 클라이언트 헬퍼 클래스"""
    
    def __init__(self, ai_server_url: str, access_token: str):
        self.ai_server_url = ai_server_url
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    async def get_daily_log(self, date: str):
        """특정 날짜의 일지 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.ai_server_url}/api/journals/by-date",
                params={"date": date},
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
    
    async def get_logs_between(self, start_date: str, end_date: str):
        """기간 내 모든 일지 조회"""
        logs = []
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            log = await self.get_daily_log(date_str)
            if log:
                logs.append(log)
            current += timedelta(days=1)
        
        return logs


async def example_client_class():
    """헬퍼 클래스 사용 예시"""
    
    print("\n" + "="*60)
    print("예시 6: 클라이언트 헬퍼 클래스 사용")
    print("="*60)
    
    # 클라이언트 초기화
    client = JournalAPIClient(
        ai_server_url="http://localhost:3000",  # CloudType 포트 3000
        access_token="YOUR_ACCESS_TOKEN"
    )
    
    # 특정 날짜 조회
    log = await client.get_daily_log("2025-10-08")
    if log:
        print(f"✅ 일지 조회 성공")
        print(f"   운동 개수: {len(log['data']['exercises'])}")
    else:
        print("📭 일지가 없습니다")
    
    # 기간 조회
    print("\n기간 내 일지 조회 (최근 7일)...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    logs = await client.get_logs_between(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    print(f"✅ {len(logs)}개의 일지를 찾았습니다")


# ============================================================
# 메인 실행
# ============================================================

async def main():
    """모든 예시 실행"""
    
    print("\n" + "="*60)
    print("🏋️ 운동 일지 조회 API 사용 예시")
    print("="*60)
    print("\n⚠️  주의: 실제 테스트를 위해서는 다음을 수정해야 합니다:")
    print("   1. access_token을 유효한 토큰으로 변경")
    print("   2. date를 실제 일지가 있는 날짜로 변경")
    print("   3. AI 서버가 실행 중이어야 함 (python main.py)")
    
    # 원하는 예시를 선택하여 실행
    # await example_basic_usage()
    # await example_multiple_dates()
    # await example_parse_and_analyze()
    # await example_error_handling()
    # await example_with_analysis()
    # await example_client_class()
    
    print("\n💡 각 예시를 실행하려면 해당 함수의 주석을 해제하세요")
    print("   예: await example_basic_usage()")
    print()


if __name__ == "__main__":
    asyncio.run(main())

