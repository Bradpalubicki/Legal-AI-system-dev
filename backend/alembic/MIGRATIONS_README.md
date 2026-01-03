# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Overview

Alembic is a database migration tool for SQLAlchemy. It allows you to:
- Track schema changes over time
- Apply migrations to upgrade databases
- Rollback changes if needed
- Maintain consistency across environments

## Common Commands

### Creating a New Migration

After modifying SQLAlchemy models, generate a new migration:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

Upgrade to the latest version:

```bash
alembic upgrade head
```

Upgrade to a specific version:

```bash
alembic upgrade <revision_id>
```

### Rolling Back Migrations

Downgrade by one revision:

```bash
alembic downgrade -1
```

Downgrade to a specific version:

```bash
alembic downgrade <revision_id>
```

### Checking Migration Status

View current database version:

```bash
alembic current
```

View migration history:

```bash
alembic history
```

View pending migrations:

```bash
alembic heads
```

## Environment Configuration

Alembic reads DATABASE_URL from your environment variables. Ensure it's set:

**Development (SQLite):**
```bash
# Leave DATABASE_URL unset or:
export DATABASE_URL=sqlite:///./legal_ai.db
```

**Production (PostgreSQL):**
```bash
export DATABASE_URL=postgresql://user:password@host:5432/database
```

## Security Notes

⚠️ **IMPORTANT:**
- Never commit database credentials to version control
- DATABASE_URL is loaded from environment variables only
- alembic.ini does NOT contain credentials
- Migration files may contain schema but never data

## Best Practices

1. **Always review generated migrations** - Autogenerate is smart but not perfect
2. **Test migrations** - Run upgrade/downgrade in dev before production
3. **Backup before migrating** - Always backup production databases
4. **Keep migrations atomic** - One logical change per migration
5. **Document complex migrations** - Add comments explaining non-obvious changes

## Production Deployment

Before deploying to production:

1. Review all pending migrations
2. Backup the database
3. Run migrations in a maintenance window
4. Verify application health after migration

```bash
# Production migration workflow
alembic current                    # Check current version
alembic history                    # Review pending migrations
alembic upgrade head --sql         # Generate SQL (dry-run)
alembic upgrade head               # Apply migrations
alembic current                    # Verify new version
```

## Troubleshooting

### Migration fails with "Target database is not up to date"

```bash
alembic stamp head  # Mark current database as up-to-date (use carefully!)
```

### Need to create an empty migration

```bash
alembic revision -m "Description"  # Without --autogenerate
```

### Alembic can't find models

Ensure models are imported in `alembic/env.py` and PYTHONPATH is correct.

## Files in This Directory

- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for new migrations
- `versions/` - Individual migration scripts
- `alembic.ini` - Alembic configuration (in parent directory)
