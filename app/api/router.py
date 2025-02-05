from fastapi import APIRouter, Depends, UploadFile
from psycopg2.extras import RealDictCursor
from app.session import get_db
from pydantic import BaseModel
from app.settings import Settings
import pathlib
from fastapi.responses import StreamingResponse, FileResponse, Response
from app.file_handler import FileHandler
import requests
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
engine = create_engine("postgresql://rootDB:root1234@localhost:5455/uni_db")
setting=Settings()
api_router = APIRouter()
file_handler: FileHandler = FileHandler()

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


''''''
class Submission(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    moodle_sub_id: int
    time_created: str
    assignment_id: Optional[int] = None

class Evaluation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    grade: int
    comment: str
    submission_id: int = Field(foreign_key="submission.id")


@api_router.get('/submission/getbyassignment')
async def get_submission(assignment: int, cursor: RealDictCursor = Depends(get_db)):
    with Session(engine) as session:
        statement = select(Submission).where(Submission.assignment_id == assignment)
        res = session.exec(statement).fetchall()
        #return res
        print()
    return res

''''''

class Submission2(BaseModel):
    class FileSubmit(BaseModel):
        file_name: str
        file_url: str
        mime_type: str
    moodle_submision_id: int
    time_created: str
    assignment_id: int
    file_links: list[FileSubmit]

async def handle_files(filelinks: list[Submission2.FileSubmit], submission_id: int):
    for link in filelinks:
        res=requests.get("http://localhost:8000/submission/moodle/download_file",
                     {"file_name": link.file_name, "file_url": link.file_url, "mime_type": link.mime_type})
        await file_handler.store_binary_file(res.content, link.file_name, link.mime_type, submission_id)
    pass


@api_router.post('/submission/postnew')
async def post_submission(submission: Submission2, cursor: RealDictCursor = Depends(get_db)):
    await handle_files(submission.file_links, submission.moodle_submision_id)
    res = cursor.execute("""
            INSERT into public.submission(moodle_sub_id,assignment_id,time_created) values(%s,%s,%s)
    """, [submission.moodle_submision_id, submission.assignment_id, submission.time_created])
    return res

''''''


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

    