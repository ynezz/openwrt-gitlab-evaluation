#!/usr/bin/env python3

import re
import sys
import os.path
import urllib.request
from types import SimpleNamespace

from gitlab import Gitlab
from gitlab.exceptions import GitlabDeleteError, GitlabCreateError
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError

GITWEB_URL = "https://git.openwrt.org"

GITLAB_URL = "https://gitlab.com"
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
GITLAB_GROUP = "openwrt"


class GitLabHelper(Gitlab):
    def __init__(self, *args, **kwargs):
        self.group_ids = {}
        super().__init__(*args, **kwargs)

    def group_id(self, group):
        id = self.group_ids.get(group)
        if id:
            return id

        id = self.groups.get(group).id
        self.group_ids[group] = id
        return id

    def login(self):
        try:
            self.auth()
        except GitlabAuthenticationError:
            return False

        return True

    def project_exists(self, project):
        return self.project_get(project) is not None

    def project_get(self, project):
        p = None

        try:
            p = self.projects.get(project.full_path)
        except GitlabGetError as e:
            if e.response_code != 404:
                raise

        return p

    def project_delete(self, project):
        try:
            self.project_get(project).delete()
        except GitlabDeleteError as e:
            print("[!] project_delete exception:", e)
            return False

        return True

    def project_create(self, **kwargs):
        new_project = {
            "name": kwargs["name"],
            "namespace_id": self.group_id(kwargs["group"]),
            "description": kwargs.get("description", ""),
            "visibility": kwargs.get("visibility", "public"),
            "merge_method": kwargs.get("merge_method", "ff"),
            "import_url": kwargs["repo_url"],
            "mirror": True,
            "mirror_trigger_builds": True,
            "only_allow_merge_if_pipeline_succeeds": True,
            "only_allow_merge_if_all_discussions_are_resolved": True,
            "printing_merge_request_link_enabled": False,
            "auto_cancel_pending_pipelines": "enabled",
            "auto_devops_enabled": False,
            "approvals_before_merge": 2,
            "container_registry_enabled": True,
            "shared_runners_enabled": True,
            "public_builds": True,
        }
        try:
            self.projects.create(new_project)
        except GitlabCreateError as e:
            print("[!] project_create exception:", e)
            return False

        return True


def file_content(filename):
    with open(filename) as f:
        return f.read()


def gitweb_index(url=GITWEB_URL, filename="gitweb_index.html"):
    if os.path.isfile(filename):
        return file_content(filename)

    with urllib.request.urlopen(url) as response, open(filename, "wb") as outfile:
        data = response.read()
        outfile.write(data)

    return file_content(filename)


def gitweb_repos_for_migration():
    repos = []

    repo_re = r'<a class="list" href="\?p=(.*).git;a=summary" title="(.*)">'
    repo_re = re.compile(repo_re)

    for match in repo_re.finditer(gitweb_index()):
        path = match.group(1)
        name = path.split("/")[-1]
        desc = match.group(2).replace("LEDE", "OpenWrt")

        if "project/luci2" in path or "openwrt/staging" in path:
            continue

        group = GITLAB_GROUP
        if "feed/" in path:
            group = "{0}/feed".format(GITLAB_GROUP)
        elif "project/" in path:
            group = "{0}/project".format(GITLAB_GROUP)
        elif path == "openwrt/openwrt":
            group = "{0}/openwrt".format(GITLAB_GROUP)
        elif "svn-archive/" in path:
            group = "{0}/openwrt/svn-archive".format(GITLAB_GROUP)

        d = {
            "name": name,
            "full_path": "{0}/{1}".format(group, name),
            "group": group,
            "description": desc,
            "repo_url": "{0}/{1}.git".format(GITWEB_URL, path),
        }
        repos.append(SimpleNamespace(**d))

    return repos


def gitweb_migrate_projects(glab, delete_existing=False):
    for project in gitweb_repos_for_migration():

        if delete_existing and glab.project_exists(project):
            if not glab.project_delete(project):
                print("[!] unable to delete GitLab project {0}".format(project.name))
                continue
            else:
                print("[!] deleted GitLab project {0}".format(project.name))

        if glab.project_exists(project):
            print("[+] GitLab project {0} already exists".format(project.name))
            continue

        if project.group != GITLAB_GROUP:
            parent_id = glab.groups.list(search=GITLAB_GROUP, top_level_only=True)[0].id
            for subgroup_name in project.group.split("/")[1:]:
                subgroup_found = False
                parent_group = glab.groups.get(parent_id)
                for subgroup in parent_group.subgroups.list():
                    if subgroup.name == subgroup_name:
                        subgroup_id = subgroup.id
                        subgroup_found = True
                        break
                if not subgroup_found:
                    subgroup_id = glab.groups.create(
                        {
                            "name": subgroup_name,
                            "path": subgroup_name,
                            "parent_id": parent_id,
                            "visibility": "public",
                        }
                    )
                parent_id = subgroup_id

        if not glab.project_create(**vars(project)):
            print("[!] unable to create GitLab project {0}".format(project.name))
            continue

        print("[*] created GitLab project {0}".format(project.name))


def main():
    if not GITLAB_TOKEN:
        sys.exit("GITLAB_TOKEN env variable is missing")

    glab = GitLabHelper(GITLAB_URL, private_token=GITLAB_TOKEN, api_version=4)
    if not glab.login():
        sys.exit("GitLab login failed")

    gitweb_migrate_projects(glab)


main()
