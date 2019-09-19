SELECT
tasks.task_id,
tasks.date_opened,
tasks.task_type AS tasktype_id,
tasktypes.tasktype_name AS tasktype,
tasks.is_closed,
tasks.date_closed,
tasks.closure_comment,
tasks.item_summary,
tasks.detailed_desc,
tasks.resolution_reason AS resolution_id,
resolutions.resolution_name,
tasks.operating_system AS os_id,
os.os_name AS os_name,
tasks.last_edited_time,
(tasks.last_edited_by > 0) AS was_edited

FROM
flyspray_tasks AS tasks,
flyspray_list_resolution AS resolutions,
flyspray_list_os AS os,
flyspray_list_tasktype AS tasktypes

WHERE
tasks.resolution_reason = resolutions.resolution_id AND
tasks.operating_system = os.os_id AND
tasks.task_type = tasktypes.tasktype_id

order by
tasks.last_edited_time desc
