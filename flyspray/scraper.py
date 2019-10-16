from bs4 import BeautifulSoup
from urllib.request import urlopen
import gitlab
from multiprocessing import Pool

with open("token", "r") as token_file:
    token = token_file.read()

issue_url_template = "https://bugs.openwrt.org/index.php?do=details&task_id={}"

gl = gitlab.Gitlab("https://code.fe80.eu", private_token=token)
gl.auth()
project = gl.projects.get(203)  # openwrt/openwrt


def add_issue(i):
    issue_raw = urlopen(issue_url_template.format(i)).read().decode("utf-8")

    issue_fs = {}
    issue_fs["id"] = i
    soup = BeautifulSoup(issue_raw, "html.parser")
    issue_fs["title"] = soup.title.string.replace(f"FS#{i} : ", "")
    taskfields = soup.find(id="taskfields")
    taskdetailstext = soup.find(id="taskdetailstext")

    try:
        spans = taskfields.ul.find_all("span")
        issue_fs["status"] = spans[1].string.strip().lower()
        issue_fs["type"] = spans[6].string.strip().lower()
        issue_fs["category"] = spans[8].string.strip().lower()
        issue_fs["severity"] = spans[14].string.strip().lower()
        issue_fs["priority"] = spans[16].string.strip().lower()
        issue_fs["version"] = spans[18].string.strip().lower()

        fineprint = taskfields.find(id="fineprint")
        issue_fs["username"] = fineprint.br.a.string
        issue_fs["created_at"] = fineprint.br.span.string

        issue_fs["description"] = "\n\n".join(taskdetailstext.stripped_strings)
    except:
        print(f"\nParsing error on issue {i}")
        with open(f"./issues/issue_{i}.html", "w") as issue_file:
            issue_file.write(issue_raw)
        return

    issue_gl = {
        "id": "openwrt/openwrt",
        "iid": issue_fs["id"],
        "created_at": issue_fs["created_at"],
        "title": issue_fs["title"],
        "labels": [
            "severity:" + issue_fs["severity"],
            "priority:" + issue_fs["priority"],
            "version:" + issue_fs["version"],
            issue_fs["type"],
        ],
        "description": "Username: {}\n\nOrigin: {}\n\n{}".format(
            issue_fs["username"],
            issue_url_template.format(issue_fs["id"]),
            issue_fs["description"],
        ),
    }
    try:
        issue = project.issues.create(issue_gl)
        if issue_fs["status"] == "closed":
            issue.state_event = "close"
            issue.save()
            print(".", end="", flush=True)
    except:
        print(f"Error GitLab add {i}")
        return

    for comment in soup.find_all(class_="comment_container"):
        try:
            data = {"issue": i, "comment_id": comment["id"][7:]}
            comment_info = comment.find(class_="comment_header_infos")
            if comment_info.a:
                data["username"] = comment_info.a.string
            else:
                data["username"] = "unknown"

            data["created_at"] = list(comment_info.strings)[-1][14:]
            data["description"] = "\n\n".join(
                comment.find(class_="commenttext").stripped_strings
            )

            issue.notes.create(
                {
                    "created_at": data["created_at"],
                    "body": "Username: {}\n\n{}".format(
                        data["username"], data["description"]
                    ),
                }
            )
            print("+", end="", flush=True)
        except Exception as e:
            print(e)
            print(f"\nError on comments of issue #{i}")


def delete_label(i):
    try:
        project.labels.delete(i)
        print("o", end="", flush=True)
    except:
        print("O", end="", flush=True)


def delete_issue(i):
    try:
        project.issues.delete(i)
        print("/", end="", flush=True)
    except:
        print("#", end="", flush=True)


issues = range(2, 2487)
# labels = range(0, 500)
pool = Pool(50)
# pool.map(delete_label, labels)
# pool.map(delete_issue, issues)
pool.map(add_issue, issues)
