# Database Migrations

Schema changes after initial deployment go here.

## Naming Convention
```
YYYY-MM-DD_description.sql
```

Examples:
- `2026-01-30_add_user_feedback_table.sql`
- `2026-02-15_add_response_time_index.sql`

## How to Apply

Migrations are **manual** for now. To apply:
```bash
docker compose -f docker/docker-compose.yml exec -T postgres \
  psql -U research_assistant -d trulens < database/migrations/2026-01-30_add_user_feedback_table.sql
```

## Future: Automated Migrations

Consider using:
- [Alembic](https://alembic.sqlalchemy.org/) (Python/SQLAlchemy)
- [Flyway](https://flywaydb.org/) (Java-based)
- [migrate](https://github.com/golang-migrate/migrate) (Go-based)