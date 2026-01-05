.PHONY: sqlc migrate-diff migrate-hash

sqlc:
	sqlc generate

migrate-diff:
	atlas migrate diff $(name) --env local --to file://schema/schema.sql

migrate-hash:
	atlas migrate hash --dir file://migrations
