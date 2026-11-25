# Notes for subsequent tasks

## Remove the `conventional-changelog-conventionalcommits@9` pin

- **Where:** `.github/workflows/semantic-release.yaml`, step "Install semantic-release and plugins".
- **Why pinned:** `conventional-changelog-conventionalcommits` 10.x (since 2026-06-26) requires `conventional-changelog-writer@9`, but `@semantic-release/release-notes-generator` 14.x (shipped with semantic-release 25) still uses writer 8. With the unpinned preset, the "generateNotes" step fails on every Node version with `Missing helper: "conventional-changelog-conventionalcommits requires conventional-changelog-writer@9 or newer ..."`.
- **When to remove:** once a stable `@semantic-release/release-notes-generator` 15.x is released (only 15.0.0 betas existed as of 2026-11-10) and the `semantic-release` version installed by the workflow uses it.
- **How to verify:** `npm view semantic-release dependencies` shows release-notes-generator `^15`. Then run `npx semantic-release --dry-run --no-ci` with the unpinned preset on a throwaway clone and check that "generateNotes" completes.
