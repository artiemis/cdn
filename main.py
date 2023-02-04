from pathlib import Path
from typing import Optional

from quart import Quart, render_template, request
from quart.datastructures import FileStorage
from quart_cors import cors
from werkzeug.utils import secure_filename

import config
from utils import (db, expire_files, generate_filename,
                   get_expiration_timestamp, has_free_space)

upload_dir = Path(config.upload_dir)
# either make Quart serve static files or let nginx do it (nginx.example.conf)
app = Quart(__name__, static_url_path="", static_folder=upload_dir.as_posix())
app: Quart = cors(app, allow_origin="*")  # type: ignore

app.config["MAX_CONTENT_LENGTH"] = 1000 * 1024 * 1024

upload_dir.mkdir(exist_ok=True)


@app.before_serving
async def startup():
    app.add_background_task(expire_files)


@app.before_request
async def check_auth():
    path = request.path
    token = request.headers.get("Authorization")

    if path.startswith("/upload"):
        if not token or token not in config.keys:
            return "Invalid token.", 401
        request.token = token
    elif path.startswith("/delete"):
        if not token or token != config.admin_key:
            return "Invalid token.", 401


@app.get("/")
async def home():
    return await render_template("index.html")


@app.get("/motd")
async def motd():
    return "Work in progress, internal use only.", 200


@app.post("/upload")
async def upload_file():
    if not has_free_space():
        return (
            "The server has no more allowed free space left, please wait until some files are removed or expired.",
            507,
        )

    files = await request.files
    file: Optional[FileStorage] = files.get("file")
    if not file:
        return "No file in body.", 400

    form = await request.form
    expiration: Optional[str | int] = form.get("expiration")
    keep_filename: Optional[str] = form.get("keep_filename")

    if expiration is None:
        expires = get_expiration_timestamp(config.default_expiration_time)
    else:
        try:
            expiration = int(expiration)
        except ValueError:
            return "Expiration time must be an integer.", 400
        if expiration not in config.allowed_expiration_times:
            return "Invalid expiration time.", 400
        expires = get_expiration_timestamp(expiration)

    if keep_filename and keep_filename == "true":
        filename = secure_filename(file.filename)
        if not filename or filename.startswith("."):
            return "Invalid or missing filename.", 400
        elif await db.find_one({"_id": filename}):
            return "File already exists.", 400
    else:
        filename = await generate_filename(file)

    path = upload_dir / filename

    await file.save(path)
    document = {"_id": filename, "expires": expires, "token": request.token}
    await db.insert_one(document)

    url = config.site_url + filename
    return url, 200


@app.get("/expiration")
async def get_allowed_expiration():
    return {
        "allowed": config.allowed_expiration_times,
        "default": config.default_expiration_time,
    }, 200


@app.post("/delete")
async def delete_files():
    form = await request.form
    files: Optional[str] = form.get("files")
    if not files:
        return "No files specified.", 400

    files = files.split(" ")
    deleted = []
    not_found = []
    for filename in files:
        upload = await db.find_one({"_id": filename})
        if not upload:
            not_found.append(filename)
        else:
            path = upload_dir / filename
            path.unlink()
            await db.delete_one({"_id": filename})
            deleted.append(filename)

    msg = ""
    if deleted:
        msg += f"Files deleted: {', '.join(deleted)}\n"
    if not_found:
        msg += f"Files not found: {', '.join(not_found)}"
    return msg


if __name__ == "__main__":
    app.run()
