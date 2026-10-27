# Phoenix Phamily — ESPN Fantasy Football weekly collector

Private league ID: **1106154**. Season: **2026**.

## Setup
1. Create a **private** GitHub repository, e.g. `phoenix-phamily-recap`.
2. Upload the contents of this starter folder to the root of the repository, including `.github/workflows/weekly.yml`.
3. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Add `ESPN_S2` and `ESPN_SWID` with values obtained locally from your authenticated ESPN browser session. Never share or commit these values.
4. Go to **Actions → Phoenix Phamily weekly stats → Run workflow**. Optionally specify a **completed** week for testing. Otherwise, the script uses ESPN's current week minus one.
5. Download the `phoenix-phamily-weekly-report` artifact from the completed workflow run. Unzip and upload the Markdown or JSON report into ChatGPT.
6. The workflow runs Tuesdays at **9:15 AM America/Phoenix** (Arizona local time).

## Notes
- ESPN's Fantasy API is unofficial. API changes and session expiration can break collection.
- A private repo and GitHub Secrets protect the credentials from being committed, but session cookies are sensitive and may grant account access. Rotate them if exposed.
- The collector deliberately refuses incomplete box scores, missing teams, odd team counts, or a bonus-cutoff scoring tie.
- For weekly bonus wins, the top half by weekly points receives one win. Head-to-head wins are separate. A tie in a head-to-head game is reported but not awarded as a win.
- The weekly scoring ranking is **not** an editorial power ranking. Power rankings and full-season records require separate calculation or additional data.
- Starter highlights use the lineup slot field as provided by `espn_api`; review unusual lineup configurations and ESPN corrections.
- The package dependency is bounded to a major version but not fully pinned; after the first successful test, pin the working version for repeatability.
- Reports are stored as GitHub Actions artifacts, not committed to the repository. Artifacts expire after the configured retention period.
- For local use: install `requirements.txt`, set `ESPN_S2` and `ESPN_SWID` in your shell environment, and run `python collector.py --week 7` (replace with a completed week).
