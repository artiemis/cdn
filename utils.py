import asyncio
import mimetypes
import os
import random
import re
import shutil
import string
import time
import unicodedata

import config

from motor.motor_asyncio import AsyncIOMotorClient
from quart.datastructures import FileStorage

upath = config.upath
mongo = AsyncIOMotorClient(config.mongo_uri)
db = mongo[config.mongo_db][config.mongo_collection]


async def expire_files() -> None:
    try:
        while True:
            now = round(time.time())
            query = {"expires": {"$ne": 0, "$lt": now}}
            async for upload in db.find(query):
                _id = upload["_id"]
                path = f"{upath}/{_id}"

                os.remove(path)
                await db.delete_one({"_id": _id})
                print(f"[Expiration Task] Removed expired upload: {path}")

            await asyncio.sleep(5 * 60)
    except asyncio.CancelledError:
        pass


def get_expiration_timestamp(hours: int) -> int:
    if hours == 0:
        # does not expire
        return 0
    expires = time.time() + (hours * 60 ** 2)
    return round(expires)


def sanitize_filename(filename: str) -> str:
    if not filename:
        return None

    ret = str(filename)
    ret = unicodedata.normalize("NFKD", ret).encode("ascii", "ignore").decode("ascii")
    ret = re.sub(r"[^\w\s\.-]", "", ret)
    return ret


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
