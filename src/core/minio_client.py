import os
import uuid
from fastapi import UploadFile
from minio import Minio

from src.core.config import settings

minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


def ensure_bucket_exists() -> None:
    try:
        if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    except Exception:
        pass


ensure_bucket_exists()


def upload_file_to_minio(file: UploadFile) -> str:
    ensure_bucket_exists()
    _, ext = os.path.splitext(file.filename or "")
    generated_name = f"{uuid.uuid4().hex}{ext}"

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=generated_name,
        data=file.file,
        length=file_size,
        content_type=file.content_type or "application/octet-stream",
    )

    return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{generated_name}"
