# LinkedIn Post Finder

Daily GitHub Actions pipeline that finds public LinkedIn hiring posts matching your roles and experience range.

It queries Google Programmable Search restricted to `linkedin.com/posts` (no LinkedIn login or scraping, which LinkedIn's ToS forbids).

## Setup
1. Create a Programmable Search Engine at https://programmablesearchengine.google.com with the site `linkedin.com/posts/*`; copy its **Search engine ID**.
2. Enable the *Custom Search API* in Google Cloud and create an API key (free: 100 queries/day).
3. Repo → Settings → Secrets → Actions: add `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`.
4. Edit `config.yaml` (roles, years of experience, location).
5. Actions → *LinkedIn Post Finder* → Run workflow. New matches go to `results.md` and an issue is opened.

Pipeline: **test** (pytest on every push/PR) → **find** (daily cron / manual; commits `results.md`, opens an issue).

Limitation: matching uses search-result titles/snippets, and Google only indexes some posts, so coverage is partial.
