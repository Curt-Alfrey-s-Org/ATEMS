# Repo / Service Host Mapping (SSoT)

**This is the authoritative map of which git repository's services run on which host/VM.**

Every operator and every code change must consult this file before assuming a service lives on a particular IP or hostname (especially anything that used to be "105").

## Goals
- All hosts (and every repo checkout) know where every service/repo is running.
- When a repo/stack is moved (e.g. to a new dedicated Ubuntu VM), this document is updated first.
- Code, `.env` files, compose overrides, nginx configs, docs, and scripts are then updated to match.
- The file is deliberately placed inside **every participating repo** (not only alfa-ai) so that a normal `git pull` on any repo brings the current cluster layout with it.

## Hosts covered (and future hosts)

All of these must have (or will have) a current `alfa-ai` clone and must `git pull --ff-only` before operating or deploying:

- 93 (WOLF1 / gamerx Windows)
- 100 (ALFA-AI)
- 102 (MARKET)
- 103 (ATEMS)
- 105 (UBUNTU-PRO-WEBSITES) — the historical "apps" host; many things remain here
- 106 (ProBilliards)
- 107 (Grafana)
- 111 (gamerboyz / TrueNAS Scale) — hub, brain, LiteLLM, registry, shared storage
- 59 (spartan)
- 219 (destroyer)
- 148 (ai-148 / n4s1)
- 249 (blade)

Add new rows when new VMs or physical hosts are commissioned.

## Current IP allocation (all in 192.168.0.0/24)

| VM label   | IP            | Role |
|------------|---------------|------|
| 100        | 192.168.0.100 | ALFA-AI (moved workloads) |
| 102        | 192.168.0.102 | MARKET (market-pie5-bot) |
| 103        | 192.168.0.103 | ATEMS |
| 105        | 192.168.0.105 | UBUNTU-PRO-WEBSITES (remaining apps + shared infra) |
| 106        | 192.168.0.106 | ProBilliards |
| 107        | 192.168.0.107 | Grafana / monitoring |

## Distribution strategy — the file lives in every repo

**Master copy (authoritative):**
`alfa-ai/docs/REPO_HOST_MAPPING.md`

**Copies for convenience:**
We maintain an up-to-date copy inside each participating repo at:
`<repo>/docs/REPO_HOST_MAPPING.md`

This way, when anyone does a normal `git pull` on contracts-bot, market-pie5-bot, atems, rankings-bot, monitoring, USPBF, alfa-ai, etc., they immediately get the current "where is everything running" picture.

### Recommended update workflow

Since the source clones of all the sibling repos currently live on `.105`:

1. Edit the master on `.105`.
2. Run the sync script (or `cp` manually).
3. Commit + push **from .105 only** in each repo.
4. On every host: `git pull --ff-only` in the repos they care about.

(Full details are inside the document itself once we get it written.)

## Repo / Stack → Host mapping

(You can paste the full table from our previous version here when you create the file.)

---

**Last updated:** 2026-07-01
