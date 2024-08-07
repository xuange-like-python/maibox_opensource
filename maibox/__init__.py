import os

if os.path.exists("logging.log"):
    with open("logging.log", "w") as f:
        f.write("")

git_sha = "undefined"
git_sha_full = "undefined"
if os.path.exists("git_sha"):
    git_sha_full = open("git_sha").read()
    git_sha = git_sha_full[:7]

build_date = "undefined"
if os.path.exists("build_date"):
    build_date = open("build_date").read()