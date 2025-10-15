"""
데이터베이스 모델 정의
SQLAlchemy ORM을 사용하여 운동 추천 시스템의 데이터 구조를 정의합니다.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

# 데이터베이스 엔진 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/fitness.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Exercise(Base):
    """운동 정보 테이블"""
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_en = Column(String(100), nullable=True)  # 영어 이름
    body_part = Column(String(50), nullable=False, index=True)  # 가슴, 등, 하체, 어깨, 팔, 코어
    category = Column(String(50), nullable=False, index=True)  # 웨이트, 체중, 유산소, 스트레칭
    difficulty = Column(String(20), nullable=False, index=True)  # 초급, 중급, 고급
    duration = Column(Integer, nullable=False)  # 예상 소요 시간 (분)
    equipment = Column(String(100), nullable=True)  # 필요 장비
    target_goal = Column(String(50), nullable=False, index=True)  # 근육 증가, 다이어트, 체력 향상
    instructions = Column(Text, nullable=True)  # 운동 방법
    tips = Column(Text, nullable=True)  # 주의사항 및 팁
    muscle_group = Column(String(100), nullable=True)  # 세부 근육군
    calories_per_minute = Column(Float, nullable=True)  # 분당 칼로리 소모량
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserGoal(Base):
    """사용자 목표 테이블"""
    __tablename__ = "user_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)  # 사용자 식별자
    weekly_frequency = Column(Integer, nullable=False)  # 주간 운동 빈도
    split_type = Column(String(20), nullable=False)  # 2분할, 3분할, 전신
    primary_goal = Column(String(50), nullable=False)  # 주 목표
    secondary_goal = Column(String(50), nullable=True)  # 부 목표
    experience_level = Column(String(20), nullable=False)  # 초급, 중급, 고급
    available_time = Column(Integer, nullable=False)  # 1회 운동 가능 시간 (분)
    preferred_equipment = Column(String(200), nullable=True)  # 선호 장비
    health_conditions = Column(Text, nullable=True)  # 건강상 제약사항
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkoutPlan(Base):
    """생성된 운동 계획 테이블"""
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_goal_id = Column(Integer, ForeignKey("user_goals.id"), nullable=False)
    plan_name = Column(String(100), nullable=False)
    total_duration = Column(Integer, nullable=False)  # 전체 운동 시간
    difficulty_score = Column(Float, nullable=False)  # 난이도 점수
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user_goal = relationship("UserGoal", back_populates="workout_plans")
    workout_sessions = relationship("WorkoutSession", back_populates="workout_plan")


class WorkoutSession(Base):
    """운동 세션 테이블 (일별 운동)"""
    __tablename__ = "workout_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    day_number = Column(Integer, nullable=False)  # 1, 2, 3, 4 (주간 운동 일차)
    day_name = Column(String(50), nullable=False)  # "Day 1 - 가슴/삼두"
    target_body_parts = Column(String(100), nullable=False)  # "가슴,삼두"
    estimated_duration = Column(Integer, nullable=False)  # 예상 소요 시간
    
    # 관계 설정
    workout_plan = relationship("WorkoutPlan", back_populates="workout_sessions")
    workout_exercises = relationship("WorkoutExercise", back_populates="workout_session")


class WorkoutExercise(Base):
    """운동 계획에 포함된 개별 운동"""
    __tablename__ = "workout_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    workout_session_id = Column(Integer, ForeignKey("workout_sessions.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    order_in_session = Column(Integer, nullable=False)  # 세션 내 운동 순서
    sets = Column(Integer, nullable=False)  # 세트 수
    reps_min = Column(Integer, nullable=True)  # 최소 반복 수
    reps_max = Column(Integer, nullable=True)  # 최대 반복 수
    weight_percentage = Column(Float, nullable=True)  # 1RM 대비 무게 비율
    rest_seconds = Column(Integer, nullable=False)  # 세트간 휴식 시간 (초)
    notes = Column(Text, nullable=True)  # 특이사항
    
    # 관계 설정
    workout_session = relationship("WorkoutSession", back_populates="workout_exercises")
    exercise = relationship("Exercise")


class UserFeedback(Base):
    """사용자 피드백 테이블 (향후 ML 학습용)"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 점수
    difficulty_rating = Column(Integer, nullable=True)  # 난이도 평가 1-5
    enjoyment_rating = Column(Integer, nullable=True)  # 재미 평가 1-5
    effectiveness_rating = Column(Integer, nullable=True)  # 효과 평가 1-5
    feedback_text = Column(Text, nullable=True)  # 자유 피드백
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    exercise = relationship("Exercise")


class DailyLog(Base):
    """운동 일지 테이블"""
    __tablename__ = "daily_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # yyyy-MM-dd 형식
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    log_exercises = relationship("LogExercise", back_populates="daily_log", cascade="all, delete-orphan")


class LogExercise(Base):
    """일지에 기록된 운동 항목"""
    __tablename__ = "log_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    daily_log_id = Column(Integer, ForeignKey("daily_logs.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    intensity = Column(String(10), nullable=False)  # 상, 중, 하
    exercise_time = Column(Integer, nullable=False)  # 운동 시간 (분)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    daily_log = relationship("DailyLog", back_populates="log_exercises")
    exercise = relationship("Exercise")


# 관계 역방향 설정
UserGoal.workout_plans = relationship("WorkoutPlan", back_populates="user_goal")


def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """테이블 생성"""
    Base.metadata.create_all(bind=engine)

