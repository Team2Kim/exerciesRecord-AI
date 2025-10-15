"""
데이터베이스 초기화 스크립트
테이블을 생성하고 샘플 데이터를 삽입합니다.
"""

import json
import os
from sqlalchemy.orm import Session
from models.database import engine, SessionLocal, create_tables
from models.database import Exercise, UserGoal, WorkoutPlan, WorkoutSession, WorkoutExercise, UserFeedback, DailyLog, LogExercise
from datetime import datetime, timedelta
import random


def load_sample_exercises():
    """샘플 운동 데이터 로드"""
    exercises_file = "data/exercises.json"
    
    if not os.path.exists(exercises_file):
        print(f"❌ {exercises_file} 파일을 찾을 수 없습니다.")
        return []
    
    with open(exercises_file, 'r', encoding='utf-8') as f:
        exercises_data = json.load(f)
    
    print(f"✅ {len(exercises_data)}개의 운동 데이터를 로드했습니다.")
    return exercises_data


def insert_sample_exercises(db: Session, exercises_data: list):
    """샘플 운동 데이터를 데이터베이스에 삽입"""
    
    # 기존 운동 데이터가 있는지 확인
    existing_count = db.query(Exercise).count()
    if existing_count > 0:
        print(f"⚠️ 이미 {existing_count}개의 운동 데이터가 존재합니다. 삽입을 건너뜁니다.")
        return
    
    exercises = []
    for exercise_data in exercises_data:
        exercise = Exercise(**exercise_data)
        exercises.append(exercise)
    
    try:
        db.add_all(exercises)
        db.commit()
        print(f"✅ {len(exercises)}개의 운동 데이터를 성공적으로 삽입했습니다.")
    except Exception as e:
        db.rollback()
        print(f"❌ 운동 데이터 삽입 중 오류 발생: {e}")


def insert_sample_user_goals(db: Session):
    """샘플 사용자 목표 데이터 삽입"""
    
    # 기존 사용자 목표 데이터가 있는지 확인
    existing_count = db.query(UserGoal).count()
    if existing_count > 0:
        print(f"⚠️ 이미 {existing_count}개의 사용자 목표가 존재합니다. 삽입을 건너뜁니다.")
        return
    
    sample_goals = [
        {
            "user_id": "demo_user_1",
            "weekly_frequency": 4,
            "split_type": "3분할",
            "primary_goal": "근육 증가",
            "secondary_goal": "체력 향상",
            "experience_level": "중급",
            "available_time": 60,
            "preferred_equipment": "바벨, 덤벨, 머신",
            "health_conditions": None
        },
        {
            "user_id": "demo_user_2",
            "weekly_frequency": 3,
            "split_type": "전신",
            "primary_goal": "다이어트",
            "secondary_goal": None,
            "experience_level": "초급",
            "available_time": 45,
            "preferred_equipment": "체중운동 위주",
            "health_conditions": "무릎 부상 경험"
        },
        {
            "user_id": "demo_user_3",
            "weekly_frequency": 5,
            "split_type": "2분할",
            "primary_goal": "체력 향상",
            "secondary_goal": "근육 증가",
            "experience_level": "고급",
            "available_time": 90,
            "preferred_equipment": "모든 장비 가능",
            "health_conditions": None
        }
    ]
    
    goals = []
    for goal_data in sample_goals:
        goal = UserGoal(**goal_data)
        goals.append(goal)
    
    try:
        db.add_all(goals)
        db.commit()
        print(f"✅ {len(goals)}개의 샘플 사용자 목표를 성공적으로 삽입했습니다.")
    except Exception as e:
        db.rollback()
        print(f"❌ 사용자 목표 삽입 중 오류 발생: {e}")


