from fastapi import APIRouter, Depends, UploadFile
from psycopg2.extras import RealDictCursor
from app.session import get_db
from pydantic import BaseModel
from app.settings import Settings
import pathlib
from fastapi.responses import StreamingResponse, FileResponse, Response
from app.file_handler import FileHandler

setting=Settings()
api_router = APIRouter()

@api_router.get('/submission/get')
async def get_submission(id, cursor: RealDictCursor = Depends(get_db)):
    
    cursor.execute("""
            SELECT * from public.submission s where s.moodle_sub_id=%s
    """, (id))
    res = cursor.fetchone()
    return res


class Submission(BaseModel):
    moodle_submision_id: int
    status: str
    time_created: str

@api_router.post('/submission/postnew')
async def post_submission(o: Submission, cursor: RealDictCursor = Depends(get_db)):
    res = cursor.execute("""
            INSERT into public.submission values(%s,%s,%s)
    """, (o.moodle_submision_id, o.status, o.time_created))

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


    