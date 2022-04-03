import os

from quart import Quart, Response, render_template, request

import config
from utils import db, expire_files, generate_filename, get_expiration_timestamp, has_free_space

upath = config.upath
# either make Quart serve static files or let nginx do it (nginx.example.conf)
app = Quart(__name__, static_url_path="", static_folder=upath)
app.config["MAX_CONTENT_LENGTH"] = 1000 * 1024 * 1024

if not os.path.exists(upath):
    os.mkdir(upath)


@app.before_serving
async def startup():
    app.add_background_task(expire_files)


@app.route("/")
async def home() -> Response:
    return await render_template(
        "index.html", upload_url=config.site_url + "upload", site_name=config.site_name
    )


@app.route("/upload", methods=["POST"])
async def upload_file() -> Response:
    token = request.headers.get("Authorization")
    if not token or token not in config.keys:
        return "Invalid token.", 403

    if not has_free_space():
        return (
            "The server has no more allowed free space left, please wait until some files are removed or expired.",
            507,
        )

    files = await request.files
    file = files.get("file")
    if not file:
        return "No file in body.", 400

    form = await request.form
    expiration = form.get("expiration")
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

    filename = await generate_filename(file)
    path = os.path.join(upath, filename)

    await file.save(path)
    document = {"_id": filename, "expires": expires, "token": token}
    await db.insert_one(document)

    url = config.site_url + filename
    return url, 200


@app.route("/delete", methods=["POST"])
async def delete_files() -> Response:
    token = request.headers.get("Authorization")
    if not token or token != config.admin_key:
        return "Invalid token.", 403

    form = await request.form
    files = form.get("files")
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
            os.remove(f"{upath}/{filename}")
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
