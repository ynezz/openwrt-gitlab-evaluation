#!/usr/bin/env python3

from subprocess import run
import os
import requests
import time

from github import Github
from gitlab import Gitlab
from gitlab.exceptions import GitlabCreateError
from pathlib import Path

gh = Github()
repo = gh.get_repo("openwrt/openwrt")

GITLAB_URL = "https://gitlab.com"
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
gl = Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)
gl.auth()
# TODO this is not nice
project = gl.projects.get(15390511)


def run_git(*cmd):
    run(["git"] + list(cmd), cwd="./openwrt")


pulls = repo.get_pulls(state="open", sort="created", base="master")
for pr in pulls:
    Path("openwrt/mbox").write_bytes(requests.get(pr.patch_url).content)
    run_git("switch", "master")
    run_git("reset", "--hard", "origin/master")
    run_git("pull")
    run_git("switch", "-C", f"gh-{pr.number}")
    run_git("am", "-3", "./mbox")
    run_git("push", "origin", f"gh-{pr.number}", "-f")
    run_git("am", "--abort")
    try:
        mr = project.mergerequests.create(
            {
                "source_branch": f"gh-{pr.number}",
                "title": pr.title,
                "description": "This patch was added via GitHub."
                f"Please follow the discussion [here]({pr.html_url})",
                "target_branch": "master",
                "labels": ["github"],
            }
        )
        mr.discussion_locked = True
        mr.save()
    except GitlabCreateError:
        print("Already created")
    time.sleep(5)
