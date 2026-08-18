import os
import uuid
from fastapi import UploadFile

class StorageService:
    def __init__(self, upload_dir: str = "/tmp/shadow-cricket-images"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_upload_file(self, file: UploadFile) -> str:
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)

        with open(file_path, "wb") as buffer:
            # Read and write in chunks if the file is large
            content = await file.read()
            buffer.write(content)

        # Return a simple URI (e.g., local path or mock object storage key)
        return f"local://{file_path}"

    def get_file_bytes(self, image_uri: str) -> bytes:
        if image_uri.startswith("local://"):
            file_path = image_uri.replace("local://", "")
            with open(file_path, "rb") as f:
                return f.read()
        raise ValueError(f"Unsupported URI scheme: {image_uri}")

storage_service = StorageService()
