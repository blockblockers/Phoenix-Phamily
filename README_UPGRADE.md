# v3.1 upgrade — owner names, history labels, 1,200-word recap

## Replace in your repository
Replace `collector.py` and `recap_instructions.md`. Add `legacy/archive.json` and `legacy/identities.json` from this ZIP. Keep your existing secrets, `owner_overrides.json`, and weekly workflow. Optional: `legacy/identity_review.json` identifies ambiguous ownership.

## How owner names work
The collector uses the authenticated ESPN `mTeam` member directory to resolve a stable member ID to `firstName` + `lastName`. It does not fall back to ESPN usernames or emails. If ESPN does not expose a verified human name, the owner is null and the recap uses only the team name. Explicit manual overrides still take precedence. ESPN may change its API; missing names do not stop the report.

## Historical data limitations
The supplied archive has season rosters for 2013–2025 but no box scores for 2013–2018 (`espn_api` limitation). Recorded rivalry statistics cover only fetched games from 2019–2025. Current owner/team identities were inferred from ESPN IDs in the supplied archive; co-managed teams may remain unresolved. Do not call those stats all-time.

## NFL news enrichment
The collector cannot independently verify external NFL news. It outputs a checklist; provide verified NFL game logs/news to the recap author (or build a separate source-backed enrichment step). The editorial rules prohibit fabricating game-log statistics.

## Check
Run `python -m py_compile collector.py` and your existing GitHub weekly workflow. Review the resulting `reports/week-NN.md` and JSON. No credentials are bundled.
