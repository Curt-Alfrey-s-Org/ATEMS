# AI governance (consumer stub)

**Canonical source:** [alfa-ai `docs/AI_GOVERNANCE.md`](https://github.com/Curt-Alfrey-s-Org/alfa-ai/blob/main/docs/AI_GOVERNANCE.md)

This consumer repo follows the ALFa cluster AI oversight model:

- **L1 default:** programmatic routing; AI enriches and suggests only.
- **L2 mutate:** human Approve before any SSH, settings, or remediation apply.
- **L3 auto-fix:** off by default; allowlisted playbooks only after drills.

Consumer bots do not implement host actions or incident remediation. They call the
shared LiteLLM gateway over HTTP with env-configured model aliases.

Standards extracts: alfa-ai `docs/standards/README.md`.

Autonomy matrix: alfa-ai `docs/AI_AUTONOMY_AND_OVERSIGHT.md`.

Do not duplicate the full governance doc here — link and comply with env boundaries.
