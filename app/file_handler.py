from pathlib import Path
from datetime import datetime
import shutil
import mimetypes
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
from app.settings import Settings
import zipfile
from io import BytesIO

class FileHandler:
    def __init__(self):
        settings = Settings()
        self.storage_base_dir = Path(settings.STORAGE_BASE_DIR)
        self.storage_base_dir.mkdir(parents=True, exist_ok=True)

    async def store_file(self, file: UploadFile, sumbission_id: int) -> dict:
        """Store an uploaded file"""
        try:
            storage_path = self._create_storage_path(sumbission_id)
            file_info = await self._save_file(file, storage_path)
            return file_info
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"File storage error: {str(e)}")

    def get_path_to_file(self, submission_id):
        storage_path = self.storage_base_dir / \
            str(submission_id)
        return storage_path

    def _create_storage_path(self, submission_id) -> Path:
        """Create organized directory structure"""
        storage_path = self.get_path_to_file(submission_id)
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    async def _save_file(self, file: UploadFile, storage_path: Path) -> dict:
        """Save uploaded file and return its information"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        destination_path = storage_path / unique_filename

        try:
            content = await file.read()
            with destination_path.open("wb") as buffer:
                buffer.write(content)

            return self._get_file_info(destination_path, file.filename)
        except Exception as e:
            if destination_path.exists():
                destination_path.unlink()
            raise e
    
    def _get_file_info(self, file_path: Path, original_filename: str) -> dict:
        """Get file information"""
        file_stats = file_path.stat()
        return {
            'file_name': original_filename,
            'file_path': str(file_path),
            'file_size': file_stats.st_size,
            'mime_type': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        }

    async def get_file(self, submission_id: int) -> FileResponse:
        p=self.get_path_to_file(submission_id)
        first=p.iterdir().__next__()
        #f=zipfile.ZipFile()
        return self.generate_archive(submission_id)
    
    def generate_archive(self,submission_id: int):
        p=self.get_path_to_file(submission_id)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(
        file=zip_buffer,
        mode="w",
        ) as zip_archive:
            for path in p.iterdir():
                zip_archive.write(path)
        return zip_buffer.getvalue()

