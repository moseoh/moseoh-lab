CREATE TABLE lotto_purchases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    week_key VARCHAR(10) NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_key)
);

CREATE INDEX idx_week_key ON lotto_purchases(week_key);

CREATE TABLE alarm_settings (
    guild_id VARCHAR(32) NOT NULL,
    alarm_type VARCHAR(32) NOT NULL,
    channel_id VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, alarm_type)
);
