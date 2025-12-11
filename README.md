# Eastern Africa Data Job Scraper

A Python-based scraper to find data-related jobs in Eastern Africa from multiple sources.

## Data Sources
- **BrighterMonday** (Kenya, Tanzania, Uganda)
- **MyJobMag** (Kenya, Uganda, etc.)
- **LinkedIn** (Global/Regional)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Copy the example environment file and add your credentials (optional, mainly for LinkedIn):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your `LINKEDIN_LI_AT` cookie if you want authenticated LinkedIn results.

## Usage

Run the scraper with default settings (scrapes all configured locations and titles):
```bash
python main.py
```

### Filters and Options

- **Limit Search (Testing)**: Run a quick test by limiting the number of searches per scraper.
  ```bash
  python main.py --limit 1
  ```

- **Filter by Location**:
  ```bash
  python main.py --location "Kenya"
  ```

- **Filter by Job Title**:
  ```bash
  python main.py --title "Data Analyst"
  ```

## Output
Results are saved to `eastern_africa_data_jobs.csv` with a summary header and deduped entries.
