import mysql.connector
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional
from mysql.connector import Error

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

RAG_EXERCISE_COLUMNS: List[str] = [
    "exercise_id",
    "title",
    "standard_title",
    "training_name",
    "body_part",
    "exercise_tool",
    "fitness_factor_name",
    "fitness_level_name",
    "target_group",
    "training_aim_name",
    "training_place_name",
    "training_section_name",
    "training_step_name",
    "description",
    "image_url",
    "video_url",
    "muscles",
    "video_length_seconds",
    "image_file_name",
]

class MySQLService:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=int(MYSQL_PORT) if MYSQL_PORT else 3306,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                charset='utf8mb4'
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except Error as e:
            print(f"MySQL 연결 오류: {e}")
            raise
        
    def get_muscles(self):
        """근육 목록 조회"""
        try:
            query = "SELECT distinct(name) FROM muscle"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"근육 목록 조회 오류: {e}")
            return []
    
    def get_exercises(
        self, 
        page: int = 1, 
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """운동 목록 조회 (페이지네이션)"""
        try:
            offset = (page - 1) * page_size
            
            # 검색 조건
            where_clause = ""
            params = []
            if search:
                where_clause = "WHERE e.title LIKE %s OR e.standard_title LIKE %s"
                params = [f"%{search}%", f"%{search}%"]
            
            # 전체 개수 조회
            count_query = f"SELECT COUNT(*) as total FROM exercise e {where_clause}"
            self.cursor.execute(count_query, params)
            total = self.cursor.fetchone()['total']
            
            # 목록 조회 (exercise 테이블에서 조회)
            query = f"""
                SELECT 
                    e.exercise_id,
                    e.title,
                    e.standard_title,
                    e.video_url,
                    e.image_url,
                    e.image_file_name,
                    e.description
                FROM exercise e
                {where_clause}
                ORDER BY e.exercise_id ASC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])
            self.cursor.execute(query, params)
            exercises = self.cursor.fetchall()
            
            return {
                "exercises": exercises,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Error as e:
            print(f"운동 목록 조회 오류: {e}")
            return {
                "exercises": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_exercise_by_id(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        """특정 운동 조회"""
        try:
            query = """
                SELECT 
                    exercise_id,
                    title,
                    standard_title,
                    video_url,
                    image_url,
                    image_file_name,
                    description
                FROM exercise 
                WHERE exercise_id = %s
            """
            self.cursor.execute(query, (exercise_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"운동 조회 오류: {e}")
            return None
    
    def update_exercise(
        self,
        exercise_id: int,
        title: Optional[str] = None,
        standard_title: Optional[str] = None,
        video_url: Optional[str] = None,
        image_url: Optional[str] = None,
        image_file_name: Optional[str] = None
    ) -> bool:
        """운동 정보 업데이트"""
        try:
            # 업데이트할 필드만 동적으로 구성
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if standard_title is not None:
                updates.append("standard_title = %s")
                params.append(standard_title)
            
            if video_url is not None:
                updates.append("video_url = %s")
                params.append(video_url)
            
            if image_url is not None:
                updates.append("image_url = %s")
                params.append(image_url)
            
            if image_file_name is not None:
                updates.append("image_file_name = %s")
                params.append(image_file_name)
            
            if not updates:
                return False
            
            params.append(exercise_id)
            query = f"""
                UPDATE exercise 
                SET {', '.join(updates)}
                WHERE exercise_id = %s
            """
            
            self.cursor.execute(query, params)
            self.conn.commit()
            
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"운동 업데이트 오류: {e}")
            self.conn.rollback()
            return False
    
    def fetch_exercises_for_rag(self) -> List[Dict[str, Any]]:
        """
        RAG 임베딩에 사용할 운동 메타데이터 전체 조회
        
        Returns:
            List[Dict[str, Any]]: TEXT_FIELDS 및 메타데이터 필드를 포함한 운동 정보
        """
        try:
            column_clause = ", ".join(RAG_EXERCISE_COLUMNS)
            query = f"""
                SELECT {column_clause}
                FROM ex_muscles
                ORDER BY exercise_id ASC
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall() or []
            
            normalized: List[Dict[str, Any]] = []
            for row in rows:
                normalized.append(
                    {
                        column: (row.get(column, "") if isinstance(row, dict) else "")
                        for column in RAG_EXERCISE_COLUMNS
                    }
                )
            return normalized
        except Error as e:
            print(f"RAG용 운동 데이터 조회 오류: {e}")
            return []
    
    def close(self):
        """연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