def insert_sample_feedback(db: Session):
    """샘플 피드백 데이터 삽입"""
    
    # 기존 피드백 데이터가 있는지 확인
    existing_count = db.query(UserFeedback).count()
    if existing_count > 0:
        print(f"⚠️ 이미 {existing_count}개의 피드백이 존재합니다. 삽입을 건너뜁니다.")
        return
    
    # 운동 ID들 가져오기
    exercises = db.query(Exercise).limit(10).all()
    if not exercises:
        print("⚠️ 피드백을 추가할 운동 데이터가 없습니다.")
        return
    
    sample_feedback = [
        {
            "user_id": "demo_user_1",
            "exercise_id": exercises[0].id,  # 벤치프레스
            "rating": 5,
            "difficulty_rating": 4,
            "enjoyment_rating": 5,
            "effectiveness_rating": 5,
            "feedback_text": "정말 효과적인 운동입니다. 가슴 근육 발달에 도움이 많이 됐어요."
        },
        {
            "user_id": "demo_user_1",
            "exercise_id": exercises[1].id,  # 스쿼트
            "rating": 4,
            "difficulty_rating": 3,
            "enjoyment_rating": 4,
            "effectiveness_rating": 5,
            "feedback_text": "하체 근력 강화에 최고입니다."
        },
        {
            "user_id": "demo_user_2",
            "exercise_id": exercises[3].id,  # 푸시업
            "rating": 4,
            "difficulty_rating": 2,
            "enjoyment_rating": 3,
            "effectiveness_rating": 4,
            "feedback_text": "집에서 하기 좋은 운동이네요."
        }
    ]
    
    feedback_list = []
    for feedback_data in sample_feedback:
        feedback = UserFeedback(**feedback_data)
        feedback_list.append(feedback)
    
    try:
        db.add_all(feedback_list)
        db.commit()
        print(f"✅ {len(feedback_list)}개의 샘플 피드백을 성공적으로 삽입했습니다.")
    except Exception as e:
        db.rollback()
        print(f"❌ 피드백 삽입 중 오류 발생: {e}")


def insert_sample_daily_logs(db: Session):
    """샘플 운동 일지 데이터 삽입"""
    
    # 기존 일지 데이터 확인
    existing_count = db.query(DailyLog).count()
    if existing_count > 0:
        print(f"⚠️ 이미 {existing_count}개의 일지가 존재합니다. 삽입을 건너뜁니다.")
        return
    
    # 운동 데이터 조회
    exercises = db.query(Exercise).all()
    if not exercises:
        print("❌ 운동 데이터가 없어 일지를 생성할 수 없습니다.")
        return
    
    # 신체 부위별 운동 분류
    exercises_by_part = {}
    for ex in exercises:
        if ex.body_part not in exercises_by_part:
            exercises_by_part[ex.body_part] = []
        exercises_by_part[ex.body_part].append(ex)
    
    # 최근 30일 간의 샘플 일지 생성 (주 3-4회)
    user_id = "demo_user"
    today = datetime.now().date()
    
    # 30일간 주 3-4회 운동 (랜덤하게 운동한 날 선택)
    workout_days = []
    for week in range(5):  # 5주
        week_start = today - timedelta(days=7 * week)
        # 각 주에 3-4일 랜덤 선택
        days_this_week = random.randint(3, 4)
        for _ in range(days_this_week):
            day_offset = random.randint(0, 6)
            workout_day = week_start - timedelta(days=day_offset)
            if workout_day not in workout_days and workout_day <= today:
                workout_days.append(workout_day)
    
    workout_days.sort()
    
    # 운동 패턴 정의 (가슴에 편중되도록)
    body_part_weights = {
        "가슴": 0.35,    # 35% - 과사용
        "등": 0.08,      # 8% - 부족
        "하체": 0.25,    # 25%
        "어깨": 0.15,    # 15%
        "팔": 0.12,      # 12%
        "코어": 0.05     # 5% - 부족
    }
    
    daily_logs = []
    
    for day in workout_days:
        # 일지 생성
        log = DailyLog(
            user_id=user_id,
            date=day.strftime("%Y-%m-%d"),
            memo=random.choice([
                "오늘은 컨디션이 좋았다!",
                "힘들었지만 완료",
                "근육통이 있지만 운동 완료",
                "좋은 운동이었다",
                None
            ])
        )
        db.add(log)
        db.flush()  # ID 생성
        
        # 이 날 할 운동 3-5개 선택 (신체 부위 가중치에 따라)
        num_exercises = random.randint(3, 5)
        
        for _ in range(num_exercises):
            # 가중치에 따라 신체 부위 선택
            body_part = random.choices(
                list(body_part_weights.keys()),
                weights=list(body_part_weights.values())
            )[0]
            
            # 해당 부위의 운동 중 랜덤 선택
            if body_part in exercises_by_part and exercises_by_part[body_part]:
                exercise = random.choice(exercises_by_part[body_part])
                
                # 운동 기록 생성
                log_exercise = LogExercise(
                    daily_log_id=log.id,
                    exercise_id=exercise.id,
                    intensity=random.choices(
                        ["상", "중", "하"],
                        weights=[0.3, 0.5, 0.2]  # 중강도가 가장 많음
                    )[0],
                    exercise_time=random.randint(15, 45)  # 15-45분
                )
                db.add(log_exercise)
        
        daily_logs.append(log)
    
    try:
        db.commit()
        print(f"✅ {len(daily_logs)}개의 샘플 일지를 성공적으로 삽입했습니다.")
        print(f"   (최근 30일간 운동 기록)")
    except Exception as e:
        db.rollback()
        print(f"❌ 일지 삽입 중 오류 발생: {e}")


