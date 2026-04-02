# Server worktree commit — 2026-04-02

Snapshot generated on the server immediately before `git add` / commit / push.
Purpose: document everything that was pending in the working tree for this repository.

## Branch tracking
## main...origin/main
 M .env.example
 M .gitignore
 M DEPLOY_NOW.md
 M Dockerfile
 M POSTGRESQL_MIGRATION.md
 M POSTGRESQL_MIGRATION_COMPLETE.md
 M POSTGRESQL_MIGRATION_SUMMARY.md
 M README.md
 M ROADMAP.md
 D TRAEFIK_ATEMS.md
 D TRAEFIK_TO_NGINX_MIGRATION_2026.md
 M atems.py
 M deploy_atems_postgres.sh
 M docker-compose.yml
 M docs/ATEMS_IMPROVEMENTS.md
 M docs/USER_GUIDE.md
 M frontend/src/api/client.ts
 M routes.py
 M scripts/deploy-to-server.sh
 M static/app/index.html
 M tests/test_error_patterns.py
 M tests/test_http_and_api.py
 M verify_postgres_migration.sh
 M web-sites-server/DEPLOY_NOW.md
 M web-sites-server/PORT_INFO.md
 M web-sites-server/README.md
 D web-sites-server/TRAEFIK_ATEMS.md
?? CONTRIBUTING.md
?? IMPROVEMENTS_FROM_RANKINGS.md
?? MYSQL_CREDENTIAL_CHANGE.md
?? docs/INDEX.md
?? docs/SERVER_COMMIT_2026-04-02.md
?? scripts/export_compose_uid_gid.sh
?? static/app/assets/index-D-71gkuN.js
?? utils/api_error_handlers.py

## Unstaged/staged diff stat (before `git add`)
 .env.example                       |   3 +
 .gitignore                         |   1 +
 DEPLOY_NOW.md                      |   4 +-
 Dockerfile                         |   2 +-
 POSTGRESQL_MIGRATION.md            |   8 +-
 POSTGRESQL_MIGRATION_COMPLETE.md   |  14 ++--
 POSTGRESQL_MIGRATION_SUMMARY.md    |   6 +-
 README.md                          |   9 +++
 ROADMAP.md                         |  40 +++++++++-
 TRAEFIK_ATEMS.md                   | 123 ----------------------------
 TRAEFIK_TO_NGINX_MIGRATION_2026.md | 160 -------------------------------------
 atems.py                           |   4 +
 deploy_atems_postgres.sh           |  54 +++++++++----
 docker-compose.yml                 |  14 +++-
 docs/ATEMS_IMPROVEMENTS.md         |   2 +-
 docs/USER_GUIDE.md                 |   2 +-
 frontend/src/api/client.ts         |  16 ++++
 routes.py                          |  19 ++++-
 scripts/deploy-to-server.sh        |   2 +-
 static/app/index.html              |   2 +-
 tests/test_error_patterns.py       |   3 +-
 tests/test_http_and_api.py         |  13 ++-
 verify_postgres_migration.sh       |  18 +++--
 web-sites-server/DEPLOY_NOW.md     |  10 +--
 web-sites-server/PORT_INFO.md      |  12 +--
 web-sites-server/README.md         |   7 +-
 web-sites-server/TRAEFIK_ATEMS.md  | 112 --------------------------
 27 files changed, 198 insertions(+), 462 deletions(-)

## Untracked files (first 400 lines)
CONTRIBUTING.md
IMPROVEMENTS_FROM_RANKINGS.md
MYSQL_CREDENTIAL_CHANGE.md
docs/INDEX.md
docs/SERVER_COMMIT_2026-04-02.md
scripts/export_compose_uid_gid.sh
static/app/assets/index-D-71gkuN.js
utils/api_error_handlers.py

## Recent commits (last 5)
ebd2c4b chore: cleanup and network/nginx updates
7bf3ca6 ROADMAP: add Option B (mount frontend) for tomorrow; clean up for fresh start
2be21aa Cleanup: Remove .venv, logs, and build artifacts (193MB freed)
8233d46 Performance optimizations: Add self-test suite, performance monitoring, update documentation and UI
8eec8c1 Merge remote ATEMS, keep splash login and local updates
