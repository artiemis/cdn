import mimetypes
import os

from quart import Quart, Response, render_template, request

import config
from utils import expire_files, generate_id, has_free_space

upath = config.upath
# either make Quart serve static files or let nginx do it (nginx.conf)
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

    if not has_free_space:
        return (
            "The server has no more allowed free space left, please wait until some files expire.",
            507,
        )

    files = await request.files
    if not files:
        return "Invalid form data.", 400
    elif "file" not in files:
        return "No file in body.", 400
    file = files["file"]

    ext = mimetypes.guess_extension(file.content_type)
    filename = generate_id() + ext
    while filename in os.listdir("uploads"):
        filename = generate_id() + ext

    path = os.path.join(upath, filename)
    await file.save(path)
    url = config.site_url + filename
    return url, 200


@app.route("/delete", methods=["POST"])
async def delete_files() -> Response:
    token = request.headers.get("Authorization")

    if not token or token != config.admin_key:
        return "Invalid token.", 403

    form = await request.form
    if not form:
        return "Invalid form data.", 400
    elif "files" not in form:
        return "No files specified.", 400

    files = form["files"].split(" ")
    deleted = []
    not_found = []
    for filename in files:
        if filename not in os.listdir(upath):
            not_found.append(filename)
        else:
            os.remove(f"{upath}/{filename}")
            deleted.append(filename)

    msg = ""
    if deleted:
        msg += f"Files deleted: {', '.join([f for f in deleted])}\n"
    if not_found:
        msg += f"Files not found: {', '.join([f for f in not_found])}"
    return msg


if __name__ == "__main__":
    app.run()
