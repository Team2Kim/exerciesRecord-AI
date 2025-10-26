"""
ExRecAI - 운동 추천 AI 시스템
FastAPI 메인 서버 애플리케이션
"""

import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, Header, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로컬 모듈 임포트
from models.database import get_db, create_tables, SessionLocal
from models.schemas import (
    Exercise, ExerciseCreate, UserGoal, UserGoalCreate,
    RecommendationRequest, RecommendationResponse,
    UserFeedbackCreate, UserFeedback, HealthStatus,
    ComprehensiveAnalysis, WorkoutPatternAnalysis, WorkoutInsight
)
from services.recommendation import ExerciseRecommendationService
from services.database_service import DatabaseService
from services.external_api import external_api
from services.external_recommendation import external_recommendation_service
from services.workout_analysis import WorkoutAnalysisService
from services.openai_service import openai_service


# FastAPI 앱 초기화
app = FastAPI(
    title="ExRecAI - 운동 추천 AI 시스템",
    description="사용자 목표 기반 개인화 운동 추천 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 실제 배포시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 서버 시작 시간 기록
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """서버 시작시 실행될 함수"""
    print("🚀 ExRecAI 서버가 시작되었습니다!")
    print("📊 데이터베이스 테이블을 확인합니다...")
    
    # 테이블 생성 (없을 경우에만)
    create_tables()
    print("✅ 데이터베이스 준비 완료!")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료시 실행될 함수"""
    print("👋 ExRecAI 서버가 종료되었습니다!")


# ==================== 메인 페이지 ====================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """메인 페이지"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ExRecAI - 운동 추천 AI</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #2E8B57; }
                .api-link { margin: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>🏋️ ExRecAI - 운동 추천 AI 시스템</h1>
            <p>개인 맞춤형 운동 추천 서비스에 오신 것을 환영합니다!</p>
            <div class="api-link">
                <h3>📚 API 문서</h3>
                <p><a href="/docs" target="_blank">Swagger UI</a> | <a href="/redoc" target="_blank">ReDoc</a></p>
            </div>
            <div class="api-link">
                <h3>🎯 주요 기능</h3>
                <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                    <li>개인 목표 기반 운동 추천</li>
                    <li>분할 방식별 운동 계획 생성</li>
                    <li>운동 데이터베이스 관리</li>
                    <li>사용자 피드백 시스템</li>
                </ul>
            </div>
        </body>
        </html>
        """)


# ==================== 상태 확인 ====================

@app.get("/health", response_model=HealthStatus)
async def health_check(db: Session = Depends(get_db)):
    """시스템 상태 확인"""
    try:
        db_service = DatabaseService(db)
        stats = db_service.get_database_stats()
        
        uptime_seconds = int(time.time() - start_time)
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        return HealthStatus(
            status="healthy",
            database_connected=True,
            total_exercises=stats['total_exercises'],
            total_users=stats['total_users'],
            version="1.0.0",
            uptime=f"{uptime_hours}시간 {uptime_minutes}분"
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            database_connected=False,
            total_exercises=0,
            total_users=0,
            version="1.0.0",
            uptime="N/A"
        )


# ==================== 운동 관련 API ====================

@app.get("/api/exercises", response_model=List[Exercise])
async def get_exercises(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=100, description="가져올 항목 수"),
    body_part: Optional[str] = Query(None, description="운동 부위 필터"),
    category: Optional[str] = Query(None, description="운동 카테고리 필터"),
    difficulty: Optional[str] = Query(None, description="난이도 필터"),
    target_goal: Optional[str] = Query(None, description="목표 필터"),
    db: Session = Depends(get_db)
):
    """운동 목록 조회"""
    db_service = DatabaseService(db)
    exercises = db_service.get_exercises(
        skip=skip, limit=limit, body_part=body_part,
        category=category, difficulty=difficulty, target_goal=target_goal
    )
    return exercises


@app.get("/api/exercises/search")
async def search_exercises(
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, ge=1, le=50, description="결과 수 제한"),
    db: Session = Depends(get_db)
):
    """운동 검색"""
    db_service = DatabaseService(db)
    exercises = db_service.search_exercises(q, limit)
    return {"query": q, "results": exercises, "count": len(exercises)}


@app.get("/api/exercises/{exercise_id}", response_model=Exercise)
async def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """특정 운동 조회"""
    db_service = DatabaseService(db)
    exercise = db_service.get_exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="운동을 찾을 수 없습니다")
    return exercise


@app.get("/api/exercises/{exercise_id}/feedback")
async def get_exercise_feedback(exercise_id: int, db: Session = Depends(get_db)):
    """운동별 피드백 요약"""
    db_service = DatabaseService(db)
    
    # 운동 존재 확인
    exercise = db_service.get_exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="운동을 찾을 수 없습니다")
    
    feedback_summary = db_service.get_exercise_feedback_summary(exercise_id)
    return {
        "exercise_id": exercise_id,
        "exercise_name": exercise.name,
        **feedback_summary
    }


@app.get("/api/exercises/popular")
async def get_popular_exercises(
    limit: int = Query(10, ge=1, le=20, description="결과 수"),
    db: Session = Depends(get_db)
):
    """인기 운동 조회"""
    db_service = DatabaseService(db)
    popular_exercises = db_service.get_popular_exercises(limit)
    return {"popular_exercises": popular_exercises}


@app.post("/api/exercises", response_model=Exercise, status_code=status.HTTP_201_CREATED)
async def create_exercise(exercise_data: ExerciseCreate, db: Session = Depends(get_db)):
    """새 운동 생성 (관리자용)"""
    db_service = DatabaseService(db)
    return db_service.create_exercise(exercise_data)


# ==================== 사용자 목표 관련 API ====================

@app.post("/api/user-goals", response_model=UserGoal, status_code=status.HTTP_201_CREATED)
async def create_user_goal(goal_data: UserGoalCreate, db: Session = Depends(get_db)):
    """사용자 목표 생성"""
    db_service = DatabaseService(db)
    return db_service.create_user_goal(goal_data)


@app.get("/api/user-goals/{user_id}", response_model=UserGoal)
async def get_user_goal(user_id: str, db: Session = Depends(get_db)):
    """사용자 목표 조회"""
    db_service = DatabaseService(db)
    goal = db_service.get_user_goal(user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="사용자 목표를 찾을 수 없습니다")
    return goal


@app.get("/api/user-goals/{user_id}/history")
async def get_user_goal_history(user_id: str, db: Session = Depends(get_db)):
    """사용자 목표 히스토리"""
    db_service = DatabaseService(db)
    goals = db_service.get_user_goals_history(user_id)
    return {"user_id": user_id, "goals": goals, "count": len(goals)}


# ==================== 추천 시스템 API ====================

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend_exercises(
    request: RecommendationRequest,
    save_as_plan: bool = Query(False, description="운동 계획으로 저장 여부"),
    db: Session = Depends(get_db)
):
    """운동 추천 생성"""
    try:
        # 추천 서비스 초기화
        recommendation_service = ExerciseRecommendationService(db)
        
        # 추천 생성
        recommendation = recommendation_service.generate_recommendation(request)
        
        # 계획으로 저장 요청시 처리
        if save_as_plan and recommendation.success:
            db_service = DatabaseService(db)
            
            # 사용자 목표가 없으면 생성
            user_goal = db_service.get_user_goal(request.user_id)
            if not user_goal:
                goal_data = UserGoalCreate(
                    user_id=request.user_id,
                    weekly_frequency=request.weekly_frequency,
                    split_type=request.split_type,
                    primary_goal=request.primary_goal,
                    experience_level=request.experience_level,
                    available_time=request.available_time,
                    preferred_equipment=request.preferred_equipment
                )
                user_goal = db_service.create_user_goal(goal_data)
            
            # 운동 계획으로 저장
            plan = db_service.save_recommendation_as_plan(
                request.user_id,
                recommendation.dict(),
                f"AI 추천 ({datetime.now().strftime('%Y-%m-%d')})"
            )
            
            if plan:
                recommendation.message += f" 운동 계획 ID {plan.id}로 저장되었습니다."
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"추천 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/recommend/external", response_model=RecommendationResponse)
async def recommend_with_external_api(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """외부 API 데이터 기반 운동 추천 (메인 기능)"""
    try:
        # 외부 API 기반 추천 생성
        recommendation = await external_recommendation_service.generate_external_recommendation(request)
        
        # 사용자 목표가 없으면 생성 (추천 기록용)
        if recommendation.success:
            db_service = DatabaseService(db)
            user_goal = db_service.get_user_goal(request.user_id)
            if not user_goal:
                goal_data = UserGoalCreate(
                    user_id=request.user_id,
                    weekly_frequency=request.weekly_frequency,
                    split_type=request.split_type,
                    primary_goal=request.primary_goal,
                    experience_level=request.experience_level,
                    available_time=request.available_time,
                    preferred_equipment=request.preferred_equipment
                )
                db_service.create_user_goal(goal_data)
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"외부 API 기반 추천 생성 중 오류: {str(e)}"
        )


@app.get("/api/recommend/quick/{user_id}")
async def quick_recommend(
    user_id: str,
    goal: str = Query("체력 향상", description="운동 목표"),
    frequency: int = Query(3, ge=1, le=7, description="주간 빈도"),
    time: int = Query(45, ge=15, le=180, description="1회 운동 시간"),
    level: str = Query("초급", description="경험 수준"),
    db: Session = Depends(get_db)
):
    """빠른 추천 (간단한 파라미터)"""
    
    # 빠른 추천 요청 객체 생성
    quick_request = RecommendationRequest(
        user_id=user_id,
        weekly_frequency=frequency,
        split_type="전신" if frequency <= 3 else "3분할",
        primary_goal=goal,
        experience_level=level,
        available_time=time
    )
    
    # 추천 생성
    recommendation_service = ExerciseRecommendationService(db)
    recommendation = recommendation_service.generate_recommendation(quick_request)
    
    return recommendation


# ==================== 피드백 관련 API ====================

@app.post("/api/feedback", response_model=UserFeedback, status_code=status.HTTP_201_CREATED)
async def create_feedback(feedback_data: UserFeedbackCreate, db: Session = Depends(get_db)):
    """사용자 피드백 생성"""
    db_service = DatabaseService(db)
    
    # 운동 존재 확인
    exercise = db_service.get_exercise_by_id(feedback_data.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="운동을 찾을 수 없습니다")
    
    return db_service.create_feedback(feedback_data)


@app.get("/api/feedback/{user_id}")
async def get_user_feedback(
    user_id: str,
    exercise_id: Optional[int] = Query(None, description="특정 운동 피드백만 조회"),
    db: Session = Depends(get_db)
):
    """사용자 피드백 조회"""
    db_service = DatabaseService(db)
    feedback_list = db_service.get_user_feedback(user_id, exercise_id)
    return {
        "user_id": user_id,
        "exercise_id": exercise_id,
        "feedback": feedback_list,
        "count": len(feedback_list)
    }


# ==================== 운동 계획 관련 API ====================

@app.get("/api/workout-plans/{user_id}")
async def get_user_workout_plans(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="조회할 계획 수"),
    db: Session = Depends(get_db)
):
    """사용자 운동 계획 목록"""
    db_service = DatabaseService(db)
    plans = db_service.get_workout_plans(user_id, limit)
    return {
        "user_id": user_id,
        "plans": plans,
        "count": len(plans)
    }


@app.get("/api/workout-plans/detail/{plan_id}")
async def get_workout_plan_detail(plan_id: int, db: Session = Depends(get_db)):
    """운동 계획 상세 정보"""
    db_service = DatabaseService(db)
    plan = db_service.get_workout_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="운동 계획을 찾을 수 없습니다")
    return plan


# ==================== 통계 및 분석 API ====================

@app.get("/api/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """전체 통계 조회"""
    db_service = DatabaseService(db)
    return db_service.get_database_stats()


@app.get("/api/analytics/{user_id}")
async def get_user_analytics(user_id: str, db: Session = Depends(get_db)):
    """사용자 분석 데이터"""
    db_service = DatabaseService(db)
    analytics = db_service.get_user_analytics(user_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="사용자 데이터를 찾을 수 없습니다")
    return analytics


# ==================== 유틸리티 API ====================

@app.get("/api/filters")
async def get_filter_options(db: Session = Depends(get_db)):
    """필터링 옵션 조회"""
    from models.database import Exercise
    # 운동 데이터에서 고유값들 추출
    exercises = db.query(Exercise).all()
    
    body_parts = sorted(list(set(ex.body_part for ex in exercises)))
    categories = sorted(list(set(ex.category for ex in exercises)))
    difficulties = sorted(list(set(ex.difficulty for ex in exercises)))
    target_goals = sorted(list(set(ex.target_goal for ex in exercises)))
    
    return {
        "body_parts": body_parts,
        "categories": categories,
        "difficulties": difficulties,
        "target_goals": target_goals,
        "split_types": ["2분할", "3분할", "전신"],
        "experience_levels": ["초급", "중급", "고급"]
    }


# ==================== 외부 운동 영상 API ====================

@app.get("/api/videos/search")
async def search_exercise_videos(
    keyword: Optional[str] = Query(None, description="제목 검색어"),
    target_group: Optional[str] = Query(None, description="대상 그룹"),
    fitness_factor_name: Optional[str] = Query(None, description="체력 요인"),
    exercise_tool: Optional[str] = Query(None, description="운동 도구"),
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=50, description="페이지 크기")
):
    """외부 API를 통한 운동 영상 검색"""
    try:
        result = await external_api.search_exercises(
            keyword=keyword,
            target_group=target_group,
            fitness_factor_name=fitness_factor_name,
            exercise_tool=exercise_tool,
            page=page,
            size=size
        )
        
        return {
            "success": True,
            "data": result,
            "source": "external_api"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 검색 중 오류: {str(e)}")


@app.get("/api/videos/by-muscle")
async def search_videos_by_muscle(
    muscles: List[str] = Query(..., description="검색할 근육 목록"),
    page: int = Query(0, ge=0, description="페이지 번호"),
    size: int = Query(10, ge=1, le=50, description="페이지 크기")
):
    """근육 부위별 운동 영상 검색"""
    try:
        result = await external_api.search_by_muscle(
            muscles=muscles,
            page=page,
            size=size
        )
        
        return {
            "success": True,
            "data": result,
            "source": "external_api"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"근육별 영상 검색 중 오류: {str(e)}")


@app.get("/api/videos/popular")
async def get_popular_videos(
    target_group: str = Query("성인", description="대상 그룹"),
    limit: int = Query(10, ge=1, le=30, description="최대 개수")
):
    """인기 운동 영상 조회"""
    try:
        result = await external_api.get_popular_exercises(
            target_group=target_group,
            limit=limit
        )
        
        return {
            "success": True,
            "videos": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인기 영상 조회 중 오류: {str(e)}")


@app.post("/api/recommend/enhanced", response_model=RecommendationResponse)
async def recommend_exercises_with_videos(
    request: RecommendationRequest,
    include_videos: bool = Query(True, description="영상 정보 포함 여부"),
    db: Session = Depends(get_db)
):
    """영상 정보가 포함된 운동 추천"""
    try:
        # 기본 추천 생성
        recommendation_service = ExerciseRecommendationService(db)
        recommendation = recommendation_service.generate_recommendation(request)
        
        if not recommendation.success:
            return recommendation
        
        # 영상 정보 추가
        if include_videos:
            enhanced_recommendation_dict = recommendation.dict()
            enhanced_result = await external_api.enhance_recommendation_with_videos(
                enhanced_recommendation_dict
            )
            
            # Pydantic 모델로 다시 변환
            recommendation = RecommendationResponse(**enhanced_result)
            recommendation.message += " (운동 영상 정보 포함)"
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"향상된 추천 생성 중 오류: {str(e)}"
        )


@app.get("/api/videos/recommendations/{user_id}")
async def get_video_recommendations_for_user(
    user_id: str,
    target_group: str = Query("성인", description="대상 그룹"),
    exercise_tool: Optional[str] = Query(None, description="선호 운동 도구"),
    limit: int = Query(5, ge=1, le=20, description="최대 추천 개수"),
    db: Session = Depends(get_db)
):
    """사용자 맞춤 운동 영상 추천"""
    try:
        # 사용자 목표 조회
        db_service = DatabaseService(db)
        user_goal = db_service.get_user_goal(user_id)
        
        if not user_goal:
            # 기본 추천
            body_parts = ["가슴", "등", "하체"]
        else:
            # 분할 방식에 따른 부위 결정
            split_mapping = {
                "2분할": ["상체", "하체"],
                "3분할": ["가슴", "등", "하체"],
                "전신": ["가슴", "등", "하체", "어깨", "팔"]
            }
            body_parts = split_mapping.get(user_goal.split_type, ["가슴", "등", "하체"])
        
        # 외부 API로 영상 추천
        video_recommendations = await external_api.get_exercise_recommendations_with_videos(
            body_parts=body_parts,
            target_group=target_group,
            exercise_tool=exercise_tool or (user_goal.preferred_equipment if user_goal else None),
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": video_recommendations,
            "count": len(video_recommendations),
            "target_body_parts": body_parts
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용자 맞춤 영상 추천 중 오류: {str(e)}"
        )


@app.post("/api/videos/cache/clear")
async def clear_video_cache():
    """영상 API 캐시 초기화 (관리자용)"""
    try:
        external_api.clear_cache()
        return {"success": True, "message": "영상 API 캐시가 초기화되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐시 초기화 중 오류: {str(e)}")


# ==================== 개발용 API ====================

@app.post("/api/dev/reset-db")
async def reset_database():
    """개발용: 데이터베이스 초기화"""
    try:
        # 위험한 작업이므로 개발 환경에서만 사용
        if os.getenv("ENVIRONMENT") != "development":
            raise HTTPException(status_code=403, detail="개발 환경에서만 사용 가능합니다")
        
        # 테이블 재생성 (주의: 모든 데이터 삭제됨)
        from models.database import Base, engine
        Base.metadata.drop_all(bind=engine)
        create_tables()
        
        return {"message": "데이터베이스가 초기화되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"초기화 중 오류: {str(e)}")


# ==================== 운동 일지 분석 API ====================

async def analyze_daily_workout(workout_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    외부 API에서 받은 운동 일지 데이터를 분석합니다.
    
    Args:
        workout_data: 외부 API에서 받은 운동 일지 데이터
        
    Returns:
        분석 결과 (운동 패턴, 강도 분석, 추천사항 등)
    """
    try:
        exercises = workout_data.get("exercises", [])
        
        if not exercises:
            return {
                "summary": "운동 기록이 없습니다.",
                "total_exercises": 0,
                "total_time": 0,
                "recommendations": ["운동을 시작해보세요!"]
            }
        
        # 기본 통계 계산
        total_exercises = len(exercises)
        total_time = sum(ex.get("exerciseTime", 0) for ex in exercises)
        avg_time_per_exercise = total_time / total_exercises if total_exercises > 0 else 0
        
        # 강도 분석
        intensity_dist = {"상": 0, "중": 0, "하": 0}
        for ex in exercises:
            intensity = ex.get("intensity", "중")
            if intensity in intensity_dist:
                intensity_dist[intensity] += 1
        
        # 운동 부위 분석 (운동 이름과 설명을 기반으로 부위 추출)
        body_parts = {}
        exercise_tools = {}
        muscles = set()
        
        def extract_body_part_from_exercise(exercise_info):
            """운동 이름과 설명에서 신체 부위를 추출"""
            title = exercise_info.get("title", "").lower()
            description = exercise_info.get("description", "").lower()
            training_name = exercise_info.get("trainingName", "").lower()
            
            # 하체 관련 키워드
            lower_body_keywords = ["다리", "하체", "스쿼트", "앉아서", "일어서기", "밀기", "펴기", "넙다리", "대퇴", "허벅지", "종아리", "발목"]
            # 상체 관련 키워드
            upper_body_keywords = ["가슴", "어깨", "팔", "등", "코어", "복부", "벤치", "프레스", "풀업", "덤벨", "로우"]
            
            # 하체 확인
            for keyword in lower_body_keywords:
                if keyword in title or keyword in description or keyword in training_name:
                    return "하체"
            
            # 상체 확인
            for keyword in upper_body_keywords:
                if keyword in title or keyword in description or keyword in training_name:
                    return "상체"
            
            # 기본값
            return "전신"
        
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            
            # 운동 부위 추출 (운동 이름 기반)
            body_part = exercise_info.get("bodyPart")
            if not body_part:
                body_part = extract_body_part_from_exercise(exercise_info)
            body_parts[body_part] = body_parts.get(body_part, 0) + 1
            
            # 운동 도구 (원본 그대로)
            tool = exercise_info.get("exerciseTool", "기타")
            exercise_tools[tool] = exercise_tools.get(tool, 0) + 1
            
            # 근육 부위
            ex_muscles = exercise_info.get("muscles", [])
            for muscle in ex_muscles:
                muscles.add(muscle)
        
        # 가장 많이 한 운동
        most_frequent_body_part = max(body_parts.items(), key=lambda x: x[1]) if body_parts else ("없음", 0)
        most_used_tool = max(exercise_tools.items(), key=lambda x: x[1]) if exercise_tools else ("없음", 0)
        
        # 강도별 비율 계산
        total_intensity = sum(intensity_dist.values())
        intensity_percentage = {}
        for intensity, count in intensity_dist.items():
            intensity_percentage[intensity] = round((count / total_intensity * 100), 1) if total_intensity > 0 else 0
        
        # 상세 AI 분석 및 추천사항 생성
        recommendations = []
        warnings = []
        insights = []
        
        # 1. 강도 분석 (더 세분화)
        high_intensity_ratio = intensity_percentage.get("상", 0)
        medium_intensity_ratio = intensity_percentage.get("중", 0)
        low_intensity_ratio = intensity_percentage.get("하", 0)
        
        if high_intensity_ratio > 70:
            warnings.append(f"고강도 운동이 {high_intensity_ratio}%로 매우 높습니다. 근육 회복을 위해 충분한 휴식을 취하고 단백질 섭취를 늘리세요.")
            recommendations.append("다음 운동은 중강도로 조절하여 과부하를 방지하세요.")
        elif high_intensity_ratio > 50:
            warnings.append(f"고강도 운동이 {high_intensity_ratio}%로 높습니다. 운동 후 스트레칭과 충분한 수면을 취하세요.")
        elif low_intensity_ratio > 70:
            recommendations.append(f"저강도 운동이 {low_intensity_ratio}%로 높습니다. 점진적으로 운동 강도를 높여 체력 향상을 도모하세요.")
        elif medium_intensity_ratio > 60:
            insights.append(f"중강도 운동 비율이 {medium_intensity_ratio}%로 적절한 강도 조절을 하고 있습니다.")
        
        # 2. 운동 시간 분석 (더 구체적)
        if avg_time_per_exercise > 45:
            insights.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 매우 충분한 시간을 투자하고 있습니다. 집중력과 자세 유지가 우수합니다.")
        elif avg_time_per_exercise > 30:
            insights.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 적절한 운동 시간입니다.")
        elif avg_time_per_exercise > 15:
            recommendations.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 조금 짧습니다. 각 세트 간 휴식을 줄이고 운동 시간을 20-30분으로 늘려보세요.")
        else:
            warnings.append(f"운동당 평균 {avg_time_per_exercise:.1f}분으로 너무 짧습니다. 운동 효과를 높이기 위해 시간을 늘리는 것을 권장합니다.")
        
        # 3. 운동 다양성 및 균형 분석
        body_part_count = len(body_parts)
        if body_part_count == 1:
            main_part = list(body_parts.keys())[0]
            warnings.append(f"오늘은 {main_part}만 집중적으로 운동했습니다. 근육 불균형을 방지하기 위해 다음 운동에서는 다른 부위도 포함하세요.")
            recommendations.append(f"상체 운동을 추가하여 전신 균형을 맞춰보세요.")
        elif body_part_count == 2:
            parts = list(body_parts.keys())
            insights.append(f"{parts[0]}와 {parts[1]} 부위를 균형있게 운동했습니다.")
        elif body_part_count >= 3:
            insights.append(f"{body_part_count}개 부위를 종합적으로 운동하여 전신 균형이 우수합니다.")
        
        # 4. 운동 도구 다양성 분석
        tool_count = len(exercise_tools)
        if tool_count == 1:
            tool = list(exercise_tools.keys())[0]
            recommendations.append(f"오늘은 {tool}만 사용했습니다. 다양한 도구를 활용하여 운동의 다양성을 높여보세요.")
        elif tool_count >= 2:
            insights.append(f"{tool_count}가지 운동 도구를 활용하여 다양한 자극을 주었습니다.")
        
        # 5. 근육 타겟 분석
        muscle_count = len(muscles)
        if muscle_count > 0:
            insights.append(f"주요 타겟 근육: {', '.join(muscles)}")
            if "넙다리네갈래근" in muscles:
                recommendations.append("넙다리네갈래근을 집중적으로 운동했습니다. 운동 후 스트레칭으로 유연성을 유지하세요.")
        
        # 6. 개별 운동 상세 분석
        exercise_details = []
        for ex in exercises:
            exercise_info = ex.get("exercise", {})
            exercise_name = exercise_info.get("title", "")
            exercise_time = ex.get("exerciseTime", 0)
            intensity = ex.get("intensity", "")
            tool = exercise_info.get("exerciseTool", "")
            
            # 운동별 맞춤 분석
            if "스쿼트" in exercise_name or "앉았다" in exercise_name:
                if intensity == "상" and exercise_time > 25:
                    exercise_details.append(f"'{exercise_name}': 고강도로 충분한 시간 운동했습니다. 대퇴사두근과 둔근 발달에 효과적입니다.")
                elif intensity == "중":
                    exercise_details.append(f"'{exercise_name}': 적절한 강도로 운동했습니다. 자세에 집중하여 안전하게 수행하세요.")
            
            elif "다리" in exercise_name and ("밀기" in exercise_name or "펴기" in exercise_name):
                if exercise_time < 15:
                    exercise_details.append(f"'{exercise_name}': {exercise_time}분은 조금 짧습니다. 15-20분으로 늘리면 더 효과적입니다.")
                else:
                    exercise_details.append(f"'{exercise_name}': {exercise_time}분간 {intensity}강도로 적절히 운동했습니다.")
        
        insights.extend(exercise_details)
        
        # 7. 운동 순서 및 조합 분석
        if len(exercises) >= 2:
            first_exercise = exercises[0]["exercise"]["title"]
            last_exercise = exercises[-1]["exercise"]["title"]
            insights.append(f"운동 순서: '{first_exercise}' → '{last_exercise}'로 구성되어 있습니다.")
            
            # 복합운동 vs 고립운동 분석
            compound_exercises = []
            isolation_exercises = []
            
            for ex in exercises:
                exercise_name = ex["exercise"]["title"]
                if any(keyword in exercise_name for keyword in ["스쿼트", "데드리프트", "벤치프레스", "풀업", "앉았다"]):
                    compound_exercises.append(exercise_name)
                else:
                    isolation_exercises.append(exercise_name)
            
            if compound_exercises and isolation_exercises:
                insights.append(f"복합운동({len(compound_exercises)}개)과 고립운동({len(isolation_exercises)}개)을 적절히 조합했습니다.")
            elif compound_exercises:
                insights.append(f"복합운동 위주로 구성되어 효율적인 운동입니다.")
        
        # 8. 메모 감정 분석
        memo = workout_data.get("memo", "")
        if memo:
            insights.append(f"운동 메모: '{memo}'")
            if any(word in memo for word in ["힘들", "어려", "고생", "조졋"]):
                insights.append("운동이 힘들었던 것 같습니다. 점진적으로 강도를 조절하여 지속 가능한 운동을 하세요.")
                recommendations.append("운동 전 충분한 워밍업과 운동 후 쿨다운을 실시하세요.")
            elif any(word in memo for word in ["좋", "만족", "성공", "완료"]):
                insights.append("운동에 만족하고 계시는군요! 꾸준한 운동으로 목표를 달성하세요.")
        
        # 9. 운동 강도별 상세 추천
        if high_intensity_ratio > 50:
            recommendations.append("고강도 운동 후에는 단백질 보충제나 BCAA 섭취를 고려하세요.")
        
        if total_time > 90:
            recommendations.append("장시간 운동 후에는 충분한 수분 섭취와 전해질 보충이 필요합니다.")
        
        # 10. 다음 운동 계획 제안
        if body_part_count == 1:
            main_part = list(body_parts.keys())[0]
            if main_part == "하체":
                recommendations.append("다음 운동에서는 상체(가슴, 등, 어깨) 운동을 추가하여 균형을 맞춰보세요.")
            elif main_part == "상체":
                recommendations.append("다음 운동에서는 하체(스쿼트, 런지 등) 운동을 추가하여 균형을 맞춰보세요.")
        
        # 결과 구성
        workout_date = workout_data.get("date", "해당 날짜")
        analysis_result = {
            "summary": f"{workout_date}에 {total_exercises}개 운동을 총 {total_time}분간 수행했습니다.",
            "statistics": {
                "total_exercises": total_exercises,
                "total_time": total_time,
                "avg_time_per_exercise": round(avg_time_per_exercise, 1),
                "intensity_distribution": intensity_dist,
                "intensity_percentage": intensity_percentage,
                "body_parts_trained": body_parts,
                "exercise_tools_used": exercise_tools,
                "muscles_targeted": list(muscles)
            },
            "insights": insights,
            "recommendations": recommendations,
            "warnings": warnings,
            "highlights": {
                "most_frequent_body_part": most_frequent_body_part,
                "most_used_tool": most_used_tool,
                "dominant_intensity": max(intensity_dist.items(), key=lambda x: x[1]) if total_intensity > 0 else ("없음", 0)
            }
        }
        
        return analysis_result
        
    except Exception as e:
        return {
            "error": f"분석 중 오류 발생: {str(e)}",
            "summary": "운동 데이터 분석에 실패했습니다."
        }

@app.get("/api/journals/by-date")
async def get_daily_log_by_date(
    date: str = Query(..., description="조회할 날짜 (형식: yyyy-MM-dd)"),
    authorization: str = Header(..., description="Bearer 토큰")
):
    """
    외부 API를 통해 특정 날짜의 운동 일지를 조회하고 분석합니다.
    
    - **date**: 조회할 날짜 (yyyy-MM-dd 형식, 예: 2025-10-08)
    - **Authorization**: HTTP Header로 Bearer 토큰 전달 (예: Bearer eyJhbGc...)
    
    Returns:
    - 운동 일지 데이터 + AI 분석 결과 (운동 패턴, 강도 분석, 추천사항 등)
    
    Example:
        GET /api/journals/by-date?date=2025-10-08
        Headers: Authorization: Bearer YOUR_ACCESS_TOKEN
    """
    try:
        # Bearer 토큰에서 실제 토큰 값 추출
        access_token = authorization
        if authorization.startswith("Bearer "):
            access_token = authorization[7:]  # "Bearer " 제거
        
        # 외부 API 호출
        result = await external_api.get_daily_log_by_date(
            date=date,
            access_token=access_token
        )
        
        if result.get("success"):
            # 운동 일지 데이터 분석
            analysis_result = await analyze_daily_workout(result["data"])
            
            # 원본 데이터와 분석 결과를 함께 반환
            return {
                "success": True,
                "date": date,
                "original_data": result["data"],
                "analysis": analysis_result
            }
        else:
            # 실패 시 적절한 HTTP 상태 코드 반환
            status_code = result.get("status_code", 500)
            raise HTTPException(
                status_code=status_code,
                detail=result.get("error", "운동 일지 조회 실패")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"운동 일지 조회 및 분석 중 오류 발생: {str(e)}"
        )


@app.get("/api/analysis/workout-pattern/{user_id}", response_model=WorkoutPatternAnalysis)
async def analyze_workout_pattern(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 운동 패턴을 분석합니다.
    
    - **user_id**: 사용자 ID
    - **days**: 분석 기간 (기본: 30일)
    
    Returns:
    - 운동 빈도, 신체 부위별 분포, 주로 한 운동, 강도 분포 등
    """
    try:
        analysis_service = WorkoutAnalysisService(db)
        pattern = analysis_service.analyze_workout_pattern(user_id, days)
        return pattern
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"운동 패턴 분석 중 오류 발생: {str(e)}"
        )


@app.get("/api/analysis/insights/{user_id}", response_model=WorkoutInsight)
async def get_workout_insights(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """
    사용자의 운동 데이터를 기반으로 맞춤형 인사이트를 제공합니다.
    
    - **user_id**: 사용자 ID
    - **days**: 분석 기간 (기본: 30일)
    
    Returns:
    - 과사용 부위 (휴식 필요)
    - 부족한 부위 (보충 필요)
    - 균형 점수
    - 맞춤 추천 및 주의사항
    """
    try:
        analysis_service = WorkoutAnalysisService(db)
        insights = analysis_service.generate_insights(user_id, days)
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"인사이트 생성 중 오류 발생: {str(e)}"
        )


@app.get("/api/analysis/comprehensive/{user_id}", response_model=ComprehensiveAnalysis)
async def get_comprehensive_analysis(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db)
):
    """
    사용자의 종합 운동 분석 결과를 반환합니다.
    
    - **user_id**: 사용자 ID
    - **days**: 분석 기간 (기본: 30일)
    
    Returns:
    - 운동 패턴 분석 + 맞춤 인사이트 통합
    - 어떤 운동을 주로 하는지
    - 어떤 근육이 주로 사용되는지
    - 어떤 부위에 휴식/보충이 필요한지
    """
    try:
        analysis_service = WorkoutAnalysisService(db)
        comprehensive = analysis_service.get_comprehensive_analysis(user_id, days)
        return comprehensive
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"종합 분석 중 오류 발생: {str(e)}"
        )


@app.get("/api/analysis/ai-recommendation/{user_id}")
async def get_ai_recommendation(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="분석 기간 (일)"),
    model: str = Query(default="gpt-4o-mini", description="사용할 OpenAI 모델"),
    db: Session = Depends(get_db)
):
    """
    AI 기반 맞춤 운동 추천을 반환합니다.
    
    - **user_id**: 사용자 ID
    - **days**: 분석 기간 (기본: 30일)
    - **model**: OpenAI 모델 (기본: gpt-4o-mini)
    
    Returns:
    - 운동 일지 분석 결과
    - AI가 생성한 맞춤형 운동 조언
    - 추천 운동 루틴
    """
    try:
        # 1. 기본 분석 수행
        analysis_service = WorkoutAnalysisService(db)
        comprehensive = analysis_service.get_comprehensive_analysis(user_id, days)
        
        # 2. OpenAI AI 추천 생성
        ai_result = openai_service.generate_workout_recommendation(comprehensive, model=model)
        
        # 3. 결과 통합
        return {
            "user_id": user_id,
            "analysis_period": f"최근 {days}일",
            "basic_analysis": {
                "total_workouts": comprehensive.pattern.total_workouts,
                "total_time": comprehensive.pattern.total_time,
                "balance_score": comprehensive.insights.balance_score,
                "overworked_parts": comprehensive.insights.overworked_parts,
                "underworked_parts": comprehensive.insights.underworked_parts
            },
            "ai_recommendation": ai_result.get("ai_recommendation", ""),
            "ai_success": ai_result.get("success", False),
            "fallback_used": not ai_result.get("success", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 추천 생성 중 오류 발생: {str(e)}"
        )


@app.post("/api/workout-log/analyze")
async def analyze_workout_log_with_ai(
    workout_log: Dict[str, Any],
    model: str = Query(default="gpt-4o-mini", description="사용할 OpenAI 모델 (gpt-4o-mini, gpt-4o, gpt-4)")
):
    """
    OpenAI를 활용한 운동 일지 분석 및 평가
    
    - **workout_log**: 운동 일지 데이터 (JSON)
        - date: 날짜
        - memo: 메모
        - exercises: 운동 목록
    - **model**: OpenAI 모델 선택
        - gpt-4o-mini: 가장 저렴하고 빠름 (기본값)
        - gpt-4o: 균형잡힌 성능
        - gpt-4: 최고 품질
        
    Returns:
    - AI 분석 결과 (운동 평가, 추천사항)
    """
    try:
        # OpenAI를 통한 운동 일지 분석
        ai_analysis = openai_service.analyze_workout_log(workout_log, model=model)
        
        if not ai_analysis.get("success"):
            # OpenAI 실패 시 기본 분석 제공
            basic_analysis = await analyze_daily_workout(workout_log)
            return {
                "success": False,
                "message": ai_analysis.get("message", "AI 분석 실패"),
                "basic_analysis": basic_analysis
            }
        
        # 기본 분석도 함께 제공
        basic_analysis = await analyze_daily_workout(workout_log)
        
        return {
            "success": True,
            "ai_analysis": ai_analysis.get("analysis"),
            "basic_analysis": basic_analysis,
            "model": ai_analysis.get("model"),
            "date": workout_log.get("date")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"운동 일지 분석 중 오류 발생: {str(e)}"
        )


@app.post("/api/workout-log/recommend")
async def recommend_workout_routine(
    workout_log: Dict[str, Any],
    days: int = Query(default=7, ge=1, le=30, description="루틴 기간 (일)"),
    frequency: int = Query(default=4, ge=1, le=7, description="주간 운동 빈도"),
    model: str = Query(default="gpt-4o-mini", description="사용할 OpenAI 모델")
):
    """
    OpenAI를 활용한 맞춤 운동 루틴 추천
    
    - **workout_log**: 운동 일지 데이터 (JSON)
    - **days**: 루틴 기간 (기본: 7일)
    - **frequency**: 주간 운동 빈도 (기본: 4회)
    - **model**: OpenAI 모델 (기본: gpt-4o-mini)
    
    Returns:
    - AI 추천 운동 루틴
    """
    try:
        # OpenAI를 통한 운동 루틴 추천
        ai_routine = openai_service.recommend_workout_routine(
            workout_log, 
            days=days, 
            frequency=frequency,
            model=model
        )
        
        if not ai_routine.get("success"):
            raise HTTPException(
                status_code=500,
                detail=ai_routine.get("message", "AI 루틴 추천 실패")
            )
        
        # 기본 분석도 함께 제공
        basic_analysis = await analyze_daily_workout(workout_log)
        
        return {
            "success": True,
            "ai_routine": ai_routine.get("routine"),
            "basic_summary": {
                "date": workout_log.get("date"),
                "total_exercises": len(workout_log.get("exercises", [])),
                "summary": basic_analysis.get("summary", "")
            },
            "routine_period": {
                "days": days,
                "frequency": frequency
            },
            "model": ai_routine.get("model")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"운동 루틴 추천 중 오류 발생: {str(e)}"
        )


# ==================== 서버 실행 ====================

if __name__ == "__main__":
    import uvicorn
    
    # 환경 변수에서 포트 설정 (CloudType 등 배포 환경 대응)
    port = int(os.getenv("PORT", 3000))  # CloudType 기본 포트 3000
    host = os.getenv("HOST", "0.0.0.0")
    
    print("🚀 ExRecAI 서버를 시작합니다...")
    print(f"📍 서버 주소: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    print("🔥 Ctrl+C로 서버를 중지할 수 있습니다.")
    
    # CloudType 배포 환경 감지
    if os.getenv("CLOUDTYPE"):
        print("☁️ CloudType 배포 환경에서 실행 중...")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",  # 개발 환경에서만 reload
        log_level="info"
    )
