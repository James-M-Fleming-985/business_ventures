# Deployment Versioning System

This project uses semantic versioning matching the pattern from `life_quality` project.

## Version Format

`MAJOR.MINOR.PATCH` (e.g., 2.0.14)

- **MAJOR**: Breaking changes or major feature releases
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, minor improvements

## Current Version

The current version is stored in the `VERSION` file at the project root.

## Version Management

### Using the bump_version.py script:

```bash
# Show current version
python bump_version.py show

# Increment patch version (2.0.14 → 2.0.15)
python bump_version.py patch

# Increment minor version (2.0.14 → 2.1.0)
python bump_version.py minor

# Increment major version (2.0.14 → 3.0.0)
python bump_version.py major

# Set specific version
python bump_version.py set 2.0.15
```

### Manual workflow:

1. **Before making changes**: Note the current version

2. **After completing changes**: Bump the version
   ```bash
   python bump_version.py patch  # or minor/major
   ```

3. **Commit with version tag**:
   ```bash
   git add -A
   git commit -m "v2.0.15: Fix leaderboard property names and network data structure"
   ```

4. **Deploy**:
   ```bash
   railway up
   ```
   Or Railway will auto-deploy from GitHub pushes

## Deployment History

Railway displays deployment history with your Git commit messages, showing version numbers like:

```
✅ v2.0.14: Fix leaderboard property names (r/p) and network data structure
✅ v2.0.13: Fix network endpoint data structure
✅ v2.0.12: Fix modal timeseries data access
```

## Version Display

The version number is displayed in:

1. **Dashboard Footer**: Shows `Causal Affect Platform v2.0.14 | Last deployed: 2025-11-14`
2. **API Health Endpoint**: `/health` returns version info
3. **API Docs**: Swagger UI shows version in header
4. **Railway Console**: Deployment list shows Git commit messages with versions

## Best Practices

- ✅ **Always use descriptive commit messages** with version tag
- ✅ **Format**: `vX.Y.Z: Brief description of change`
- ✅ **Bump version before committing** changes
- ✅ **Use patch** for bug fixes
- ✅ **Use minor** for new features
- ✅ **Use major** for breaking changes

## Examples

```bash
# Bug fix workflow
python bump_version.py patch
git add -A
git commit -m "v2.0.15: Fix Alpine.js leaderboard rendering"
railway up

# New feature workflow
python bump_version.py minor
git add -A
git commit -m "v2.1.0: Add cryptocurrency data source integration"
railway up

# Breaking change workflow
python bump_version.py major
git add -A
git commit -m "v3.0.0: Migrate to PostgreSQL and refactor API structure"
railway up
```

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 2.0.14 | 2025-11-14 | Fix leaderboard property names (r/p) and network data structure |
| 2.0.13 | 2025-11-14 | Fix network endpoint nested data structure |
| 2.0.12 | 2025-11-14 | Fix modal timeseries data access pattern |

---

*This versioning system matches the pattern used in the life_quality project for consistency across repositories.*
