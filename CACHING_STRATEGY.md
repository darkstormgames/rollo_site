# Caching Strategy Documentation

This document outlines the comprehensive caching strategy implemented for the Rollo Monorepo CI/CD workflows to reduce pipeline execution times and improve developer productivity.

## Overview

The caching strategy implements multi-layered caching across all technologies in the monorepo:
- **Node.js/npm** (Rollo Site Angular app, SSO Express.js service)
- **Python/pip** (VM Service FastAPI)
- **Build artifacts** (compiled TypeScript, SCSS, Python bytecode)

## Cache Strategy Components

### 1. Dependency Caching

#### npm Dependencies
```yaml
# Root level dependencies
path: |
  ~/.npm
  node_modules
key: v1-ubuntu-latest-npm-root-{{ hashFiles('package-lock.json') }}

# App-specific dependencies
path: |
  ~/.npm
  apps/{app}/node_modules
key: v1-ubuntu-latest-npm-{app}-{{ hashFiles('apps/{app}/package-lock.json') }}
```

#### Python Dependencies
```yaml
path: |
  ~/.cache/pip
  apps/vm-service/venv
key: v1-ubuntu-latest-python-{{ hashFiles('apps/vm-service/requirements.txt') }}
```

### 2. Build Artifact Caching

#### Angular/TypeScript Compilation
```yaml
path: |
  apps/rollo-site/dist
  apps/rollo-site/.angular
key: v1-ubuntu-latest-build-rollo-site-{{ hashFiles('apps/rollo-site/src/**/*') }}
```

#### SCSS Compilation
```yaml
path: |
  apps/rollo-site/dist/**/*.css
  apps/rollo-site/.angular/cache
key: v1-ubuntu-latest-scss-{{ hashFiles('apps/rollo-site/src/**/*.scss', 'packages/shared-styles/**/*.scss') }}
```

#### Python Bytecode
```yaml
path: |
  apps/vm-service/**/__pycache__
  apps/vm-service/**/*.pyc
key: v1-ubuntu-latest-python-bytecode-{{ hashFiles('apps/vm-service/src/**/*.py') }}
```

## Cache Key Strategy

### Primary Keys
Primary cache keys use content hashes of dependency files for precise invalidation:
- `package-lock.json` hash for npm dependencies
- `requirements.txt` hash for pip dependencies
- Source file hashes for build artifacts

### Restore Keys (Fallbacks)
Hierarchical fallback keys enable partial cache restoration:
```yaml
restore-keys: |
  v1-ubuntu-latest-npm-rollo-site-
  v1-ubuntu-latest-npm-
  v1-ubuntu-latest-
```

### Cache Versioning
- `CACHE_VERSION` environment variable (default: `v1`)
- Allows manual cache busting when needed
- Increment for major dependency or tooling changes

## Workflows

### 1. Main CI/CD Pipeline (`ci.yml`)
- **Trigger**: Push/PR to main/develop branches
- **Purpose**: Primary build, test, and validation
- **Caching**: Full dependency and build artifact caching
- **Features**: 
  - Parallel job execution with shared caches
  - Cache hit reporting in job summaries
  - Integration test validation

### 2. Build and Cache (`build-and-cache.yml`)
- **Trigger**: Push to main branch
- **Purpose**: Comprehensive artifact building and caching
- **Features**:
  - Matrix strategy for all apps
  - Performance benchmarking
  - Build artifact uploading

### 3. Cache Management (`cache-management.yml`)
- **Trigger**: Weekly schedule + manual dispatch
- **Purpose**: Cache warm-up and maintenance
- **Features**:
  - Scheduled cache population
  - Manual cache refresh option
  - Cache version bumping
  - Performance monitoring

## Performance Targets

### Time Reduction Goals
- **Target**: 50% reduction in average workflow time
- **Baseline**: Without caching (first run)
- **Optimized**: With cache hits on subsequent runs

