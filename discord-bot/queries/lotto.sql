-- name: FindPurchaseByWeekKey :one
SELECT id, user_id, user_name, week_key, purchased_at
FROM lotto_purchases
WHERE week_key = $1
LIMIT 1;

-- name: FindPurchaseByUserAndWeek :one
SELECT id, user_id, user_name, week_key, purchased_at
FROM lotto_purchases
WHERE user_id = $1 AND week_key = $2
LIMIT 1;

-- name: CreatePurchase :one
INSERT INTO lotto_purchases (user_id, user_name, week_key)
VALUES ($1, $2, $3)
RETURNING id, user_id, user_name, week_key, purchased_at;
