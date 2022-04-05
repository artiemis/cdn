# mongo config
mongo_db = "yuzu"
mongo_collection = "uploads"
mongo_uri = "mongodb://localhost:27017"
# filenames will be appended to this URL on successful upload
site_url = "https://example.com/"
# name of the site displayed in <title> and above the upload form
site_name = "Yuzu CDN"
# filepath for the uploads
upath = "uploads"
# random filename length, recommended: 6-12
id_length = 6
# default file expiration time (in hours, 0 for no expiration)
default_expiration_time = 0
# allowed file expiration times (in hours, 0 for no expiration)
allowed_expiration_times = [0, 24, 48, 72, 168]
# don't accept any uploads when when free disk space goes below this limit, 0 to disable
disk_space_limit = 10 * 1024 ** 3
# access tokens for uploading files
keys = ["somelongassrandomstringhere"]
# admin access token for deleting files
admin_key = "somelongassrandomstringhere"
