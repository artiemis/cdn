# filenames will be appended to this URL on successful upload
site_url = "https://example.com/"
# filepath for the uploads
upath = "uploads"
# random filename length, recommended: 6-12
id_length = 6
# expire files older than this time in seconds
expiration_time = 72 * 60 * 60
# don't accept any uploads when when free disk space goes below this limit, 0 to disable
disk_space_limit = 10 * 1024 * 1024 * 1024
# access tokens for uploading files
keys = ["somelongassrandomstringhere"]
# admin access token for deleting files
admin_key = keys[0]
