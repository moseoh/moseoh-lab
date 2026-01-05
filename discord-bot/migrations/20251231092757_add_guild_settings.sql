-- Create "guild_settings" table
CREATE TABLE "public"."guild_settings" (
  "guild_id" character varying(32) NOT NULL,
  "alarm_channel_id" character varying(32) NULL,
  "created_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("guild_id")
);
