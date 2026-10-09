# Contributing

## Branching Strategy — GitHub Flow with a `develop` integration branch

- `main` — always deployable. Only receives merges from `develop` via a
  release PR, or hotfixes.
- `develop` — integration branch. Each milestone's feature branches merge
  here first.
- `feature/<milestone-number>-<short-name>` — e.g. `feature/02-accounts-auth`.
  Branched from `develop`, merged back via PR once its milestone is approved.
- `hotfix/<short-name>` — branched from `main` for urgent production fixes,
  merged into both `main` and `develop`.

We use this instead of full Git Flow (no separate `release/*` branches) because
at this project's scale, release branches add process overhead without a
matching benefit — `develop` itself is the release candidate.

## Commit Convention — Conventional Commits

```
<type>(<scope>): <short summary>

<body: what changed and why>

<footer: breaking changes, issue refs>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`, `build`.

Example:
```
feat(scraping): add Playwright-based scraper strategy

Implements the PlaywrightScraper class conforming to the BaseScraper
interface introduced in apps/scraping/strategies.py. Handles JS-rendered
pages that BeautifulSoup alone cannot parse.

Refs: #14
```

## Pull Requests

Every milestone ships as one PR from its feature branch into `develop`,
containing:
- A summary of what the milestone delivers
- Architecture decisions made and alternatives considered
- Test coverage added
- Screenshots (for UI-facing milestones)
- A checklist confirming lint/type/test CI is green

## Code Review Checklist

- [ ] No business logic in views/serializers
- [ ] All new models have tests + factories
- [ ] All new endpoints documented in OpenAPI schema
- [ ] No magic numbers/strings — use constants or enums
- [ ] Type hints on all new functions
- [ ] Docstrings on all public classes/functions
- [ ] No N+1 queries introduced (checked via `django-debug-toolbar` in dev)
