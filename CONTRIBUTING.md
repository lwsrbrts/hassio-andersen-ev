# Contributing

Thanks for your interest in contributing to the Andersen EV Home Assistant integration!

## Branch model

The primary branch is **`main`** — the stable trunk. Contributions normally target `main` via pull
request; direct pushes are not used.

**`develop`** is an *optional* beta/staging branch. It is used only when a change should first go out
as a `-beta.N` prerelease for testing before it lands on `main`. In that case the change is merged to
`develop` (which publishes a beta prerelease), tested, and then `develop` is promoted to `main` for the
stable release. When no beta is needed, PRs go straight to `main`.

Contributor flow: fork the repo -> create a feature branch -> open a PR into `main` (or into
`develop` if you want a beta test first).

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/) are required. Common types used in
this repo:

* `feat` — a new feature
* `fix` — a bug fix
* `docs` — documentation-only changes
* `ci` — changes to CI configuration or workflows
* `chore` — maintenance work that isn't a fix or feature (tooling, deps, config)
* `build` — changes to the build/packaging process
* `test` — adding or correcting tests
* `refactor` — code changes that neither fix a bug nor add a feature

Examples:

```
fix: resolve userLock desync when Andersen omits lock state
feat: add sensor for charger fault code
```

These commit types drive automated version bumps and changelog generation, so please use them
accurately.

## Local development

See the README's [Development](README.md#development) section for full details. In short:

* The repo ships a devcontainer (VS Code "Reopen in Container") for a full Linux test suite
  matching CI.
* Run tests with `pytest` from the repo root; lint/format with `ruff` (config at
  `custom_components/andersen_ev/ruff.toml`, line length 120).
* Enable pre-commit hooks with `pre-commit install` — see the README "Development" section for
  details.

## Releases & versioning

This project follows [Semantic Versioning](https://semver.org/). Merges to `main` cut stable
releases. When a change should be beta-tested first, merging it to the optional `develop` branch
cuts a `-beta.N` prerelease; promoting `develop -> main` then cuts the stable release. Both are
produced automatically by `release-please` (landing in an upcoming PR). Until that automation is in
place, versions are bumped manually in `custom_components/andersen_ev/manifest.json`.
