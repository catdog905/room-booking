# Contributing guide


## Development flow

1. Create a new branch for your feature/fix/etc.
2. Write, test, and commit (with any descriptive message format) your code
3. Create a pull request to main
4. Make sure all checks are passed
5. Make sure your branch is up-to-date with `main` and there are no conflicts
6. Wait until your code will be reviewed and merged into `main`


### To remember

- One PR must introduce a small change/addition. If it can be split into smaller
  pieces, split it and create a single PR for each piece.
- All PRs are squashed before merging, commit message is updated to follow the
  [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/), so 
  each merged PR will appear as a single commit in the `main` branch, all with
  consistent commit messages.


## Running project locally

<details>
<summary>Step 1. Make sure all necessary tools are installed</summary>

- [Python 3.11+](https://www.python.org/)
- [Poetry](https://python-poetry.org/)

</details>

<details>
<summary>Step 2. Install dependencies</summary>

```shell
poetry install
```

</details>

<details>
<summary>Step 3. Run the development server</summary>

```shell
poetry run uvicorn app.main:app --reload
```

</details>

## Project structure

```text
./                 Root of the project
├─ app/              Source code of the application
│  ├─ api/             FastAPI-related code (routers, dependencies, etc.)
│  ├─ domain/          Business logic code (must depend only on abstractions from ./deps)
│  │  ├─ deps/           Abstract dependencies (not FastAPI) that business logic relies on
│  │  ├─ entities/       Entities that business logic operates with
│  │  ├─ use_cases/      Business logic methods — core of the application
│  ├─ adapters/        Business-logic dependencies implementation
│  ├─ main.py        Entry-point of the app
```

- [A good article about clean architecture](https://medium.com/codex/clean-architecture-for-dummies-df6561d42c94)
