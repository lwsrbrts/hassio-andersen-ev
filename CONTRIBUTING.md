# Contributing

Thanks for your interest in contributing to the Andersen EV Home Assistant integration!

## Branch model

**`main`** is the sole trunk and the stable release branch. All work lands on `main` through pull
requests; it is branch-protected and direct pushes are not used.

Contributor flow: fork the repo -> create a feature branch -> open a PR into `main`.

Betas are cut on demand via the "Cut beta" GitHub Actions workflow (`workflow_dispatch`). See
"Releases & versioning" below for how betas and stable releases are produced.

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

This project follows [Semantic Versioning](https://semver.org/). `release-please` is now active.
Merges to `main` are driven by Conventional Commits: `release-please` maintains a rolling release PR
that bumps the version in `custom_components/andersen_ev/manifest.json`, updates `CHANGELOG.md`, and
tags `vX.Y.Z` when merged. Merging that release PR promotes the change to a stable release.

To beta-test a change before promoting it, run the "Cut beta" workflow to publish a
`vX.Y.Z-beta.N` pre-release. Enable HACS "Show beta versions" for this repository to receive it;
stable users are unaffected.
