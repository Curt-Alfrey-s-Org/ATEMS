# Docker build pattern — atems

**This repo's default:** Pattern A — server-side dep cache at `/srv/dep-cache`.

Every `Dockerfile` and every build script in this repo must pull its pip /
npm / apt deps through the shared BuildKit cache mounts (ids: `bots-pip`,
`bots-apt`, `bots-apt-lists`, `bots-npm`) or via
`npm_config_cache=/srv/dep-cache/npm` for host / `docker run` builds. No
plain `RUN pip install` / `npm ci` without a cache mount.

See the canonical spec for recipes, ids, prerequisites, and verification:

→ [`/home/ansible/docs/DOCKER_BUILD_PATTERNS.md`](../docs/DOCKER_BUILD_PATTERNS.md)
  (section "Pattern A — Server-side dep cache")

## When to ask about pattern B (TrueNAS hub) instead

An agent MUST ask the user which pattern to use if the build:

- Pulls CUDA-specific wheels, HuggingFace model shards, Ollama blobs, or any
  single artifact ≥ 200 MB.
- Will run on a cluster worker that must not touch the public internet.

Otherwise, stay on pattern A (server cache).

## Quick verification

```bash
/srv/dep-cache/bin/dep-cache status   # sizes + last-used per shared cache
```

After any rebuild, `bots-pip` / `bots-npm` / `bots-apt*` should grow (new pin)
or stay flat (everything cached). If those lanes are stuck at 0, the cache
mount wasn't applied — check the `# syntax=docker/dockerfile:1` header and
the `--mount=type=cache,id=bots-*` lines.
