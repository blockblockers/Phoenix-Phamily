# Multi-league recap v4.2 — archives and team personalities

1. Back up your GitHub repository. Upload all files in this ZIP to the **repository root**, preserving paths. Do not put the whole ZIP in a subfolder.
2. Confirm `leagues/work-league/league.json` and `leagues/friends-league/league.json` contain the intended IDs and `enabled: true`.
3. Verify `leagues/work-league/legacy/archive.json` and `leagues/friends-league/legacy/archive.json` are committed; previously weekly reports said “Legacy archive not installed.”
4. Run GitHub Actions > All leagues weekly recap with league `all`, week `7` for a validation run.
5. Download reports and check that both new league reports have `legacy_warning` cleared and `legacy_rivalries` populated where supported. Historical matchups may be unavailable for pre-2019 ESPN seasons.

This ZIP uses the v4.1 code and adds configuration and archives; it does not add an automatic AI prose writer. Work league has 14 teams, friends league has 12, and both have top-half bonuses disabled.

Security: The archive contains owner identifiers and league history. Keep the GitHub repository private if you do not want this information publicly accessible.
