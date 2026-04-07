#!/usr/bin/env python3
"""DuckDuckGo job board scanner for fractional CFO leads."""
import json, re, time, subprocess, urllib.parse, sys
from datetime import datetime

QUERIES = [
    'site:linkedin.com/jobs "fractional CFO"',
    'site:linkedin.com/jobs "part-time CFO"',
    'site:linkedin.com/jobs "fractional finance director"',
    'site:linkedin.com/jobs "interim CFO"',
    'site:linkedin.com/jobs "fractional VP Finance"',
    'site:wellfound.com/jobs "fractional CFO"',
    'site:wellfound.com/jobs "part-time CFO"',
    'site:weworkremotely.com CFO finance',
    'site:remotive.com "fractional CFO" finance',
    'site:remotive.com "interim CFO" finance',
    'site:himalayas.app "fractional CFO"',
    'site:boards.greenhouse.io "fractional CFO"',
    'site:jobs.ashbyhq.com "fractional CFO"',
    'site:jobs.lever.co "fractional CFO"',
    'site:apply.workable.com "fractional CFO"',
    'site:apply.workable.com "part-time CFO"',
    'site:welcometothejungle.com "fractional CFO"',
    'site:welcometothejungle.com "directeur financier" "temps partiel"',
    'site:totaljobs.com "fractional CFO"',
    'site:reed.co.uk "fractional CFO" OR "part-time finance director"',
    'site:indeed.com "fractional CFO" remote',
    'site:fractionaljobs.io CFO',
    'site:glassdoor.com "fractional CFO" remote',
    'site:simplyhired.com "fractional CFO" remote',
    '"fractional CFO" "marketing agency" OR "digital agency" job',
    '"fractional CFO" "recruitment agency" OR "staffing agency" job',
    '"fractional CFO" "consulting firm" OR "professional services" job',
    '"fractional CFO" South Africa job',
    '"fractional CFO" Canada job',
    '"part-time finance director" agency OR services job',
    '"outsourced CFO" small business hiring',
]

def search_ddg(query):
    """Search DuckDuckGo HTML and return list of (title, url) tuples."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "15", url,
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"],
            capture_output=True, text=True, timeout=20
        )
        html = result.stdout
    except Exception as e:
        print(f"  Error fetching: {e}", file=sys.stderr)
        return []

    results = []
    # Extract result links from DuckDuckGo HTML
    # Pattern: <a rel="nofollow" class="result__a" href="...">TITLE</a>
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
        raw_url = match.group(1)
        title = re.sub(r'<[^>]+>', '', match.group(2)).strip()

        # DuckDuckGo wraps URLs in a redirect; extract the actual URL
        actual = re.search(r'uddg=([^&]+)', raw_url)
        if actual:
            raw_url = urllib.parse.unquote(actual.group(1))

        if raw_url and title:
            results.append({"title": title, "url": raw_url})

    return results

def extract_id(url, title):
    """Generate a dedup key from URL or title."""
    # LinkedIn job IDs
    m = re.search(r'linkedin\.com/jobs/view/[^/]*?(\d{8,})', url)
    if m:
        return f"linkedin-{m.group(1)}"
    # Wellfound
    m = re.search(r'wellfound\.com/jobs/(\d+)', url)
    if m:
        return f"wellfound-{m.group(1)}"
    # Remotive
    m = re.search(r'remotive\.com.*?(\d{5,})', url)
    if m:
        return f"remotive-{m.group(1)}"
    # Workable
    m = re.search(r'workable\.com/[^/]+/j/([A-Z0-9]+)', url)
    if m:
        return f"workable-{m.group(1)}"
    # Generic: hash of URL
    return f"url-{hash(url) % 10**10}"

def main():
    # Load seen listings
    seen_file = "seen_listings.json"
    try:
        with open(seen_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"last_scan": "", "seen": []}

    seen_ids = {item["id"] for item in data["seen"]}
    seen_keys = {(item.get("company",""), item.get("title",""), item.get("portal",""))
                 for item in data["seen"]}

    all_new = []
    today = datetime.now().strftime("%Y-%m-%d")

    for i, query in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] {query[:60]}...")
        results = search_ddg(query)
        print(f"  Found {len(results)} results")

        for r in results:
            rid = extract_id(r["url"], r["title"])
            if rid in seen_ids:
                continue

            # Determine portal from URL
            portal = "Unknown"
            for p in ["linkedin", "wellfound", "remotive", "himalayas",
                       "greenhouse", "ashbyhq", "lever", "workable",
                       "welcometothejungle", "totaljobs", "reed.co.uk",
                       "indeed", "fractionaljobs", "glassdoor", "simplyhired",
                       "weworkremotely"]:
                if p in r["url"]:
                    portal = p
                    break

            entry = {
                "id": rid,
                "title": r["title"],
                "url": r["url"],
                "portal": portal,
                "first_seen": today,
                "query": query[:50]
            }

            all_new.append(entry)
            seen_ids.add(rid)
            data["seen"].append({"id": rid, "company": "", "title": r["title"],
                                  "portal": portal, "first_seen": today})

        if i < len(QUERIES) - 1:
            time.sleep(2)

    # Save updated seen listings
    data["last_scan"] = today
    with open(seen_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Output new results as JSON for the agent to process
    output = {"date": today, "new_count": len(all_new), "results": all_new}
    with open("search_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(all_new)} new results found.")
    print(f"Results saved to search_results.json")
    print(f"Updated seen_listings.json ({len(data['seen'])} total)")

if __name__ == "__main__":
    main()
