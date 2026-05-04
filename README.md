# Korean Assembly Bill Briefs

A GitHub Pages site that displays plain-English summaries of recent bills and agenda items passed by South Korea's National Assembly.

Data source: the National Assembly's official English **Plenary Results** page.

## How it works

- `scripts/update_bills.py` scrapes recent official plenary-result notices.
- It extracts headline bullets and key item sections into `data/bills.json`.
- `.github/workflows/update-bills.yml` runs daily and commits refreshed data.
- `index.html` renders the digest as a static page.

No paid LLM key is required; summaries are deterministic and based on official English notices.
