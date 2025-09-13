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

## Release Process

This project uses semantic-release for automated versioning and release notes. The release workflow is as follows:

1. **Feature development**: Work on feature branches, squash merge to `develop`
2. **Release preparation**: Cherry-pick commits from `develop` to `release-vX.Y.Z` branch
3. **Release**: Create PR from `release-vX.Y.Z` to `main`
4. **Automated release**: Semantic-release generates version, tags, and release notes

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
