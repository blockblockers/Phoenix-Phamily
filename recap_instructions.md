# Phoenix Phamily — recap editorial contract (v3.1)

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
- `collector.py` does NOT fetch outside NFL news automatically. Without a separately sourced `nfl_context` input, rely only on ESPN fantasy scoring and projections; don't invent real-world game stats.
- A high-scoring benched player is NOT automatically a legal replacement: check lineup slot eligibility, lock times, and available starters before claiming a manager 'cost themselves' the win.
- Never make up quotes, rivalries, playoff odds, real names or events.
- All 6 matchup outcomes, all scoring bonuses, 12 rankings, exact scores and margins must be checked against JSON.
