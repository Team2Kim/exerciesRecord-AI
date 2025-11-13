"""
ExRecAI - 운동 추천 AI 시스템
FastAPI 메인 서버 애플리케이션
"""

import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로컬 모듈 임포트
from services.openai_service import openai_service
from services.mysql_service import MySQLService


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


# ==================== 운동 데이터 관리 API ====================

class ExerciseUpdateRequest(BaseModel):
    title: str = None
    standard_title: str = None
    video_url: str = None
    image_url: str = None
    image_file_name: str = None


@app.get("/api/muscles")
async def get_muscles():
    """근육 목록 조회"""
    try:
        mysql_service = MySQLService()
        muscles = mysql_service.get_muscles()
        mysql_service.close()
        return {
            "success": True,
            "muscles": muscles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"근육 목록 조회 중 오류: {str(e)}")


@app.get("/api/exercises")
async def get_exercises(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: str = Query(None, description="검색어 (제목 또는 표준 제목)")
):
    """운동 목록 조회 (페이지네이션)"""
    try:
        mysql_service = MySQLService()
        result = mysql_service.get_exercises(
            page=page,
            page_size=page_size,
            search=search
        )
        mysql_service.close()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"운동 목록 조회 중 오류: {str(e)}")


@app.get("/api/exercises/{exercise_id}")
async def get_exercise(exercise_id: int):
    """특정 운동 조회"""
    try:
        mysql_service = MySQLService()
        exercise = mysql_service.get_exercise_by_id(exercise_id)
        mysql_service.close()
        
        if not exercise:
            raise HTTPException(status_code=404, detail="운동을 찾을 수 없습니다")
        
            return {
                "success": True,
                "exercise": exercise
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"운동 조회 중 오류: {str(e)}")


@app.put("/api/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    update_data: ExerciseUpdateRequest
):
    """운동 정보 업데이트"""
    try:
        mysql_service = MySQLService()
        
        # 업데이트할 데이터만 추출
        update_dict = update_data.dict(exclude_none=True)
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="업데이트할 데이터가 없습니다")
        
        success = mysql_service.update_exercise(
            exercise_id=exercise_id,
            **update_dict
        )
        mysql_service.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="운동을 찾을 수 없거나 업데이트에 실패했습니다")
        
        return {
                "success": True,
                "message": "운동 정보가 성공적으로 업데이트되었습니다",
                "exercise_id": exercise_id
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"운동 업데이트 중 오류: {str(e)}")


