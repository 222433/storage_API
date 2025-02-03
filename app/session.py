from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, status
from app.settings import Settings

settings = Settings()

def get_db_connection():
    """Create a new database connection"""
    try:
        return psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            cursor_factory=RealDictCursor
        )
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )


@contextmanager
def get_db_cursor(commit=True):
    """Context manager for database cursor"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()



def get_db():
    """Dependency for FastAPI endpoints"""
    with get_db_cursor(commit=True) as cursor:
        yield cursor