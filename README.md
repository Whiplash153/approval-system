# Approval System (L3)

## Goal

This project implements an approval system where users can create proposals, assign participants, collect votes, and reach a final decision.

The system models a controlled decision-making workflow with proposal lifecycle management, voting deadlines, audit logging, and transactional consistency.

---

## What was done

- Implemented proposal creation with participants validation
- Added participant entity with proposal membership tracking
- Implemented proposal lifecycle with controlled status transitions
- Added proposal editing in draft status
- Added soft deletion of proposals
- Implemented voting and revoting functionality
- Added manual and automatic proposal finishing
- Implemented voting deadlines
- Added audit log for important business actions
- Implemented transactional protection for concurrent voting scenarios
- Added Alembic migrations support
- Implemented API using FastAPI
- Added database layer using SQLAlchemy ORM
- Covered business logic, API, and transaction scenarios with pytest tests

---

## Architecture

The project follows a layered architecture:

- **Router (FastAPI)** — handles HTTP requests and responses
- **Service layer** — contains business logic and lifecycle rules
- **Repository layer** — handles database interactions
- **Models (SQLAlchemy ORM)** — define database structure and relationships
- **Schemas (Pydantic)** — define request and response validation
- **Alembic** — manages database schema migrations

Main domain entities:

- User
- Proposal
- Vote
- Participant
- AuditLog

Business rules are centralized inside the service layer.
Status transitions are controlled through a dedicated transition map.

---

## Business Logic

The system enforces the following rules:

- Proposal lifecycle is controlled by status transitions:
  - draft → voting
  - voting → approved
  - voting → rejected
  - draft/voting/approved/rejected → deleted

- Only the proposal author can:
  - start voting
  - finish voting manually
  - edit a proposal
  - delete a proposal

- Proposal editing is allowed only in draft status

- Only assigned participants can vote

- Participants can change their vote while voting is active

- Voting is allowed only in voting status

- Proposal can finish automatically when:
  - all participants have voted
  - deadline is reached

- Proposal can also be finished manually by the author

- Final result is determined by majority of votes:
  - approve > reject → approved
  - otherwise → rejected

- Deleted proposals are hidden from regular read operations

- Important actions are recorded in audit log

---

## API Overview

Main endpoints:

- `POST /proposals` — create proposal
- `GET /proposals/{id}` — get proposal
- `GET /proposals/{id}/result` — get proposal result
- `GET /proposals/{id}/votes` — get proposal with votes
- `PATCH /proposals/{id}` — update proposal in draft status
- `DELETE /proposals/{id}` — soft delete proposal
- `POST /proposals/{id}/start` — start proposal voting
- `POST /proposals/{id}/finish` — manually finish proposal
- `POST /votes` — create vote
- `PATCH /votes` — change existing vote

---

## Error Handling

The application uses custom domain exceptions to represent business rule violations.

Exceptions are mapped to HTTP responses globally through FastAPI exception handlers.

Response codes:

- `400 Bad Request`
  - InvalidVoteValueError
  - EmptyParticipantsError
  - DuplicateParticipantsError

- `403 Forbidden`
  - NotParticipantError
  - NotAuthorError

- `404 Not Found`
  - ProposalNotFoundError
  - UserNotFoundError
  - VoteNotFoundError

- `409 Conflict`
  - AlreadyVotedError
  - InvalidProposalStatusError

Business logic raises domain-specific exceptions inside the service layer, while HTTP response mapping is handled in the application entry point.

---

## Limitations

The system intentionally does NOT include:

- Authentication and authorization system
- User interface (UI)
- Role-based permissions beyond proposal author and participants
- Weighted voting
- Veto rights
- Quorum rules
- Multi-stage approval workflows
- Background jobs and schedulers
- Notifications

This project focuses on approval workflow lifecycle, voting mechanics, transactional consistency, and clean service-layer architecture.

---

## Run

Create the environment file:

```bash
cp .env.example .env
```

Replace the example username and password in `.env`, then build and start the application:

```bash
docker compose up -d --build
```

Apply database migrations:

```bash
docker compose exec backend alembic upgrade head
```

Open Swagger UI:

```text
http://localhost:8001/docs
```

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

Install development dependencies and run the test suite:

```bash
poetry install
poetry run pytest -v
```

Tests use the separate database configured by `TEST_DATABASE_URL`. Never point
`TEST_DATABASE_URL` to the application database.