@app.get("/admin/exercises", response_class=HTMLResponse)
async def exercise_admin_page():
    """운동 데이터 관리 페이지"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>운동 데이터 관리</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .search-bar {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .search-bar input {
            width: 100%;
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-bar input:focus {
            border-color: #667eea;
        }
        
        .exercises-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 20px 30px;
        }
        
        .exercise-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 15px 20px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 20px;
            position: relative;
        }
        
        .exercise-card:hover:not(.editing) {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .exercise-card.editing {
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
        }
        
        .exercise-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .play-video-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .play-video-btn:hover {
            background: #218838;
            transform: scale(1.05);
        }
        
        .edit-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .edit-btn:hover {
            background: #5568d3;
            transform: scale(1.05);
        }
        
        .exercise-thumbnail {
            width: 120px;
            height: 80px;
            object-fit: cover;
            border-radius: 8px;
            background: #f8f9fa;
            flex-shrink: 0;
        }
        
        .exercise-info {
            flex: 1;
            min-width: 0;
        }
        
        .edit-mode {
            width: 100%;
        }
        
        .exercise-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .exercise-standard-title {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .exercise-muscles {
            font-size: 0.8em;
            color: #667eea;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .exercise-id {
            font-size: 0.75em;
            color: #999;
        }
        
        .pagination {
            padding: 20px 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            border-top: 1px solid #dee2e6;
        }
        
        .pagination button {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .pagination button:hover:not(:disabled) {
            background: #667eea;
            color: white;
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pagination-input {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pagination-input input {
            width: 60px;
            padding: 8px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            font-weight: bold;
        }
        
        .pagination-input input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .pagination-input span {
            color: #666;
            font-size: 14px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            overflow-y: auto;
        }
        
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
        }
        
        .video-modal-content {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 1000px;
            width: 100%;
            position: relative;
        }
        
        .video-player {
            width: 100%;
            max-height: 70vh;
            border-radius: 10px;
            background: #000;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .modal-header h2 {
            color: #333;
            font-size: 2em;
        }
        
        .close-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.2em;
            transition: background 0.3s;
        }
        
        .close-btn:hover {
            background: #c82333;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .thumbnail-preview {
            width: 100%;
            max-height: 300px;
            object-fit: contain;
            border-radius: 10px;
            margin-top: 10px;
            background: #f8f9fa;
        }
        
        .form-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 30px;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: bold;
            z-index: 2000;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .toast.success {
            background: #28a745;
            color: white;
        }
        
        .toast.error {
            background: #dc3545;
            color: white;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏋️ 운동 데이터 관리</h1>
            <p>운동 정보를 수정하고 관리하세요</p>
        </div>
        
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="운동 제목으로 검색...">
        </div>
        
        <div id="exercisesContainer" class="exercises-list">
            <div class="loading">로딩 중...</div>
        </div>
        
        <div class="pagination" id="pagination"></div>
    </div>
    
    <!-- 영상 모달 -->
    <div id="videoModal" class="modal">
        <div class="video-modal-content">
            <div class="modal-header">
                <h2 id="videoTitle">영상 재생</h2>
                <button class="close-btn" onclick="closeVideoModal()">✕</button>
            </div>
            <video id="videoPlayer" class="video-player" controls>
                <source id="videoSource" src="" type="video/mp4">
                브라우저가 비디오 태그를 지원하지 않습니다.
            </video>
        </div>
    </div>
    
    <script>
        const API_BASE = window.location.origin;
        let currentPage = 1;
        let currentSearch = '';
        
        // 페이지 로드 시 운동 목록 가져오기
        document.addEventListener('DOMContentLoaded', () => {
            loadExercises();
            
            // 검색 입력 이벤트
            document.getElementById('searchInput').addEventListener('input', (e) => {
                currentSearch = e.target.value;
                currentPage = 1;
                loadExercises();
            });
        });
        
        async function loadExercises() {
            const container = document.getElementById('exercisesContainer');
            container.innerHTML = '<div class="loading">로딩 중...</div>';
            
            try {
                const params = new URLSearchParams({
                    page: currentPage,
                    page_size: 20
                });
                
                if (currentSearch) {
                    params.append('search', currentSearch);
                }
                
                const response = await fetch(`${API_BASE}/api/exercises?${params}`);
                const data = await response.json();
                
                if (data.success) {
                    displayExercises(data.exercises);
                    displayPagination(data.page, data.total_pages);
                } else {
                    container.innerHTML = '<div class="error">운동 목록을 불러올 수 없습니다.</div>';
                }
            } catch (error) {
                container.innerHTML = `<div class="error">오류 발생: ${error.message}</div>`;
            }
        }
        
        function displayExercises(exercises) {
            const container = document.getElementById('exercisesContainer');
            
            if (exercises.length === 0) {
                container.innerHTML = '<div class="loading">운동 데이터가 없습니다.</div>';
                return;
            }
            
            container.innerHTML = exercises.map(ex => {
                const thumbnailUrl = ex.image_url && ex.image_file_name 
                    ? `${ex.image_url}${ex.image_file_name}` 
                    : 'https://via.placeholder.com/120x80?text=No+Image';
                
                const hasVideo = ex.video_url && ex.video_url.trim() !== '';
                const videoUrlEscaped = (ex.video_url || '').replace(/'/g, "\\'");
                const titleEscaped = (ex.title || '').replace(/'/g, "\\'");
                
                return `
                    <div class="exercise-card" id="card-${ex.exercise_id}" data-exercise-id="${ex.exercise_id}">
                        <img src="${thumbnailUrl}" alt="${ex.title}" class="exercise-thumbnail" 
                             onerror="this.src='https://via.placeholder.com/120x80?text=No+Image'">
                        <div class="exercise-info" style="flex: 1;">
                            <div id="view-mode-${ex.exercise_id}">
                                <div class="exercise-title">${ex.title || '제목 없음'}</div>
                                <div class="exercise-standard-title">${ex.standard_title || '표준 제목 없음'}</div>
                                <div class="exercise-id">ID: ${ex.exercise_id}</div>
                            </div>
                            <div id="edit-mode-${ex.exercise_id}" class="edit-mode" style="display: none;">
                                <label class="inline-edit-label">제목 (Title)</label>
                                <input type="text" class="inline-edit-input" id="edit-title-${ex.exercise_id}" 
                                       value="${(ex.title || '').replace(/"/g, '&quot;')}" placeholder="제목">
                                
                                <label class="inline-edit-label">표준 제목 (Standard Title)</label>
                                <input type="text" class="inline-edit-input" id="edit-standard-title-${ex.exercise_id}" 
                                       value="${(ex.standard_title || '').replace(/"/g, '&quot;')}" placeholder="표준 제목">
                                
                                <label class="inline-edit-label">영상 링크 (Video URL)</label>
                                <input type="url" class="inline-edit-input" id="edit-video-url-${ex.exercise_id}" 
                                       value="${(ex.video_url || '').replace(/"/g, '&quot;')}" placeholder="https://...">
                                
                                <label class="inline-edit-label">이미지 URL (Image URL)</label>
                                <input type="url" class="inline-edit-input" id="edit-image-url-${ex.exercise_id}" 
                                       value="${(ex.image_url || '').replace(/"/g, '&quot;')}" placeholder="https://...">
                                
                                <label class="inline-edit-label">이미지 파일명 (Image File Name)</label>
                                <input type="text" class="inline-edit-input" id="edit-image-filename-${ex.exercise_id}" 
                                       value="${(ex.image_file_name || '').replace(/"/g, '&quot;')}" placeholder="image.jpg">
                                
                                <div class="edit-actions">
                                    <button class="save-btn" onclick="saveExercise(${ex.exercise_id})">💾 저장</button>
                                    <button class="cancel-btn" onclick="cancelEdit(${ex.exercise_id})">❌ 취소</button>
                                </div>
                            </div>
                        </div>
                        <div class="exercise-actions" id="actions-${ex.exercise_id}">
                            ${hasVideo ? `
                                <button class="play-video-btn" onclick="event.stopPropagation(); openVideoModal('${videoUrlEscaped}', '${titleEscaped}')">
                                    ▶ 영상 보기
                                </button>
                            ` : ''}
                            <button class="edit-btn" onclick="event.stopPropagation(); startEdit(${ex.exercise_id})">
                                ✏️ 수정
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function displayPagination(current, total) {
            const pagination = document.getElementById('pagination');
            
            if (total <= 1) {
                pagination.innerHTML = '';
                return;
            }
            
            let html = `
                <button onclick="changePage(${current - 1})" ${current === 1 ? 'disabled' : ''}>
                    이전
                </button>
                <div class="pagination-input">
                    <span>페이지</span>
                    <input type="number" id="pageInput" min="1" max="${total}" value="${current}" 
                           onkeypress="if(event.key==='Enter') goToPage()">
                    <span>/ ${total}</span>
                </div>
                <button onclick="changePage(${current + 1})" ${current === total ? 'disabled' : ''}>
                    다음
                </button>
            `;
            
            pagination.innerHTML = html;
        }
        
        function changePage(page) {
            if (page < 1) return;
            const totalPages = document.getElementById('pagination')?.querySelector('.pagination-input span:last-child')?.textContent;
            if (totalPages) {
                const total = parseInt(totalPages.replace('/', '').trim());
                if (page > total) return;
            }
            currentPage = page;
            loadExercises();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        function goToPage() {
            const input = document.getElementById('pageInput');
            if (input) {
                const page = parseInt(input.value);
                if (page && page >= 1) {
                    changePage(page);
                }
            }
        }
        
        // 원래 데이터 저장용
        let originalData = {};
        
        function startEdit(exerciseId) {
            const card = document.getElementById(`card-${exerciseId}`);
            const viewMode = document.getElementById(`view-mode-${exerciseId}`);
            const editMode = document.getElementById(`edit-mode-${exerciseId}`);
            const actions = document.getElementById(`actions-${exerciseId}`);
            
            // 현재 데이터 저장
            const titleInput = document.getElementById(`edit-title-${exerciseId}`);
            const standardTitleInput = document.getElementById(`edit-standard-title-${exerciseId}`);
            const videoUrlInput = document.getElementById(`edit-video-url-${exerciseId}`);
            const imageUrlInput = document.getElementById(`edit-image-url-${exerciseId}`);
            const imageFileNameInput = document.getElementById(`edit-image-filename-${exerciseId}`);
            
            originalData[exerciseId] = {
                title: titleInput.value,
                standardTitle: standardTitleInput.value,
                videoUrl: videoUrlInput.value,
                imageUrl: imageUrlInput.value,
                imageFileName: imageFileNameInput.value
            };
            
            card.classList.add('editing');
            viewMode.style.display = 'none';
            editMode.style.display = 'block';
            actions.style.display = 'none';
        }
        
        function cancelEdit(exerciseId) {
            const card = document.getElementById(`card-${exerciseId}`);
            const viewMode = document.getElementById(`view-mode-${exerciseId}`);
            const editMode = document.getElementById(`edit-mode-${exerciseId}`);
            const actions = document.getElementById(`actions-${exerciseId}`);
            
            // 원래 데이터로 복원
            if (originalData[exerciseId]) {
                const data = originalData[exerciseId];
                document.getElementById(`edit-title-${exerciseId}`).value = data.title;
                document.getElementById(`edit-standard-title-${exerciseId}`).value = data.standardTitle;
                document.getElementById(`edit-video-url-${exerciseId}`).value = data.videoUrl;
                document.getElementById(`edit-image-url-${exerciseId}`).value = data.imageUrl;
                document.getElementById(`edit-image-filename-${exerciseId}`).value = data.imageFileName;
                delete originalData[exerciseId];
            }
            
            card.classList.remove('editing');
            viewMode.style.display = 'block';
            editMode.style.display = 'none';
            actions.style.display = 'flex';
        }
        
        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 300);
            }, 3000);
        }
        
        async function saveExercise(exerciseId) {
            const title = document.getElementById(`edit-title-${exerciseId}`).value;
            const standardTitle = document.getElementById(`edit-standard-title-${exerciseId}`).value;
            const videoUrl = document.getElementById(`edit-video-url-${exerciseId}`).value;
            const imageUrl = document.getElementById(`edit-image-url-${exerciseId}`).value;
            const imageFileName = document.getElementById(`edit-image-filename-${exerciseId}`).value;
            
            const updateData = {
                title: title || null,
                standard_title: standardTitle || null,
                video_url: videoUrl || null,
                image_url: imageUrl || null,
                image_file_name: imageFileName || null
            };
            
            // null 값 제거
            Object.keys(updateData).forEach(key => {
                if (updateData[key] === null || updateData[key] === '') {
                    delete updateData[key];
                }
            });
            
            if (Object.keys(updateData).length === 0) {
                showToast('수정할 내용이 없습니다.', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/exercises/${exerciseId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(updateData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // 화면만 업데이트 (리로드 없이)
                    updateExerciseCard(exerciseId, {
                        title: title,
                        standard_title: standardTitle,
                        video_url: videoUrl,
                        image_url: imageUrl,
                        image_file_name: imageFileName
                    });
                    
                    // 편집 모드 종료
                    const card = document.getElementById(`card-${exerciseId}`);
                    const viewMode = document.getElementById(`view-mode-${exerciseId}`);
                    const editMode = document.getElementById(`edit-mode-${exerciseId}`);
                    const actions = document.getElementById(`actions-${exerciseId}`);
                    
                    card.classList.remove('editing');
                    viewMode.style.display = 'block';
                    editMode.style.display = 'none';
                    actions.style.display = 'flex';
                    
                    // 원래 데이터 삭제
                    delete originalData[exerciseId];
                    
                    showToast('✅ 저장되었습니다!', 'success');
                } else {
                    showToast(`❌ 저장 실패: ${data.detail || '알 수 없는 오류'}`, 'error');
                }
            } catch (error) {
                showToast(`❌ 오류 발생: ${error.message}`, 'error');
            }
        }
        
        function updateExerciseCard(exerciseId, data) {
            const viewMode = document.getElementById(`view-mode-${exerciseId}`);
            const card = document.getElementById(`card-${exerciseId}`);
            
            // 제목 업데이트
            const titleElement = viewMode.querySelector('.exercise-title');
            if (titleElement) {
                titleElement.textContent = data.title || '제목 없음';
            }
            
            // 표준 제목 업데이트
            const standardTitleElement = viewMode.querySelector('.exercise-standard-title');
            if (standardTitleElement) {
                standardTitleElement.textContent = data.standard_title || '표준 제목 없음';
            }
            
            // 썸네일 업데이트
            const thumbnail = card.querySelector('.exercise-thumbnail');
            if (data.image_url && data.image_file_name) {
                thumbnail.src = `${data.image_url}${data.image_file_name}`;
            }
            
            // 영상 버튼 업데이트
            const actions = document.getElementById(`actions-${exerciseId}`);
            const hasVideo = data.video_url && data.video_url.trim() !== '';
            const videoUrlEscaped = (data.video_url || '').replace(/'/g, "\\'");
            const titleEscaped = (data.title || '').replace(/'/g, "\\'");
            
            let playBtn = actions.querySelector('.play-video-btn');
            
            if (hasVideo) {
                if (!playBtn) {
                    // 영상 버튼이 없으면 추가
                    playBtn = document.createElement('button');
                    playBtn.className = 'play-video-btn';
                    playBtn.innerHTML = '▶ 영상 보기';
                    actions.insertBefore(playBtn, actions.querySelector('.edit-btn'));
                }
                // onclick 핸들러 업데이트
                playBtn.onclick = (e) => {
                    e.stopPropagation();
                    openVideoModal(videoUrlEscaped, titleEscaped);
                };
            } else {
                // 영상 버튼 제거
                if (playBtn) {
                    playBtn.remove();
                }
            }
            
            // 편집 모드의 입력 필드도 업데이트 (다음 편집을 위해)
            const editTitleInput = document.getElementById(`edit-title-${exerciseId}`);
            const editStandardTitleInput = document.getElementById(`edit-standard-title-${exerciseId}`);
            const editVideoUrlInput = document.getElementById(`edit-video-url-${exerciseId}`);
            const editImageUrlInput = document.getElementById(`edit-image-url-${exerciseId}`);
            const editImageFileNameInput = document.getElementById(`edit-image-filename-${exerciseId}`);
            
            if (editTitleInput) editTitleInput.value = data.title || '';
            if (editStandardTitleInput) editStandardTitleInput.value = data.standard_title || '';
            if (editVideoUrlInput) editVideoUrlInput.value = data.video_url || '';
            if (editImageUrlInput) editImageUrlInput.value = data.image_url || '';
            if (editImageFileNameInput) editImageFileNameInput.value = data.image_file_name || '';
        }
        
        function openVideoModal(videoUrl, title) {
            const modal = document.getElementById('videoModal');
            const videoPlayer = document.getElementById('videoPlayer');
            const videoSource = document.getElementById('videoSource');
            const videoTitle = document.getElementById('videoTitle');
            
            videoTitle.textContent = title || '영상 재생';
            videoSource.src = videoUrl;
            videoPlayer.load();
            modal.classList.add('active');
        }
        
        function closeVideoModal() {
            const modal = document.getElementById('videoModal');
            const videoPlayer = document.getElementById('videoPlayer');
            videoPlayer.pause();
            videoPlayer.currentTime = 0;
            modal.classList.remove('active');
        }
        
        
        document.getElementById('videoModal').addEventListener('click', (e) => {
            if (e.target.id === 'videoModal') {
                closeVideoModal();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/workout-log/weekly-pattern")
async def analyze_weekly_workout_pattern(
    payload: Dict[str, Any],
    model: str = Query(default="gpt-4o-mini", description="사용할 OpenAI 모델")
):
    """
    최근 7일간의 운동 데이터를 분석하여 패턴과 루틴을 추천합니다.
    
    - **payload.weekly_logs**: 최근 7일 운동 일지 리스트 (최신순/과거순 무관)
    - **model**: OpenAI 모델 (기본: gpt-4o-mini)
    
    Returns:
    - AI 패턴 분석 및 추천 루틴
    """

    weekly_logs: List[Dict[str, Any]] = payload.get("weekly_logs") or payload.get("logs")

    if not isinstance(weekly_logs, list) or not weekly_logs:
        raise HTTPException(
            status_code=400,
            detail="최근 7일 운동 기록(weekly_logs)이 필요합니다."
        )

    trimmed_logs = weekly_logs[:7]

    ai_result = openai_service.analyze_weekly_pattern_and_recommend(trimmed_logs, model=model)

    if not ai_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=ai_result.get("message", "AI 패턴 분석 실패")
        )

    return {
        "success": True,
        "ai_pattern": ai_result.get("result"),
        "metrics_summary": ai_result.get("metrics_summary"),
        "rag_sources": ai_result.get("rag_sources", []),
        "model": ai_result.get("model"),
        "records_analyzed": len(trimmed_logs)
    }


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