def verify_database(db: Session):
    """데이터베이스 내용 확인"""
    print("\n📊 데이터베이스 현황:")
    print("-" * 50)
    
    exercise_count = db.query(Exercise).count()
    goal_count = db.query(UserGoal).count()
    plan_count = db.query(WorkoutPlan).count()
    session_count = db.query(WorkoutSession).count()
    workout_exercise_count = db.query(WorkoutExercise).count()
    feedback_count = db.query(UserFeedback).count()
    daily_log_count = db.query(DailyLog).count()
    log_exercise_count = db.query(LogExercise).count()
    
    print(f"운동 데이터: {exercise_count}개")
    print(f"사용자 목표: {goal_count}개")
    print(f"운동 계획: {plan_count}개")
    print(f"운동 세션: {session_count}개")
    print(f"계획별 운동: {workout_exercise_count}개")
    print(f"사용자 피드백: {feedback_count}개")
    print(f"운동 일지: {daily_log_count}개")
    print(f"일지 운동 기록: {log_exercise_count}개")
    
    # 운동 부위별 통계
    print(f"\n🏋️ 운동 부위별 통계:")
    from sqlalchemy import func
    body_parts = db.query(Exercise.body_part, func.count(Exercise.id)).group_by(Exercise.body_part).all()
    for body_part, count in body_parts:
        print(f"  {body_part}: {count}개")
    
    # 운동 카테고리별 통계  
    print(f"\n📈 운동 카테고리별 통계:")
    categories = db.query(Exercise.category, func.count(Exercise.id)).group_by(Exercise.category).all()
    for category, count in categories:
        print(f"  {category}: {count}개")


def main():
    """메인 함수"""
    print("🚀 ExRecAI 데이터베이스 초기화 시작")
    print("=" * 60)
    
    # 데이터 폴더 생성
    os.makedirs("data", exist_ok=True)
    
    try:
        # 1. 테이블 생성
        print("1️⃣ 데이터베이스 테이블 생성...")
        create_tables()
        print("✅ 테이블 생성 완료")
        
        # 2. 데이터베이스 세션 생성
        db = SessionLocal()
        
        # 3. 샘플 운동 데이터 삽입
        print("\n2️⃣ 샘플 운동 데이터 삽입...")
        exercises_data = load_sample_exercises()
        if exercises_data:
            insert_sample_exercises(db, exercises_data)
        
        # 4. 샘플 사용자 목표 삽입
        print("\n3️⃣ 샘플 사용자 목표 삽입...")
        insert_sample_user_goals(db)
        
        # 5. 샘플 피드백 삽입
        print("\n4️⃣ 샘플 피드백 삽입...")
        insert_sample_feedback(db)
        
        # 6. 샘플 운동 일지 삽입
        print("\n5️⃣ 샘플 운동 일지 삽입...")
        insert_sample_daily_logs(db)
        
        # 7. 데이터베이스 확인
        print("\n6️⃣ 데이터베이스 확인...")
        verify_database(db)
        
        db.close()
        
        print("\n🎉 데이터베이스 초기화 완료!")
        print("📍 데이터베이스 파일: data/fitness.db")
        print("🔥 이제 'python main.py' 명령으로 서버를 시작할 수 있습니다!")
        
    except Exception as e:
        print(f"\n❌ 데이터베이스 초기화 중 오류 발생: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()
