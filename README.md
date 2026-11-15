# PipeKeeper

Self-healing data pipelines, running 24/7 on free infrastructure (GitHub Actions) — no servers of ours to break.

## What this is
- **Collectors** (`collectors/`): pull data from public sources on a schedule
- **Data** (`data/`): collected output, committed fresh every run
- **Workflows** (`.github/workflows/`): the hourly schedule + health monitor
- **Status page**: coming next — live view for clients

## Why this architecture
- No single machine the business depends on (runs on GitHub's fleet)
- $0 cost, no card required
- Auto-retry on failure, full version history of every change
