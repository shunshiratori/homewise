# Repository Guidelines

## Project Structure & Module Organization

Homewise is currently an initial repository containing only `README.md`. No application source, tests, assets, or dependency manifests have been committed. Keep the README updated as the project takes shape. When introducing code, group related modules together and document the chosen directory layout; use dedicated directories such as `src/`, `tests/`, and `assets/` where appropriate.

## Build, Test, and Development Commands

There are currently no configured build, test, lint, or development commands. Do not assume that `npm test`, `bun run dev`, or similar commands are available. When adding a toolchain, define reproducible commands in its configuration and document prerequisites, installation, local development, testing, and production builds in `README.md`.

Useful checks at this stage:

- `git status --short`: inspect pending changes.
- `git diff --check`: detect whitespace errors in tracked changes.
- `git diff`: review modifications before committing.

## Coding Style & Naming Conventions

No language, formatter, or indentation standard has been established. Follow the conventions of the language selected and commit formatter or linter configuration alongside the first implementation. Use descriptive filenames and identifiers, consistent indentation within each file, and concise Markdown headings in documentation.

## Testing Guidelines

No testing framework or coverage threshold exists yet. Introduce tests with executable functionality and document the test command. Use descriptive test names that identify behavior and expected outcomes. Cover meaningful success paths, edge cases, and failure handling.

## Commit & Pull Request Guidelines

Git history contains only `Initial commit`, so no recurring message convention is established. Write concise, imperative commit subjects, such as `Add household setup flow`. Keep changes focused.

Pull requests should describe the purpose, summarize behavior changes, and report verification performed or explain why checks were unavailable. Link related issues when applicable and include screenshots for visible UI changes.

## Security & Configuration

Never commit credentials or local secrets. When configuration is introduced, document required variables using placeholder values and ignore local environment files.
