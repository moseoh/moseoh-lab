-- name: GetAlarmSetting :one
SELECT guild_id, alarm_type, channel_id, created_at, updated_at
FROM alarm_settings
WHERE guild_id = $1 AND alarm_type = $2
LIMIT 1;

-- name: UpsertAlarmSetting :one
INSERT INTO alarm_settings (guild_id, alarm_type, channel_id)
VALUES ($1, $2, $3)
ON CONFLICT (guild_id, alarm_type) DO UPDATE SET
    channel_id = EXCLUDED.channel_id,
    updated_at = CURRENT_TIMESTAMP
RETURNING guild_id, alarm_type, channel_id, created_at, updated_at;

-- name: DeleteAlarmSetting :exec
DELETE FROM alarm_settings
WHERE guild_id = $1 AND alarm_type = $2;

-- name: GetAlarmSettingsByType :many
SELECT guild_id, channel_id
FROM alarm_settings
WHERE alarm_type = $1;

-- name: DeleteAlarmSettingsByChannel :exec
DELETE FROM alarm_settings
WHERE channel_id = $1;
