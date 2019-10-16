import gitlab
import peewee as pw
import time


# load local gitlab token
with open("token_com", "r") as token_file:
    token = token_file.readline()[:-1]

# connect to gitlab
gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
gl.auth()
project = gl.projects.get(14341737)

# connect to local running mariadb with flyspray bugs
db = pw.MySQLDatabase("bugs", host="172.17.0.2", port=3306, user="root", passwd="bugs")
db.connect()


# get a list of all tasks
with open("select_tasks.sql", "r") as tasks_file:
    cursor = db.execute_sql(tasks_file.read())
    tasks = list(cursor.fetchall())

for task in tasks:
    try:
        # try getting task, if this fails the task does not yet exists...
        issue = project.issues.get(task[0])
        print("-", end="", flush=True)
    except Exception as e:
        # ... so create it here
        print(e)
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
        issue = project.issues.create(issue_gl)

        print("+", end="", flush=True)
        # gitlab.com has a rate limit of 10 add actions per minute
        time.sleep(7)

    # close closed tasks
    if task[4] and issue.state != "closed":
        issue.state_event = "close"
        print("x", end="", flush=True)
        issue.save()

# now add comment
for task in tasks:
    # get the issue
    issue = project.issues.get(task[0])

    # get comments of the issue
    with open("select_comments.sql", "r") as comments_file:
        cursor = db.execute_sql(comments_file.read(), (str(task[0]),))
        comments = cursor.fetchall()

    # iterate over only new comment, as comments don't have unique id
    # if a comment would be edited, it is not covered here
    for comment in comments[len(issue.notes.list()):]:
        issue.notes.create(
            {"created_at": comment[0], "body": comment[1].replace("@", "@ ")}
        )
        print("c", end="", flush=True)
        # same rate limit as above
        time.sleep(7)
