"""
외부 운동 영상 API 연동 서비스
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json


class ExternalExerciseAPI:
    """외부 운동 영상 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "http://52.54.123.236:8080/api/exercises"
        self.journals_base_url = "http://52.54.123.236:8080/api/journals"
        self.timeout = 30.0
        
        # 캐시 관리
        self._cache = {}
        self._cache_expiry = {}
        self.cache_duration = timedelta(hours=1)  # 1시간 캐시


    async def search_exercises(
        self,
        keyword: Optional[str] = None,
        target_group: Optional[str] = None,
        fitness_factor_name: Optional[str] = None,
        exercise_tool: Optional[str] = None,
        page: int = 0,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        다중 조건으로 운동 영상 검색
        
        Args:
            keyword: 제목 검색어
            target_group: 대상 그룹 (유소년, 성인 등)
            fitness_factor_name: 체력 요인 (근력 등)
            exercise_tool: 운동 도구 (맨몸, 밴드 등)
            page: 페이지 번호 (0부터 시작)
            size: 페이지 크기
            
        Returns:
            페이징된 운동 영상 데이터
        """
        
        # 캐시 키 생성
        cache_key = f"search_{keyword}_{target_group}_{fitness_factor_name}_{exercise_tool}_{page}_{size}"
        
        # 캐시 확인
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        # 쿼리 파라미터 구성
        params = {
            "page": page,
            "size": size
        }
        
        if keyword:
            params["keyword"] = keyword
        if target_group:
            params["targetGroup"] = target_group
        if fitness_factor_name:
            params["fitnessFactorName"] = fitness_factor_name
        if exercise_tool:
            params["exerciseTool"] = exercise_tool
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 캐시에 저장
                self._cache[cache_key] = data
                self._cache_expiry[cache_key] = datetime.now() + self.cache_duration
                
                return data
                
        except httpx.HTTPError as e:
            print(f"외부 API 호출 실패: {e}")
            return {
                "content": [],
                "totalPages": 0,
                "totalElements": 0,
                "error": str(e)
            }


    async def search_by_muscle(
        self,
        muscles: List[str],
        page: int = 0,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        근육 부위별 운동 영상 검색
        
        Args:
            muscles: 근육 이름 목록
            page: 페이지 번호
            size: 페이지 크기
            
        Returns:
            페이징된 운동 영상 데이터
        """
        
        # 캐시 키 생성
        cache_key = f"muscle_{'_'.join(sorted(muscles))}_{page}_{size}"
        
        # 캐시 확인
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        # 쿼리 파라미터 구성
        params = {
            "page": page,
            "size": size,
        }
        
        # 근육 목록을 쿼리 파라미터로 추가
        muscle_params = []
        for muscle in muscles:
            muscle_params.append(("muscles", muscle))
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 근육 파라미터를 직접 URL에 추가
                url = f"{self.base_url}/by-muscle"
                response = await client.get(url, params=params + muscle_params)
                response.raise_for_status()
                
                data = response.json()
                
                # 캐시에 저장
                self._cache[cache_key] = data
                self._cache_expiry[cache_key] = datetime.now() + self.cache_duration
                
                return data
                
        except httpx.HTTPError as e:
            print(f"근육별 검색 API 호출 실패: {e}")
            return {
                "content": [],
                "totalPages": 0,
                "totalElements": 0,
                "error": str(e)
            }


    def _is_cached(self, cache_key: str) -> bool:
        """캐시 유효성 확인"""
        if cache_key not in self._cache:
            return False
            
        if cache_key not in self._cache_expiry:
            return False
            
        return datetime.now() < self._cache_expiry[cache_key]


    async def get_daily_log_by_date(
        self,
        date: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        특정 날짜의 운동 일지 조회 (외부 API)
        
        Args:
            date: 조회할 날짜 (형식: yyyy-MM-dd)
            access_token: 인증 토큰 (Bearer 토큰)
            
        Returns:
            운동 일지 데이터 (DailyLogResponseDto)
        """
        
        try:
            # Authorization 헤더 구성
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # 쿼리 파라미터 구성
            params = {
                "date": date
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.journals_base_url}/by-date"
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "date": date
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "success": False,
                    "error": "해당 날짜에 작성된 일지가 없습니다",
                    "status_code": 404,
                    "date": date
                }
            elif e.response.status_code == 401:
                return {
                    "success": False,
                    "error": "인증이 필요합니다. 유효한 토큰을 제공해주세요",
                    "status_code": 401,
                    "date": date
                }
            else:
                return {
                    "success": False,
                    "error": f"API 호출 실패: {str(e)}",
                    "status_code": e.response.status_code,
                    "date": date
                }
        except httpx.HTTPError as e:
            print(f"운동 일지 조회 API 호출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "date": date
            }


    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self._cache_expiry.clear()


    async def get_exercise_recommendations_with_videos(
        self,
        body_parts: List[str],
        target_group: str = "성인",
        exercise_tool: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        운동 부위에 맞는 영상 추천
        
        Args:
            body_parts: 운동 부위 목록
            target_group: 대상 그룹
            exercise_tool: 선호 운동 도구
            limit: 최대 추천 개수
            
        Returns:
            추천 운동 영상 목록
        """
        
        all_exercises = []
        
        # 각 부위별로 검색
        for body_part in body_parts:
            try:
                # 부위를 키워드로 검색
                result = await self.search_exercises(
                    keyword=body_part,
                    target_group=target_group,
                    exercise_tool=exercise_tool,
                    size=limit
                )
                
                if result.get("content"):
                    all_exercises.extend(result["content"])
                    
            except Exception as e:
                print(f"부위 '{body_part}' 검색 중 오류: {e}")
                continue
        
        # 중복 제거 (exerciseId 기준)
        seen_ids = set()
        unique_exercises = []
        for exercise in all_exercises:
            if exercise.get("exerciseId") not in seen_ids:
                seen_ids.add(exercise.get("exerciseId"))
                unique_exercises.append(exercise)
        
        # 제한 개수만큼 반환
        return unique_exercises[:limit]


    async def enhance_recommendation_with_videos(
        self,
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        기존 추천에 운동 영상 정보 추가
        
        Args:
            recommendation: 기존 추천 결과
            
        Returns:
            영상 정보가 추가된 추천 결과
        """
        
        enhanced_recommendation = recommendation.copy()
        
        # 각 일별 추천에 영상 정보 추가
        for day_key, day_data in enhanced_recommendation.get("recommendation", {}).items():
            enhanced_exercises = []
            
            for exercise in day_data.get("exercises", []):
                enhanced_exercise = exercise.copy()
                
                # 운동 이름으로 영상 검색
                try:
                    video_result = await self.search_exercises(
                        keyword=exercise.get("name", ""),
                        size=1
                    )
                    
                    if video_result.get("content"):
                        video_data = video_result["content"][0]
                        enhanced_exercise.update({
                            "video_url": video_data.get("videoUrl"),
                            "video_id": video_data.get("exerciseId"),
                            "image_url": video_data.get("imageUrl"),
                            "video_length": video_data.get("videoLengthSeconds"),
                            "target_group": video_data.get("targetGroup"),
                            "fitness_factor": video_data.get("fitnessFactorName")
                        })
                        
                except Exception as e:
                    print(f"운동 '{exercise.get('name')}' 영상 검색 중 오류: {e}")
                
                enhanced_exercises.append(enhanced_exercise)
            
            # 업데이트된 운동 목록으로 교체
            enhanced_recommendation["recommendation"][day_key]["exercises"] = enhanced_exercises
        
        return enhanced_recommendation


    async def get_popular_exercises(
        self,
        target_group: str = "성인",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        인기 운동 영상 조회
        
        Args:
            target_group: 대상 그룹
            limit: 최대 개수
            
        Returns:
            인기 운동 영상 목록
        """
        
        try:
            result = await self.search_exercises(
                target_group=target_group,
                size=limit
            )
            
            return result.get("content", [])
            
        except Exception as e:
            print(f"인기 운동 조회 중 오류: {e}")
            return []


# 전역 인스턴스
external_api = ExternalExerciseAPI()

