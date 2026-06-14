# fCFO Lead Scanner

Automated daily monitoring of job boards for fractional CFO opportunities.

State file `seen_listings.json` tracks previously surfaced listings to avoid duplicates.
Managed by a scheduled Claude Code remote agent.

## Known issue: search.py requires DuckDuckGo network access

`search.py` shells out to `curl https://html.duckduckgo.com/...`. In remote
execution environments with a restricted network policy, this host returns
"Host not in allowlist" (curl gets a 403), so every query silently returns 0
results - the scan looks like it ran successfully but found nothing.

**Fix:** add `html.duckduckgo.com` (and ideally the job-board domains in
`QUERIES`) to the environment's network allowlist.

**Workaround used by the agent on 2026-06-10:** when search.py returns 0
results across all 31 queries, verify with `curl -s -o /dev/null -w '%{http_code}'
https://html.duckduckgo.com` (403 = blocked). If blocked, fall back to the
built-in WebSearch tool to run the same `QUERIES` list, then manually dedupe
against `seen_listings.json` and triage as usual. This caught up on a ~26-day
gap (last real new listing was 2026-05-14) - 41 new postings were found and
triaged in the 2026-06-10 scan.

**2026-06-11:** Same DDG 403 block. Direct `curl`/WebFetch to job-board URLs
(Upwork, Glassdoor, Reed, AshbyHQ, etc.) is also 403'd in this environment -
only the WebSearch tool works for research, so PIPELINE/FLAGGED research in
Step 3 must go through WebSearch too. WebSearch fallback found 22 new IDs;
21 were cross-posts of already-triaged listings, competitor fractional-CFO
firms recruiting their own bench, staffing agencies for unnamed clients, or
expired/old postings (all logged as SKIPPED). 1 new PIPELINE lead (Upwork
digital marketing agency).

**2026-06-14:** Same DDG 403 block (curl to html.duckduckgo.com -> 403).
WebSearch fallback (split across two parallel sub-agents covering all 31
queries) found 6 new IDs. 0 PIPELINE: 5 SKIPPED (Huzzle cross-post of an
already-triaged Workable listing, OneTwenty Fi and Ascent CFO Solutions
both recruiting their own fractional-CFO bench, E78 Talent staffing for an
unnamed PE-backed manufacturing client, Myriad Genetics large regulated
public company - none fit the target profile). 1 FLAGGED: "Fractional CFO
- Fundraising & Growth (Equity Only)" at Client Link LLC (LinkedIn) -
generic/placeholder-style company name and equity-only comp made fit
uncertain.
