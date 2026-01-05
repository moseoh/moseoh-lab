-- Create "alarm_settings" table
CREATE TABLE "public"."alarm_settings" (
  "guild_id" character varying(32) NOT NULL,
  "alarm_type" character varying(32) NOT NULL,
  "channel_id" character varying(32) NOT NULL,
  "created_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("guild_id", "alarm_type")
);
-- Drop "guild_settings" table
DROP TABLE "public"."guild_settings";
