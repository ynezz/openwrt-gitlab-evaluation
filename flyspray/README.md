# FlySpray to GitLab migrator

1. Retreive a database dump.
2. Run a local database containing the issues via the following command.

```
sudo docker run -v "$(pwd)/flyspray.sql:/docker-entrypoint-initdb.d/fs.sql" -e MYSQL_ROOT_PASSWORD=bugs -e MYSQL_DATABASE=bugs --rm  mariadb:latest
```

3. Run `python3 fs2gitlab.py`
4. Wait a very long time

