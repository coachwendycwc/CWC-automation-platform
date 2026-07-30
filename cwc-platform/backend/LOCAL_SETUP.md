# Local setup

## Use Postgres locally, not SQLite

Production runs Postgres. SQLite silently tolerates schema changes Postgres
rejects, so developing on SQLite means schema problems surface on deploy
instead of on your laptop.

This is not hypothetical: the migration chain was broken for months and nobody
noticed, because SQLite failed at a *different* migration than Postgres does,
and because the local database had been hand-built with `create_all` rather
than by running migrations.

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16
createdb cwc_platform
```

In `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://<your-username>@localhost:5432/cwc_platform
```

Then build the schema **by running migrations**, never `create_all`:

```bash
cd cwc-platform/backend
alembic upgrade head
python -m scripts.seed_dev_user   # creates the first admin
```

## Migrations are the only way schema changes

`Base.metadata.create_all()` builds tables from the models directly. It is
convenient and it is how this codebase drifted into two conflicting sources of
truth — 52 tables in the models, 34 in the migration chain, with the other 18
existing only on machines where someone happened to run `create_all`.

The rule now:

1. Change a model.
2. Generate a migration: `alembic revision --autogenerate -m "what changed"`.
3. **Read the generated file.** Autogenerate misses things — server defaults,
   renames (it sees a drop plus an add), and anything needing data backfill.
4. Test it both ways before committing:
   ```bash
   # fresh database — what a new environment does
   createdb cwc_scratch
   DATABASE_URL=postgresql+asyncpg://$(whoami)@localhost:5432/cwc_scratch alembic upgrade head

   # and against a copy of a real database — what a deploy does
   ```
5. Commit the model change and the migration together, in one commit.

CI enforces the first half of this: every PR runs `alembic upgrade head`
against an empty Postgres and then checks the resulting schema matches the
models. A model without a migration fails the build.

## Running the tests

```bash
cd cwc-platform/backend
pytest tests/ --timeout=40 --timeout-method=thread
```

Tests use in-memory SQLite for speed and build their schema from the models,
so they do **not** exercise migrations. That is what the CI migration job is
for. A green test suite says nothing about whether the schema can be built.

Known: ~23 tests fail on a clean checkout (AI extraction field mismatches,
scheduling, and subscription tests that reach for the real Stripe API with a
placeholder key). They predate current work. When changing code, compare your
failure list against the baseline rather than expecting zero.

Note: `pytest` finishes in about three minutes but then hangs at exit on a
lingering connection. The results are already written when the summary line
appears.

## Frontend

```bash
cd cwc-platform/frontend
npm install
npm run dev        # http://localhost:3001
npx tsc --noEmit   # typecheck; CI runs this too
```
