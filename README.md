# Multi-League ESPN Fantasy Recap Engine v4

One GitHub repository, one weekly workflow, independent reports, histories, and personalities per league. This generates **research briefs and sourced NFL game-log context**, not automatically written prose. Paste each league's outputs and league.json into ChatGPT to write the 1,150–1,250 word recap.

## Install
1. Download the ZIP. Back up your existing repository and replace the root scripts and `.github/workflows` with this package. **Do not leave the old single-league workflows enabled**, or both will run.
2. Your existing Phoenix Phamily settings and 2013–2025 historical archive are under `leagues/phoenix-phamily/`. When you rerun archive, download its artifacts and replace only the corresponding `legacy/` files.
3. Keep GitHub repository Secrets `ESPN_S2` and `ESPN_SWID`. These are never committed. The same authenticated ESPN account must have access to each private league.
4. In GitHub Actions, run **All leagues weekly recap** manually, league `all`, week blank or a completed week. Tuesday UTC schedule is `09:15 UTC` (02:15 Phoenix during MST).
5. Download `all-leagues-weekly-reports` artifact. Inside it, reports are separated by league slug.

## Add another league
1. Copy `leagues/_new-league-template` to `leagues/my-other-league`.
2. Edit `league.json`: unique `slug` matching folder name, ESPN ID, season, league name, `scoring.top_half_bonus_win`, tone, and team personality jokes. Set `enabled` to `true`.
3. Run the weekly workflow. Historical archive is optional; to create it run **Selected league historical archive** with league slug.
4. Save downloaded historical files under `leagues/my-other-league/legacy/` and commit.

## Scoring
- Phoenix Phamily: 1 H2H win plus top-half weekly points bonus; 12 teams, six bonus winners.
- Other leagues: set `top_half_bonus_win` to `false` unless the league actually uses it. ESPN tie and special league rules may need adaptation.
- Weekly standings are reconstructed from completed box scores and may differ from ESPN for manual adjustments, playoffs, or special rules.

## Privacy and caveats
- Never commit cookies. ESPN owners are included only if verified; no handles in published recaps.
- `legacy` data is isolated per league; no mixing of rivalries across leagues.
- Game-log enrichment is best effort and is not verified injury reporting.
- Old 2013–2018 archive seasons have incomplete box-score coverage.
- This release uses one ESPN credential pair for all leagues. Multiple ESPN accounts require additional secret-selection work.
- Running all leagues currently processes them sequentially.

## Local validation
`python -m unittest discover -p 'test_*.py'`
`python run_leagues.py --help`
