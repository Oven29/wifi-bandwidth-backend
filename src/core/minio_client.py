import os
import uuid
from fastapi import UploadFile
from minio import Minio

from src.core.config import settings

minio_client = Minio(
    endpoint=settings.minio.endpoint,
    access_key=settings.minio.access_key,
    secret_key=settings.minio.secret_key,
    secure=False,
)


def ensure_bucket_exists() -> None:
    try:
        if not minio_client.bucket_exists(settings.minio.bucket_name):
            minio_client.make_bucket(settings.minio.bucket_name)
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
        bucket_name=settings.minio.bucket_name,
        object_name=generated_name,
        data=file.file,
        length=file_size,
        content_type=file.content_type or "application/octet-stream",
    )

    return f"http://{settings.minio.endpoint}/{settings.minio.bucket_name}/{generated_name}"
