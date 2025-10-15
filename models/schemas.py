"""
Pydantic 스키마 정의
API 요청/응답 및 데이터 검증을 위한 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExerciseBase(BaseModel):
    """운동 기본 스키마"""
    name: str
    name_en: Optional[str] = None
    body_part: str
    category: str
    difficulty: str
    duration: int
    equipment: Optional[str] = None
    target_goal: str
    instructions: Optional[str] = None
    tips: Optional[str] = None
    muscle_group: Optional[str] = None
    calories_per_minute: Optional[float] = None


class ExerciseCreate(ExerciseBase):
    """운동 생성 스키마"""
    pass


class Exercise(ExerciseBase):
    """운동 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserGoalBase(BaseModel):
    """사용자 목표 기본 스키마"""
    user_id: str
    weekly_frequency: int = Field(..., ge=1, le=7, description="주간 운동 빈도 (1-7회)")
    split_type: str = Field(..., pattern="^(2분할|3분할|전신)$")
    primary_goal: str = Field(..., pattern="^(근육 증가|다이어트|체력 향상|재활|유지)$")
    secondary_goal: Optional[str] = None
    experience_level: str = Field(..., pattern="^(초급|중급|고급)$")
    available_time: int = Field(..., ge=15, le=180, description="1회 운동 시간 (15-180분)")
    preferred_equipment: Optional[str] = None
    health_conditions: Optional[str] = None


class UserGoalCreate(UserGoalBase):
    """사용자 목표 생성 스키마"""
    pass


class UserGoal(UserGoalBase):
    """사용자 목표 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkoutExerciseBase(BaseModel):
    """운동 계획 내 운동 기본 스키마"""
    exercise_id: int
    order_in_session: int
    sets: int = Field(..., ge=1, le=10)
    reps_min: Optional[int] = Field(None, ge=1, le=50)
    reps_max: Optional[int] = Field(None, ge=1, le=50)
    weight_percentage: Optional[float] = Field(None, ge=0.3, le=1.2)
    rest_seconds: int = Field(..., ge=30, le=300)
    notes: Optional[str] = None


class WorkoutExerciseCreate(WorkoutExerciseBase):
    """운동 계획 내 운동 생성 스키마"""
    pass


class WorkoutExercise(WorkoutExerciseBase):
    """운동 계획 내 운동 응답 스키마"""
    id: int
    exercise: Exercise

    class Config:
        from_attributes = True


class WorkoutSessionBase(BaseModel):
    """운동 세션 기본 스키마"""
    day_number: int = Field(..., ge=1, le=7)
    day_name: str
    target_body_parts: str
    estimated_duration: int


class WorkoutSessionCreate(WorkoutSessionBase):
    """운동 세션 생성 스키마"""
    exercises: List[WorkoutExerciseCreate]


class WorkoutSession(WorkoutSessionBase):
    """운동 세션 응답 스키마"""
    id: int
    workout_exercises: List[WorkoutExercise] = []

    class Config:
        from_attributes = True


class WorkoutPlanBase(BaseModel):
    """운동 계획 기본 스키마"""
    plan_name: str
    total_duration: int
    difficulty_score: float = Field(..., ge=1.0, le=5.0)


class WorkoutPlanCreate(WorkoutPlanBase):
    """운동 계획 생성 스키마"""
    user_goal_id: int
    sessions: List[WorkoutSessionCreate]


class WorkoutPlan(WorkoutPlanBase):
    """운동 계획 응답 스키마"""
    id: int
    user_goal_id: int
    workout_sessions: List[WorkoutSession] = []
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """추천 요청 스키마"""
    user_id: str = Field(..., min_length=1)
    weekly_frequency: int = Field(..., ge=1, le=7, description="주간 운동 빈도")
    split_type: str = Field(..., description="분할 방식: 2분할, 3분할, 전신")
    primary_goal: str = Field(..., description="주 목표: 근육 증가, 다이어트, 체력 향상")
    experience_level: str = Field(..., description="경험 수준: 초급, 중급, 고급")
    available_time: int = Field(..., ge=15, le=180, description="1회 운동 시간")
    preferred_equipment: Optional[str] = Field(None, description="선호 장비")
    exclude_exercises: Optional[List[str]] = Field(None, description="제외할 운동들")
    
    @validator('split_type')
    def validate_split_type(cls, v):
        allowed = ['2분할', '3분할', '전신']
        if v not in allowed:
            raise ValueError(f'분할 방식은 {allowed} 중 하나여야 합니다.')
        return v
    
    @validator('primary_goal')
    def validate_primary_goal(cls, v):
        allowed = ['근육 증가', '다이어트', '체력 향상', '재활', '유지']
        if v not in allowed:
            raise ValueError(f'목표는 {allowed} 중 하나여야 합니다.')
        return v
    
    @validator('experience_level')
    def validate_experience_level(cls, v):
        allowed = ['초급', '중급', '고급']
        if v not in allowed:
            raise ValueError(f'경험 수준은 {allowed} 중 하나여야 합니다.')
        return v


class ExerciseRecommendation(BaseModel):
    """개별 운동 추천 결과"""
    name: str
    name_en: Optional[str] = None
    body_part: str
    sets: int
    reps: str  # "8-12" 또는 "15" 형태
    weight: Optional[str] = None  # "중량의 70%" 등
    rest: str  # "2-3분"
    instructions: Optional[str] = None
    tips: Optional[str] = None
    difficulty: str
    equipment: Optional[str] = None
    # 영상 관련 필드 추가
    video_url: Optional[str] = None
    video_id: Optional[int] = None
    image_url: Optional[str] = None
    video_length: Optional[int] = None  # 초 단위
    target_group: Optional[str] = None
    fitness_factor: Optional[str] = None


class DayRecommendation(BaseModel):
    """일별 운동 추천 결과"""
    day_name: str
    target_body_parts: List[str]
    exercises: List[ExerciseRecommendation]
    estimated_duration: int
    warm_up_time: int = 10
    cool_down_time: int = 10


class RecommendationResponse(BaseModel):
    """추천 응답 스키마"""
    success: bool = True
    message: str = "추천이 성공적으로 생성되었습니다."
    recommendation: Dict[str, DayRecommendation]
    summary: Dict[str, Any]
    tips: List[str] = []
    total_weekly_duration: int
    difficulty_score: float
    created_at: datetime


class UserFeedbackCreate(BaseModel):
    """피드백 생성 스키마"""
    user_id: str
    exercise_id: int
    rating: int = Field(..., ge=1, le=5, description="전체 평점 (1-5)")
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5, description="난이도 (1-5)")
    enjoyment_rating: Optional[int] = Field(None, ge=1, le=5, description="재미 (1-5)")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="효과 (1-5)")
    feedback_text: Optional[str] = None


class UserFeedback(BaseModel):
    """피드백 응답 스키마"""
    id: int
    user_id: str
    exercise_id: int
    rating: int
    difficulty_rating: Optional[int]
    enjoyment_rating: Optional[int]
    effectiveness_rating: Optional[int]
    feedback_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HealthStatus(BaseModel):
    """시스템 상태 응답"""
    status: str = "healthy"
    database_connected: bool
    total_exercises: int
    total_users: int
    version: str = "1.0.0"
    uptime: str
