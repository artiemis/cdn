import asyncio
import mimetypes
import os
import random
import shutil
import string
import time

import config

from quart.datastructures import FileStorage

upath = config.upath


async def expire_files() -> None:
    try:
        while True:
            for filename in os.listdir(upath):
                path = f"{upath}/{filename}"
                mtime = os.stat(path).st_mtime
                if time.time() - mtime > config.expiration_time:
                    os.remove(path)
                    print(f"[Expiration Task] Removing: {filename}")
            await asyncio.sleep(5 * 60)
    except asyncio.CancelledError:
        pass


def generate_id() -> str:
    ret = random.choices(string.ascii_lowercase + string.digits, k=config.id_length)
    return "".join(ret)


def generate_filename(file: FileStorage) -> str:
    ext = mimetypes.guess_extension(file.content_type)
    filename = generate_id() + ext
    while filename in os.listdir(upath):
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
