from fastapi import APIRouter, Depends, UploadFile
from psycopg2.extras import RealDictCursor
from app.session import get_db
from pydantic import BaseModel
from app.settings import Settings
import pathlib
from fastapi.responses import StreamingResponse, FileResponse, Response
from app.file_handler import FileHandler

from app.api.endpoints.get_submission import get_submission
setting=Settings()
api_router = APIRouter()

class Evaluation:
    grade: int
    comment: str

@api_router.get('/submission/get')
async def get_submission(id: int, cursor: RealDictCursor = Depends(get_db)):
    cursor.execute("""
            SELECT * from public.submission s where s.moodle_sub_id=%s
    """, [id])
    sub = cursor.fetchone()
    cursor.execute("""
            SELECT * from public.evaluation e where e.submission_id=%s
    """, [id])
    ev=cursor.fetchall()
    sub['evaluations'] = ev
    return sub

class Submission(BaseModel):
    moodle_submision_id: int
    status: str
    time_created: str
    file_links: list[str]

def handle_files(filelinks: list[str]):
    pass


@api_router.post('/submission/postnew')
async def post_submission(submission: Submission, cursor: RealDictCursor = Depends(get_db)):
    res = cursor.execute("""
            INSERT into public.submission values(%s,%s,%s)
    """, [submission.moodle_submision_id, submission.status, submission.time_created])

    return res

@api_router.post("/submission/uploadfiles")
async def create_upload_files(submission_id, files: list[UploadFile], file_handler: FileHandler = Depends(FileHandler), cursor: RealDictCursor = Depends(get_db)):
    fi: list[dict] = []
    for f in files:
        res=await file_handler.store_file(f, submission_id)
        fi.append(res)
    return fi


@api_router.get("/submission/getfiles")
async def create_upload_files(submission_id, file_handler: FileHandler = Depends(FileHandler)) -> FileResponse:
    file=await file_handler.get_file(submission_id)
    headers = {"content-disposition": "attachment; filename=submission_nr_{}.zip".format(submission_id)}
    return StreamingResponse(gen(file), media_type='application/zip', headers=headers)

def gen(file: bytes):
    yield file


class EvaluationBody(BaseModel):
    comment: str
    grade: int

@api_router.post("/evaluation/evaluate")
async def create_upload_files(submission_id, body: EvaluationBody, cursor: RealDictCursor = Depends(get_db)):
    cursor.execute(
        "INSERT INTO public.evaluation(submission_id,grade,comment) values(%s, %s, %s)", 
        (submission_id, body.grade, body.comment))
    return 1

    