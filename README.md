# Approval System

An educational backend REST API for managing proposals and collective decision-making.

Users can create proposals, assign participants, collect votes, and determine a final result. The project focuses on business-rule enforcement, proposal lifecycle management, audit logging, and transactional consistency.

## Key Features

- Controlled proposal lifecycle: `draft`, `voting`, `approved`, `rejected`, and `deleted`
- Proposal editing in draft status and soft deletion from any active or final status
- Participant validation and author-only operations
- Voting and vote changing while voting is active
- Manual finalization and automatic finalization after all participants vote
- Timezone-aware voting deadlines
- Audit logging for important business actions
- PostgreSQL row-level locking for concurrent changes
- Business logic, API, and transaction tests

## Tech Stack

- Python 3.12
- FastAPI and Pydantic
- SQLAlchemy ORM
- PostgreSQL 17
- Alembic
- pytest
- Docker Compose
- GitHub Actions

## Architecture

The application uses a layered architecture:

```text
HTTP request
    ↓
Router (FastAPI)
    ↓
Service layer
    ↓
Repository layer
    ↓
PostgreSQL
```

- **Routers** accept HTTP requests and return responses
- **Schemas (Pydantic)** validate request and response data
- **Service layer** contains business rules and controls transaction boundaries
- **Repositories** isolate database queries
- **Models (SQLAlchemy ORM)** define persisted entities and relationships
- **Alembic** manages database schema migrations

The main domain entities are `User`, `Proposal`, `Participant`, `Vote`, and `AuditLog`.

Operations that change a proposal or its votes lock the proposal row with `SELECT FOR UPDATE`. This prevents concurrent requests from making decisions based on the same outdated proposal state.

## Proposal Lifecycle

```text
draft ──→ voting ──→ approved
  │          │
  │          └────→ rejected
  │
  └────────────────→ deleted

voting / approved / rejected ──→ deleted
```

The proposal author can edit a proposal only while it is in `draft`. The author can start voting, finish voting manually, or soft-delete the proposal.

A proposal is approved only when the number of `approve` votes is greater than the number of `reject` votes. A tie, including a proposal without votes, results in `rejected`.

## Voting and Deadlines

Only assigned participants can vote. Each participant has one vote and may change it while the proposal remains in `voting` status. Supported values are `approve` and `reject`.

A proposal is finalized automatically when all participants have voted. A deadline is checked when a participant attempts to create or change a vote. If the deadline has passed, the proposal is finalized first and the attempted vote is rejected.

Deadline processing is intentionally request-driven: the project does not use a background scheduler. Therefore, a proposal may remain in `voting` after its deadline until the next voting action.

## API

Interactive OpenAPI documentation is available at `/docs` while the application is running.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Check application availability |
| `POST` | `/proposals` | Create a proposal |
| `GET` | `/proposals/{proposal_id}` | Get a proposal |
| `PATCH` | `/proposals/{proposal_id}` | Update a draft proposal |
| `DELETE` | `/proposals/{proposal_id}` | Soft-delete a proposal |
| `POST` | `/proposals/{proposal_id}/start` | Start voting |
| `POST` | `/proposals/{proposal_id}/finish` | Finish voting manually |
| `GET` | `/proposals/{proposal_id}/result` | Get the proposal status |
| `GET` | `/proposals/{proposal_id}/votes` | Get a proposal with its votes |
| `POST` | `/votes` | Create a vote |
| `PATCH` | `/votes` | Change an existing vote |

Deleted proposals are hidden from regular read operations.

## Error Handling

Business logic raises domain-specific exceptions in the service layer. FastAPI exception handlers convert them into HTTP responses:

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid domain data |
| `403 Forbidden` | User is not allowed to perform the operation |
| `404 Not Found` | Proposal, user, or vote does not exist |
| `409 Conflict` | Operation conflicts with the current proposal or vote state |
| `422 Unprocessable Entity` | Request body does not match the Pydantic schema |

## Running with Docker

Create the environment file:

```bash
cp .env.example .env
```

Replace the example database password in `.env`. The same value must be used in `POSTGRES_PASSWORD`, `DATABASE_URL`, and `TEST_DATABASE_URL`.

Pull the published application image and start PostgreSQL:

```bash
docker compose pull
docker compose up -d postgres
```

Apply migrations and start the backend:

```bash
docker compose run --rm backend alembic upgrade head
docker compose up -d backend
```

Check the application:

```bash
curl http://localhost:8001/health
```

Swagger UI is available at [http://localhost:8001/docs](http://localhost:8001/docs).

For subsequent starts, use:

```bash
docker compose up -d
```

To stop the application:

```bash
docker compose down
```

PostgreSQL data is preserved in the `postgres_data` Docker volume.

## Tests

Tests use SQLite for service-level scenarios and a separate PostgreSQL database for API and transaction scenarios.

Install development dependencies, start PostgreSQL, and run the complete test suite:

```bash
poetry install
docker compose up -d postgres
poetry run pytest -v
```

The PostgreSQL container creates the test database defined by `POSTGRES_TEST_DB` during its first initialization. `TEST_DATABASE_URL` must point to that database and must never point to the application database. The test configuration checks this before connecting.

The transaction test sends simultaneous votes from separate database sessions and verifies that both votes are stored and the proposal reaches the correct final status.

## Database Migrations

Alembic is the only mechanism used to manage the application database schema.

Apply all migrations with:

```bash
docker compose run --rm backend alembic upgrade head
```

## CI/CD

Every push to `main` starts the GitHub Actions workflow:

1. Start an isolated PostgreSQL service.
2. Apply Alembic migrations.
3. Create a separate test database and run the test suite.
4. Build the Docker image and publish it to GitHub Container Registry.
5. Connect to the VPS, apply migrations, and restart the application.
6. Verify the deployment through `/health`.

The image is deployed only after the tests pass.

## Intentional Limitations

This is an educational project with a deliberately limited scope:

- No authentication: author and user IDs are accepted from request data
- No user-management endpoints: proposals reference users that already exist in the database
- No background scheduler: deadline processing occurs during voting actions
- No public endpoint for reading the audit log
- No user interface, notifications, weighted voting, veto rights, quorum rules, or multi-stage approval workflows

These constraints keep the project focused on proposal lifecycle rules, service-layer design, database transactions, testing, and deployment.
