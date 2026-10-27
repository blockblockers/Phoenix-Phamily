# Multi-league fantasy — recap editorial contract (v3.1)

**Length:** 1,150–1,250 words total for the published recap, including headings, awards, rankings and closing. Aim 1,200. Count before delivery; cut repetition rather than sections.

## Required structure and budget
- Opening (~80 words): memorable week-specific hook, two-win scoring reminder only when useful.
- Six matchups (~600 words total, ~100 each): both team names, exact scores and winner, two or three meaningful fantasy performances, a genuinely relevant bench decision when supported, team-name-specific humor.
- Historical callbacks (0–2, ~60 words total): only verified archive matches; cite season/week, historical names and actual score. Archive begins with usable box scores in 2019; do not imply all-time completeness.
- Weekly awards (~110 words): hero, disaster, bad beat, bench regret; no unsupported assertions.
- Standings and bonus-wins explanation (~110 words): combined H2H + top-half scoring bonus, don't mistake scoring bonus for H2H victory. Compact table allowed.
- Editorial power rankings (~190 words): all 12 teams, copyable plain text, independent of weekly scoring ranks.
- Closing (~70 words): distinct final roast and meaningful look ahead without invented next-week schedule.

## Identities
- Always use **current team names** in headings, standings, power rankings, and as the primary referent in prose.
- Use real owner first names occasionally only if the collector labels them as manually overridden or ESPN verified. If unavailable, use the team name; do not guess.
- Never expose ESPN usernames, email addresses, login handles, member IDs, opaque franchise IDs or owner identity keys in published prose.
- Historical callbacks must use current names plus historical season-specific team names.

## NFL research and factual discipline
- Match the exact NFL scoring week and 2026 season; verify NFL game logs and news with dated sources (NFL.com/ESPN/team reports). Cite linked sources for real-life yardage, touchdowns, injuries, snaps, usage, or trades. Do not reuse later-week news as if it happened during the fantasy week.
- `nfl_enrichment.py` automatically retrieves ESPN NFL final-game box-score rows for the **same season and week** as the fantasy report and saves `reports/week-NN-nfl-context.json` and `.md`. Use the sourced game logs only when a row and URL are present. This is NOT a verified injury/news feed: do not invent injury, trade, snap-count or usage explanations. If enrichment fails, rely only on fantasy scoring and projections.
- A high-scoring benched player is NOT automatically a legal replacement: check lineup slot eligibility, lock times, and available starters before claiming a manager 'cost themselves' the win.
- Never make up quotes, rivalries, playoff odds, real names or events.
- All 6 matchup outcomes, all scoring bonuses, 12 rankings, exact scores and margins must be checked against JSON.

## Source-backed storytelling
- Use one or two relevant sourced NFL box-score details per matchup when available, with links to the source; never force every game log into the story.
- Keep the published article at 1,150–1,250 words **including** headings, tables, rankings and awards; measure word count before publishing.
- Do not copy ESPN usernames from legacy files or archived names into owner labels.

## League personality
Use `league.json` for the current league's `tone`, `team_personalities`, `running_jokes`, and scoring rules. Team-name-specific trash talk belongs in **every matchup, opening, awards, standings commentary, rankings, and closing**. Keep jokes varied and grounded in real results. For The Boomers, "Boomers" means the older generation; retirement, flip phones, and early-bird specials are appropriate jokes. Do not recycle the exact same punchline repeatedly. If `top_half_bonus_win` is false, do not mention or award a bonus.
