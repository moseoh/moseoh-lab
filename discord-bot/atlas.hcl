env "local" {
  src = "file://schema/schema.sql"
  dev = "docker://postgres/18/dev"
  migration {
    dir = "file://migrations"
  }
}
