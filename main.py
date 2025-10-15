"""
ExRecAI - 운동 추천 AI 시스템
FastAPI 메인 서버 애플리케이션
"""

import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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


# ==================== 서버 실행 ====================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 ExRecAI 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🔥 Ctrl+C로 서버를 중지할 수 있습니다.")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발용: 코드 변경시 자동 재시작
        log_level="info"
    )
