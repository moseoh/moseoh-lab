-- Create "lotto_purchases" table
CREATE TABLE "public"."lotto_purchases" (
  "id" serial NOT NULL,
  "user_id" character varying(32) NOT NULL,
  "user_name" character varying(100) NOT NULL,
  "week_key" character varying(10) NOT NULL,
  "purchased_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("id"),
  CONSTRAINT "lotto_purchases_user_id_week_key_key" UNIQUE ("user_id", "week_key")
);
-- Create index "idx_week_key" to table: "lotto_purchases"
CREATE INDEX "idx_week_key" ON "public"."lotto_purchases" ("week_key");
