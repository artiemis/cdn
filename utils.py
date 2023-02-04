import asyncio
import mimetypes
import random
import shutil
import string
import time
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from quart.datastructures import FileStorage

import config

upload_dir = Path(config.upload_dir)
mongo = AsyncIOMotorClient(config.mongo_uri)
db = mongo[config.mongo_db][config.mongo_collection]


async def expire_files() -> None:
    try:
        while True:
            now = round(time.time())
            query = {"expires": {"$ne": 0, "$lt": now}}
            async for upload in db.find(query):
                _id: str = upload["_id"]
                path = upload_dir / _id

                path.unlink()
                await db.delete_one({"_id": _id})
                print(f"[Expiration Task] Removed expired upload: {path}")

            await asyncio.sleep(5 * 60)
    except asyncio.CancelledError:
        pass


def get_expiration_timestamp(hours: int) -> int:
    if hours == 0:
        # does not expire
        return 0
    expires = time.time() + (hours * 60**2)
    return round(expires)


def generate_id() -> str:
    ret = random.choices(string.ascii_lowercase + string.digits, k=config.id_length)
    return "".join(ret)


async def generate_filename(file: FileStorage) -> str:
    ext = mimetypes.guess_extension(file.content_type) or ""
    filename = generate_id() + ext
    while await db.find_one({"_id": filename}):
        filename = generate_id() + ext
    return filename


def has_free_space() -> bool:
    limit = config.disk_space_limit
    if limit == 0:
        return True

    free = shutil.disk_usage("/").free
    if free < limit:
        return False
    return True
