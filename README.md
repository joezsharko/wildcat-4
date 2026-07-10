# McGrath City Mazda — New Inventory Price Tracker

Tracks new-vehicle prices from mcgrathcitymazda.com over time and hosts a
live dashboard for free using GitHub Actions (scraping on a schedule) +
GitHub Pages (serving the dashboard). No server to manage or pay for.

## How it works

- A GitHub Actions workflow runs every 6 hours, scrapes the current
  inventory, and appends a new snapshot to `data/prices.db`.
- It regenerates `docs/index.html` (a self-contained dashboard with the
  price history embedded) and commits both back to the repo.
- GitHub Pages serves `docs/index.html` as your live site.

## One-time setup

1. **Create a new GitHub repo** (public repos get free Pages hosting;
   private repos need a paid plan for Pages, so public is simplest here).

2. **Push this folder to it:**
   ```bash
   cd mazda_scraper
   git init
   git add .
   git commit -m "Initial price tracker"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

3. **Enable write permissions for Actions** (needed so the workflow can
   commit updated data back):
   - Go to your repo → **Settings → Actions → General**
   - Under "Workflow permissions", select **Read and write permissions**
   - Save

4. **Enable GitHub Pages:**
   - Go to **Settings → Pages**
   - Under "Build and deployment" → Source: **Deploy from a branch**
   - Branch: **main**, folder: **/docs**
   - Save. GitHub will give you a URL like
     `https://<your-username>.github.io/<repo-name>/`

5. **Trigger the first run manually** (don't wait 6 hours):
   - Go to the **Actions** tab → "Scrape prices and update dashboard" →
     **Run workflow**
   - Watch it run; it should finish in under a minute for one dealership.

6. Visit your Pages URL. It may take a minute or two after the first
   successful run for Pages to publish.

After that, it just runs itself every 6 hours, building up price history
automatically. Check the **Actions** tab any time to see run history and
logs.

## Changing the schedule

Edit `.github/workflows/scrape.yml`:
```yaml
schedule:
  - cron: "0 */6 * * *"   # every 6 hours
```
Dealership prices rarely change more than once or twice a day, so this is
already generous. crontab.guru is handy for building other schedules.

## Files

- `fetcher.py` — downloads the inventory pages (polite delay between pages)
- `parser.py` — extracts vehicle data from page text (year, model, VIN,
  stock #, colors, MSRP, "Your Price")
- `storage.py` — saves each scrape as rows in `data/prices.db` (SQLite)
- `run_scrape.py` — the full pipeline: fetch → parse → store → rebuild dashboard
- `generate_dashboard.py` — builds `docs/index.html` with embedded data + charts
- `.github/workflows/scrape.yml` — the schedule + automation

## Local testing (optional)

You can still run it locally before pushing, same as before:
```bash
pip install -r requirements.txt
python3 run_scrape.py
open docs/index.html
```

## Being a good citizen about scraping

- The fetcher waits 2 seconds between page requests and only pulls public
  inventory pages — nothing behind a login.
- Checking every few hours keeps load on their server negligible.
- Worth doing manually at some point: check
  mcgrathcitymazda.com/robots.txt yourself and skim their Terms of
  Service to confirm nothing here conflicts with their preferences. This
  is a small personal project, but worth knowing where things stand.

## When the site changes

Dealer sites get redesigned occasionally, which can break the parser.
Symptoms: the Actions run succeeds but logs "No vehicles parsed," or the
dashboard stops updating with new vehicles. Check the run logs in the
Actions tab first — if fetch is failing outright (e.g. a 403), the site
may have started blocking the request pattern; if fetch succeeds but
parsing finds nothing, the HTML structure likely changed and the parser
needs re-tuning against the new page.

## Roadmap ideas

- Add more dealerships (each just needs its own fetcher + parser; reuse
  storage/dashboard code, and add rows to the same price_snapshots
  table with a dealership column to distinguish them)
- Track used inventory too (/inventory/used)
- Add day-over-day / week-over-week % change columns
- Email/text alert when a specific VIN's price drops (GitHub Actions can
  send emails too, or ping a webhook)
