
# Persistent Key-Value Database

A command-line persistent key-value database developed in Python for CSCE 4350 at the University of North Texas.

The project implements a custom list-based index and append-only storage without relying on Python's built-in dictionary or map types for indexing.

## Features

- SET and GET: Store and retrieve values
- DEL and EXISTS: Delete keys and check existence
- MSET and MGET: Store and retrieve multiple values
- EXPIRE and TTL: Manage key expiration
- RANGE: Retrieve keys in lexicographical order
- BEGIN, COMMIT, ABORT: Transaction support
- HSET, HGET, HGETALL: Hash operations
- LPUSH, RPUSH, LRANGE, LPOP: List operations
- INCR and DECR: Numeric counters
- FLUSHDB: Clear database contents
- Persistent append-only storage and recovery

## Requirements

- Python 3.13 or compatible Python 3 version
- No third-party dependencies required to run the database

## Running the Database

Open Terminal in the project directory and run:

```bash
python3 -u main.py
```

Example:

```text
SET name Janak
OK
GET name
Janak
SET university UNT
OK
GET university
UNT
EXIT
```

## Database Architecture

The database uses a custom list-based in-memory index.

Each key is located using a manually implemented linear search rather than a built-in dictionary.

Write operations are recorded in an append-only file named `data.db`.

When the program restarts, it replays the log to rebuild the in-memory database state.

Transactions buffer operations until COMMIT, while ABORT discards uncommitted changes.

## Automated Testing

Run all unit tests:

```bash
python3 -m unittest discover -v
```

Install Ruff for linting:

```bash
python3 -m pip install ruff
```

Run the linter:

```bash
python3 -m ruff check .
```

The project includes 14 automated unit tests.

## GitHub Actions

GitHub Actions automatically runs Python tests and Ruff linting when changes are pushed to the repository.

## Project Structure

- `main.py` - Command-line interface
- `database.py` - Database implementation
- `test_database.py` - Automated tests
- `pyproject.toml` - Ruff configuration
- `.github/workflows/python-tests.yml` - CI workflow
- `gradebot_screenshot.png` - Gradebot evaluation screenshot

## Gradebot Evaluation

The project was evaluated using the CSCE 4350 Project 1 Gradebot.

**Gradebot Score: 99.25%**

All functional and project checks received full points.

The only deduction was in the subjective code-quality evaluation.

See `gradebot_screenshot.png` for the complete grading results.

## Author

Janak Karki

University of North Texas

CSCE 4350
