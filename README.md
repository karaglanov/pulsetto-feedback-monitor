# Pulsetto Feedback Monitor

Simple MVP pipeline that collects public Reddit mentions of **"Pulsetto"**, classifies issue patterns, and generates a weekly summary JSON.

## What it does

- Fetches Reddit search results for keyword `Pulsetto`
- Normalizes fields into a consistent schema and stores rows in CSV
- Avoids duplicates using `url` as unique key
- Classifies each mention with deterministic keyword rules (no paid APIs):
  - `sentiment`: `positive`, `mixed`, `negative`
  - `issue_category`: `support_silence`, `poor_support_quality`, `no_results`, `weak_results`, `onboarding_confusion`, `app_connectivity`, `comfort_fit`, `price_value_mismatch`, `trust_skepticism`, `scientific_credibility`, `delivery_logistics`, `competitor_comparison`, `pre_purchase_question`, `usage_question`, `general_awareness`, `experience_sharing`, `recommendation_seeking`, `positive_advocacy`, `other`
  - `severity`: `low`, `medium`, `high`
  - `attribute_affected`: mapped business area (`support`, `product`, `technical`, `delivery`, `trust`, etc.)
- Generates `data/weekly_summary.json` with:
  - `total_mentions`
  - `negative_mentions`
  - `issue_category_counts`
  - `attribute_counts`
  - `source_breakdown`
  - `stage_breakdown` (`discovery`, `purchase`, `setup`, `first_use`, `support_aftercare`)
  - `trust_risk_score`
  - `support_gap_count`
  - `top_positive_signals`
  - `top_negative_signals`
  - `top_critical_mentions`
  - `recommended_actions`

Saved mention columns in `data/mentions.csv`:

- `title`
- `body_text`
- `subreddit`
- `author`
- `created_date` (UTC ISO format)
- `url`
- `source` (`reddit`)

## Local setup

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) set a custom Reddit user agent:

   ```bash
   export REDDIT_USER_AGENT="PulsettoFeedbackMonitor/0.1"
   ```

## Run

```bash
python scripts/run_pipeline.py
```

One command runs:

1. collection (`fetch_reddit_mentions`)
2. classification (`classify_mentions`)
3. summary generation (`build_weekly_summary`)

Output files:

- `data/mentions.csv`
- `data/weekly_summary.json`

## Public demo via GitHub Pages (QR-ready)

This repo is already static and can be hosted directly with **GitHub Pages**.

### Enable GitHub Pages

1. Push this repository to GitHub.
2. Open **Settings → Pages**.
3. Under **Build and deployment**, set:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main` (or your default branch)
   - **Folder:** `/ (root)`
4. Save, then wait for the Pages deployment to finish.

### Open the public URL

After deployment, open:

- `https://<your-github-username>.github.io/pulsetto-feedback-monitor/`

The root URL automatically redirects to `web/`, where the dashboard lives, and the dashboard fetches `data/weekly_summary.json` with a GitHub Pages-safe path.

## GitHub Actions daily auto-renew

A GitHub Actions workflow is included at `.github/workflows/weekly_report.yml`.

It runs the pipeline:

- on a daily schedule (every day at 09:00 UTC)
- on manual trigger (`workflow_dispatch`)

During each run, GitHub Actions executes `python scripts/run_pipeline.py`, stages changes in `data/`, and pushes a bot commit (`chore: refresh Pulsetto data`) only when generated files changed. The pipeline first repairs or creates the mentions CSV header, keeps previously saved mentions, and only appends new unique Reddit URLs, which keeps the GitHub Pages dashboard up to date automatically without changing the Pages setup.

### Run manually from GitHub

1. Open your repository on GitHub.
2. Go to **Actions**.
3. Select **Daily Pulsetto Pipeline**.
4. Click **Run workflow**.
5. Choose the branch and click **Run workflow**.

After the run completes, download `daily-pipeline-output` from the workflow run page to get:

- `data/mentions.csv`
- `data/weekly_summary.json`