### Cache Hit Rate Goals
- **Target**: >80% cache hit rate for regular commits
- **Measurement**: Tracked in workflow summaries
- **Monitoring**: Weekly cache management reports

## Usage Instructions

### For Developers

#### Normal Development
No special actions required - caching works automatically on push/PR.

#### Troubleshooting Build Issues
1. Check workflow summary for cache hit rates
2. Review dependency changes that might invalidate caches
3. Use cache management workflow for refresh if needed

### For Maintainers

#### Manual Cache Busting
```bash
# Option 1: Use workflow dispatch
# Go to Actions > Cache Management > Run workflow
# Enable "Bump cache version"

# Option 2: Update workflow files
# Change CACHE_VERSION from v1 to v2 in workflow files
```

#### Cache Monitoring
- Weekly automatic cache warm-up runs
- Performance reports in workflow summaries
- GitHub's 10GB cache limit monitoring

## Cache Size Management

### Current Cache Allocation
- **npm dependencies**: ~200-500MB per app
- **Python dependencies**: ~100-300MB
- **Build artifacts**: ~50-200MB per app
- **Total estimated**: 1-2GB (well under 10GB limit)

### Cleanup Strategy
- GitHub automatically removes caches not accessed in 7 days
- Cache versioning allows manual cleanup of old versions
- Regular monitoring via cache management workflow

## Best Practices

### Cache Key Design
1. Use content hashes for precise invalidation
2. Implement hierarchical fallback keys
3. Include cache version for manual control
4. Separate concerns (deps vs. build artifacts)

### Workflow Optimization
1. Parallel job execution where possible
2. Share caches between related jobs
3. Cache validation before expensive operations
4. Upload important artifacts for debugging

### Monitoring and Maintenance
1. Regular cache hit rate monitoring
2. Performance benchmark tracking
3. Proactive cache warm-up scheduling
4. Documentation updates with changes

## Troubleshooting Guide

### Common Issues

#### Cache Misses
**Symptoms**: Workflows taking longer than expected
**Causes**: 
- Dependency file changes
- Cache eviction due to age/size limits
- Cache key mismatches

**Solutions**:
1. Check workflow logs for cache restoration
2. Verify dependency file changes in commits
3. Run cache warm-up workflow
4. Consider cache version bump if persistent

#### Build Failures with Cache
**Symptoms**: Builds failing after cache restoration
**Causes**:
- Stale cached dependencies
- Version mismatches
- Corrupted cache entries

**Solutions**:
1. Run workflow with force cache refresh
2. Bump cache version to start fresh
3. Check for breaking changes in dependencies

#### Cache Storage Limits
**Symptoms**: Older caches being evicted unexpectedly
**Causes**:
- Approaching GitHub's 10GB limit
- Too many cache variants

**Solutions**:
1. Review cache usage in repository settings
2. Optimize cache key strategies
3. Clean up old cache versions

### Manual Recovery Steps

#### Complete Cache Reset
1. Bump `CACHE_VERSION` in all workflow files
2. Run cache management workflow with version bump
3. Verify new caches populate successfully

#### Selective Cache Refresh
1. Use cache management workflow dispatch
2. Enable "Force refresh all caches"
3. Monitor subsequent workflow performance

## Future Enhancements

### Potential Improvements
1. **Docker Layer Caching**: For containerized deployments
2. **Test Result Caching**: Cache test outputs for faster re-runs
3. **Incremental Builds**: Smart build artifact caching
4. **Cross-Platform Caching**: Optimize for multiple OS runners

### Monitoring Enhancements
1. **Cache Analytics**: Detailed hit/miss ratio tracking
2. **Performance Dashboards**: Workflow time trend analysis
3. **Automated Optimization**: Dynamic cache key adjustment
4. **Cost Analysis**: GitHub Actions minutes savings tracking

## References

- [GitHub Actions Cache Documentation](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [actions/cache Repository](https://github.com/actions/cache)
- [Workflow Performance Best Practices](https://docs.github.com/en/actions/using-workflows/about-workflows#best-practices-for-using-workflows)