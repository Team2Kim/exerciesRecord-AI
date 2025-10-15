"""
데이터베이스 초기화 스크립트
테이블을 생성하고 샘플 데이터를 삽입합니다.
"""

import json
import os
from sqlalchemy.orm import Session
from models.database import engine, SessionLocal, create_tables
from models.database import Exercise, UserGoal, WorkoutPlan, WorkoutSession, WorkoutExercise, UserFeedback


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
    
    print(f"운동 데이터: {exercise_count}개")
    print(f"사용자 목표: {goal_count}개")
    print(f"운동 계획: {plan_count}개")
    print(f"운동 세션: {session_count}개")
    print(f"계획별 운동: {workout_exercise_count}개")
    print(f"사용자 피드백: {feedback_count}개")
    
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
        
        # 6. 데이터베이스 확인
        print("\n5️⃣ 데이터베이스 확인...")
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
