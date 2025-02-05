from fastapi import APIRouter, Depends, UploadFile
from psycopg2.extras import RealDictCursor
from app.session import get_db
from pydantic import BaseModel
from app.settings import Settings
import pathlib
from fastapi.responses import StreamingResponse, FileResponse, Response
from app.file_handler import FileHandler
import requests

setting=Settings()
api_router = APIRouter()
file_handler: FileHandler = FileHandler()

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
    class FileSubmit(BaseModel):
        file_name: str
        file_url: str
        mime_type: str
    moodle_submision_id: int
    status: str
    time_created: str
    file_links: list[FileSubmit]

async def handle_files(filelinks: list[Submission.FileSubmit], submission_id: int):
    for link in filelinks:
        res=requests.get("http://localhost:8000/submission/moodle/download_file",
                     {"file_name": link.file_name, "file_url": link.file_url, "mime_type": link.mime_type})
        await file_handler.store_binary_file(res.content, link.file_name, link.mime_type, submission_id)
    pass


@api_router.post('/submission/postnew')
async def post_submission(submission: Submission, cursor: RealDictCursor = Depends(get_db)):
    await handle_files(submission.file_links, submission.moodle_submision_id)
    res = cursor.execute("""
            INSERT into public.submission(moodle_sub_id,status,time_created) values(%s,%s,%s)
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

    