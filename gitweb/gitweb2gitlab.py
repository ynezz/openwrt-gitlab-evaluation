#!/usr/bin/env python3

import re
import sys
import os.path
import urllib.request
from types import SimpleNamespace

from gitlab import Gitlab
from gitlab.exceptions import GitlabDeleteError, GitlabCreateError
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError

GITWEB_URL = 'https://git.openwrt.org'

GITLAB_URL = 'https://gitlab.com'
GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')
GITLAB_GROUP = 'openwrtorg'

class GitLabHelper(Gitlab):
    def __init__(self, *args, **kwargs):
        self._group_id = None
        self.group = kwargs.pop('group')
        super().__init__(*args, **kwargs)

    def group_id(self):
        if self._group_id:
            return self._group_id

        self._group_id = self.groups.get(self.group).id
        return self._group_id

    def login(self):
        try:
            self.auth()
        except GitlabAuthenticationError:
            return False

        return True

    def project_exists(self, name):
        return self.project(name) is not None

    def project(self, name):
        project = None

        try:
            project = self.projects.get('{0}/{1}'.format(self.group, name))
        except GitlabGetError as e:
            if e.response_code != 404:
                raise

        return project

    def project_delete_by_name(self, name):
        project = self.project(name)
        if not project:
            return False

        return self.project_delete(project)

    def project_delete(self, project):
        try:
            project.delete()
        except GitlabDeleteError as e:
            return False

        return True

    def project_create(self, **kwargs):
        new_project = {
            'name': kwargs['name'],
            'namespace_id': self.group_id(),
            'description': kwargs.get('description', ''),
            'visibility': kwargs.get('visibility', 'public'),
            'merge_method': kwargs.get('merge_method', 'ff'),
            'import_url': kwargs['repo_url'],
            'mirror': True,
            'mirror_trigger_builds': True,
            'only_allow_merge_if_pipeline_succeeds': True,
            'only_allow_merge_if_all_discussions_are_resolved': True,
            'printing_merge_request_link_enabled': False,
            'auto_cancel_pending_pipelines': 'enabled',
            'auto_devops_enabled': False,
            'approvals_before_merge': 2,
            'container_registry_enabled': True,
            'shared_runners_enabled': True,
            'public_builds': True,
        }
        try:
            project = self.projects.create(new_project)
        except GitlabCreateError as e:
            return False

        return True

def file_content(filename):
    with open(filename) as f:
        return f.read()

def gitweb_index(url=GITWEB_URL, filename='gitweb_index.html'):
    if os.path.isfile(filename):
        return file_content(filename)

    with urllib.request.urlopen(url) as response, open(filename, 'wb') as outfile:
        data = response.read()
        outfile.write(data)

    return file_content(filename)

def gitweb_projects():
    projects = []

    project_re = '<a class="list" href="\?p=(project/[\w-]+.git);a=summary" title="([\w\d \(\)/;\'\.-]+)">'
    project_re = re.compile(project_re)

    for match in project_re.finditer(gitweb_index()):
        d = {
            'repo_url': "{0}/{1}".format(GITWEB_URL, match.group(1)),
            'name': match.group(1)[8:-4],
            'description': match.group(2)
        }
        projects.append(SimpleNamespace(**d))

    return projects

def gitweb_migrate_projects(glab, delete_existing=False):
    for project in gitweb_projects():

        if delete_existing and glab.project_exists(project.name):
            if not glab.project_delete_by_name(project.name):
                print("[!] unable to delete GitLab project {0}".format(project.name))
                continue

        if glab.project_exists(project.name):
            print("[+] GitLab project {0} already exists".format(project.name))
            continue

        if not glab.project_create(**vars(project)):
            print("[!] unable to create GitLab project {0}".format(project.name))
            continue

        print("[*] created GitLab project {0}".format(project.name))

def main():
    if not GITLAB_TOKEN:
        sys.exit("GITLAB_TOKEN env variable is missing")

    glab = GitLabHelper(GITLAB_URL, private_token=GITLAB_TOKEN, group=GITLAB_GROUP, api_version=4)
    if not glab.login():
        sys.exit('GitLab login failed')

    gitweb_migrate_projects(glab)

main()
