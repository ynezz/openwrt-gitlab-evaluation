SELECT
comments.date_added,
comments.comment_text

FROM
flyspray_comments AS comments

WHERE
comments.task_id = %s

ORDER BY
comments.date_added
