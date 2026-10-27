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

## Version 3 — legacy rivalry archive (2013–2025)

V3 adds `legacy.py`, `build_legacy.py`, `.github/workflows/legacy.yml` and `legacy/identities.json` and modifies `collector.py` and `recap_instructions.md`. Keep your existing `owner_overrides.json` unchanged when upgrading. `weekly.yml` and secrets remain unchanged.

1. Upload new/modified files to the repository, preserving folder paths. **Do not overwrite your populated `owner_overrides.json`.**
2. GitHub Actions → **Phoenix Phamily historical archive (manual)** → Run workflow. This may take a while and older ESPN years may fail; errors are recorded rather than fabricated.
3. Download the `phoenix-phamily-legacy-archive` artifact and **commit `archive.json` to `legacy/archive.json` in the repository**. The weekly workflow cannot read an artifact from a different workflow automatically.
4. Inspect `legacy/archive.json` seasons/errors. The collector never claims complete league history when historical endpoints omit weeks.
5. Populate `legacy/identities.json` by checking ESPN historical owners/teams. Example:

```json
{
  "franchises": {
    "owner-a": {"label": "Preferred franchise name", "owner": "Preferred owner name"}
  },
  "seasons": {
    "2026": {"17": "owner-a"},
    "2025": {"4": "owner-a"}
  }
}
```

Each mapping is a **season-specific ESPN team ID** to your stable franchise identifier. Reused team IDs in another season are NOT assumed to identify the same owner. The `franchises` metadata is for human reference; mappings under `seasons` drive comparisons. For a renamed team with the same owner, use the same franchise ID; for a new owner, create a different franchise ID. You can map multiple years gradually. If ownership continuity is uncertain, leave it unmapped. Current owner overrides are display names only, not proof of historical ownership.
6. Re-run **Phoenix Phamily weekly stats** using **Run workflow**, not Re-run jobs, after committing archive and identity mappings. The weekly JSON now contains `legacy_rivalries` and `legacy_warning`, and Markdown has a short legacy section. If none of the six current matchups have two mapped historical franchises, the section may be empty.

Archive is intentionally separate from weekly stats and does not auto-refresh. It collects **regular-season** games where the ESPN API returns box scores, with top three active starters when available. It does not yet claim playoff or championship records. 2013–2018 player detail may be unavailable. Some old seasons may have different scoring rules. The archive may contain owner-sensitive information; keep your repository private.

## Version 3.1 — automatic identity inference

The historical archive workflow now generates `legacy/identities.json` and `legacy/identity_review.json` automatically alongside `legacy/archive.json`. Download and commit **both** `archive.json` and `identities.json` into `legacy/` before running the weekly collector. `identity_review.json` is optional and shows unmapped seasons, co-owned teams, and conflicting mappings.

Identity inference uses exact ESPN owner identifiers where available and otherwise exact ESPN account handles. It does **not** link teams by name or team ID alone. Account handles are useful evidence but are not guaranteed immutable; manually check any doubtful matches. Multi-owner entries are intentionally left unresolved. The inference preserves existing manual identity mappings if you run it against a populated `legacy/identities.json`. If older ESPN seasons lack owner data, they remain unmapped and won't produce fabricated rivalries.

The archive workflow also fetches a 2026 owner snapshot so historic identities can be linked to current teams. If you previously ran the archive workflow, **Run workflow** again after uploading the updated `legacy.py`, `build_legacy.py`, `infer_identities.py`, and `.github/workflows/legacy.yml`. The GitHub artifact is not committed automatically.
