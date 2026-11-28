# Contributing Guidelines

## Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to ensure consistent and meaningful commit messages that enable automated release notes generation.

### Required Format and Case Sensitivity

```git
<type>(<scope>): <Description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Release Impact |
|------|-------------|----------------|
| `feat` | New features | Minor version bump |
| `fix` | Bug fixes | Patch version bump |
| `perf` | Performance improvements | Patch version bump |
| `docs` | Documentation changes | No release |
| `ci` | CI/CD configuration changes | No release |
| `build` | Build system changes | No release |
| `test` | Adding or updating tests | No release |
| `refactor` | Code refactoring | No release |
| `style` | Code style changes (formatting, etc.) | No release |
| `chore` | Maintenance tasks | No release |

### Scope Guidelines

The scope is optional but recommended for clarity. Use lowercase and keep it concise:

- `auth` - Authentication and authorization
- `docker` - Docker configuration and images
- `api` - API endpoints and logic
- `ui` - User interface components
- `database` - Database schema and queries
- `release` - Release and deployment processes
- `docs` - Documentation

### Description Guidelines

The description should be concise, using imperative mood (e.g., "Add", "Fix", "Update"). It should start with a capital letter and not end with a period.

### Breaking Changes

For breaking changes, add `!` after the type/scope or include `BREAKING CHANGE:` in the footer:

```bash
feat(api)!: redesign user authentication endpoints

BREAKING CHANGE: User authentication endpoints have been completely redesigned.
The old /auth/login endpoint has been replaced with /api/v2/auth/authenticate.
```

### Examples

**Good commit messages:**

```bash
feat(auth): Add user authentication system
fix(docker): Resolve container startup issue
docs(readme): Update installation instructions
ci(release): Add automated release workflow
perf(database): Optimize user query performance
test(auth): Add integration tests for login flow
```

**Bad commit messages:**

```bash
✗ Add feature           # Missing type and scope
✗ Fix bug              # Too vague, missing scope
✗ Update documentation # Missing conventional format
✗ WIP                  # Not descriptive
```

## Quick Setup (Recommended)

### Pre-commit Hooks (Primary Validation)

Install Python >= 3.9 as a prerequisite.

Install pre-commit hooks for immediate feedback:

```bash
# Install pre-commit (one-time setup)
pip install pre-commit

# Install project hooks (run in project directory)
pre-commit install --config .pre-commit/.pre-commit-config.yaml
pre-commit install --hook-type commit-msg --config .pre-commit/.pre-commit-config.yaml

# Test the setup (optional)
pre-commit run --config .pre-commit/.pre-commit-config.yaml --all-files
```

### Bypassing Validation (Not Recommended)

In rare cases, you can bypass pre-commit hooks:

```bash
# Skip all pre-commit hooks (use sparingly)
git commit --no-verify -m "emergency fix"
```

**Note:** GitHub Actions will still validate these commits in PRs.

## Branching and Release Process

This project follows a simplified Gitflow and uses semantic-release for automated versioning and release notes.

```text
feature/* ──→ develop ──→ main
                           ↑
              hotfix/* ────┘
```

| Branch | Purpose |
| --- | --- |
| `main` | Production releases, always deployable |
| `develop` | Integration branch and staging area |
| `feature/*` | New features and enhancements; delete after merge to `develop` |
| `hotfix/*` | Production bug fixes; delete after merge to `main` |

| Transition | Method | PR required |
| --- | --- | --- |
| `feature/*` → `develop` | Direct merge with `--no-ff` | No |
| `develop` → `main` | Pull request, merge commit | **Yes** — the quality gate |
| `hotfix/*` → `main` | Pull request | **Yes** |
| `main` → `develop` | Merge (post-release sync) | No |

### Feature Development

```bash
git checkout develop && git pull origin develop
git checkout -b feature/my-feature

# ... work, committing with conventional commits ...

# Optional: tidy up commits before merging
git rebase -i develop

git checkout develop && git pull origin develop
git merge --no-ff feature/my-feature
git push origin develop
git branch -d feature/my-feature
```

**Do not squash-merge.** Squashing collapses separate `feat:`, `fix:`, and `test:` commits into
one, and semantic-release may then miss the version bump. `--no-ff` preserves each conventional
commit and creates a merge commit that marks the feature boundary, so the whole feature can be
reverted with a single `git revert`.

Feature branches need no PR — the quality gate is at `develop` → `main`, where it matters.

### Release

Create a PR from `develop` to `main`. This is the quality gate and is always required:

```bash
gh pr create --base main --head develop --title "Release: [describe release]"
```

Use a standard merge commit, not squash or rebase, so individual conventional commits survive
for semantic-release to analyse. Once merged, semantic-release determines the version, creates
the git tag, publishes the GitHub release, and generates the changelog. The tag then triggers
the binary and Docker builds.

### Hotfix

For critical production bugs that cannot wait for the normal cycle, branch from `main`, open a
PR back into `main`, then sync the fix into `develop`.

### Post-Release Sync

After anything lands on `main`, merge it back so `develop` does not fall behind:

```bash
git checkout main && git pull origin main
git checkout develop && git merge main && git push origin develop
```

Always merge, never rebase.

### Enhancing Release Notes

For richer release notes, include detailed information in commit bodies:

```bash
feat(dashboard): Implement user analytics dashboard

* Real-time user activity metrics
* Customizable dashboard widgets
* Export functionality for reports
* Mobile-responsive design
```

## Troubleshooting

### Pre-commit Issues

**Pre-commit hooks not running:**

```bash
# Reinstall hooks
pre-commit uninstall --config .pre-commit/.pre-commit-config.yaml
pre-commit install --config .pre-commit/.pre-commit-config.yaml

# Verify installation
pre-commit --version
```

**Node.js/npm errors with commitlint:**

```bash
# Clear npm cache and reinstall
npm cache clean --force
pre-commit clean
pre-commit install
```

**Permission errors:**

```bash
# Fix permissions (Unix/Linux/Mac)
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

## Questions?

If you have questions about the commit format or contribution process, please:

1. Check the automated validation feedback in failed CI runs
2. Review existing commits for examples
3. Refer to [Conventional Commits specification](https://www.conventionalcommits.org/)
4. Open an issue for clarification
