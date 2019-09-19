import gitlab
from multiprocessing import Pool
import peewee as pw
import time
import random


with open("token_com", "r") as token_file:
    token = token_file.readline()[:-1]

gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
gl.auth()
project = gl.projects.get(14341737)

db = pw.MySQLDatabase("bugs", host="172.17.0.2", port=3306, user="root", passwd="bugs")
db.connect()


def add_task(task):
    try:
        issue = project.issues.get(task[0])
        print("-", end="", flush=True)
    except:
        labels = []
        if task[3] != "Feature Request":
            labels.append("type:" + task[3])

        issue_gl = {
            "id": "openwrt/openwrt",
            "iid": task[0],
            "created_at": task[1],
            "title": task[7],
            "labels": labels,
            "description": task[8].replace("@", "@ "),
        }
        for x in range(100):
            time.sleep(10)
            try:
                issue = project.issues.create(issue_gl)
                break
            except:
                print("#", end="", flush=True)


        print("+", end="", flush=True)

    # is closed
    if task[4]:
        issue.state_event = "close"
        print("x", end="", flush=True)

    with open("select_comments.sql", "r") as comments_file:
        cursor = db.execute_sql(comments_file.read(), params=(str(task[0])))
        comments = cursor.fetchall()

    for comment in comments[len(issue.notes.list()) :]:
        try:
            issue.notes.create(
                {"created_at": comment[0], "body": comment[1].replace("@", "@ ")}
            )
        except:
            print(comment)
        print("o", end="", flush=True)
        time.sleep(1)
    issue.save()
    time.sleep(1)


with open("select_tasks.sql", "r") as tasks_file:
    cursor = db.execute_sql(tasks_file.read())
    tasks = list(cursor.fetchall())

random.shuffle(tasks)
pool = Pool(10)
pool.map(add_task, tasks)
