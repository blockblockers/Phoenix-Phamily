# Phoenix Phamily ESPN Recap Collector — v2

Private ESPN league **1106154**, season **2026**. GitHub Actions runs Tuesday 9:15 a.m. Phoenix time. Does not generate prose via API; creates a research brief for ChatGPT.

## Upgrade from v1

Upload and overwrite `collector.py`, `README.md`, `.github/workflows/weekly.yml`, `requirements.txt`, `.gitignore`; add `owner_overrides.json` and `recap_instructions.md`. Keep the existing GitHub Actions secrets `ESPN_S2` and `ESPN_SWID`. Never paste cookies into GitHub code or ChatGPT.

## Run

GitHub → Actions → **Phoenix Phamily weekly stats** → Run workflow → optional `week` (completed week only). Download artifact `phoenix-phamily-weekly-report`. Upload `week-XX.md` and optionally `week-XX.json` to ChatGPT with `recap_instructions.md`. Ask for NFL news research for that week before drafting.

Local: `pip install -r requirements.txt` then set environment variables `ESPN_S2` and `ESPN_SWID` securely and run `python collector.py --week 6`.

## Owner names

The collector tries ESPN team `owners` / `owner` fields. Some ESPN API/library versions return an ID or no display name. Check the `owners` array in JSON and the owner column in Markdown. For reliable friendly names, populate `owner_overrides.json` with **team IDs** (not team names, which can change), e.g. `{"17": "Preferred owner name"}`. This file is optional and starts as `{}`. Only add names you're comfortable storing in a private repository. If ESPN exposes opaque IDs, replace them with friendly names via overrides.

## Limitations

- The unofficial `espn_api` library may change or fail when ESPN sessions expire.
- Historical stats are fetched for all weeks 1..target; ESPN corrections may change prior results.
- Combined wins are H2H + top-half scoring bonus, with H2H ties tracked separately. The script stops on ties at the scoring-bonus cutoff.
- Season standings are calculated, not necessarily ESPN's official playoff-seeding order. Playoff odds, league tiebreakers and bye weeks require additional rules.
- Bench points are not proof that a legal lineup swap existed; positional eligibility and lock times aren't evaluated.
- News and subjective power rankings are **not** automatically fetched or generated. ChatGPT researches verified week-specific news when drafting.
- Do not publish raw JSON if it contains personal owner names you don't wish to share.
