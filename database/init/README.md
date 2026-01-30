# Database Initialization Scripts

These scripts run **once** when PostgreSQL container starts with empty volumes.

## Execution Order

PostgreSQL runs scripts in **alphabetical order**:

1. `01-create-databases.sql` - Creates `research_assistant` and `trulens` databases
2. `02-trulens-schema.sql` - Creates custom evaluation tables

## First-Time Setup

No manual intervention needed. Just run:
```bash
docker compose -f docker/docker-compose.yml up -d
```

## After TruLens Initializes

TruLens will create its `records` table on first use. After that, add foreign key constraints:
```bash
docker compose -f docker/docker-compose.yml exec postgres \
  psql -U research_assistant -d trulens -c "SELECT add_foreign_key_constraints();"
```

Or use the helper script:
```bash
bash database/scripts/add-foreign-keys.sh
```

## Reset Database

To wipe everything and start fresh:
```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

The `-v` flag removes volumes, triggering a complete re-initialization.