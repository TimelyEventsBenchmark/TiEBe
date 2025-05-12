# Reference Retrieval

This module contains every script needed to collect, clean, and inspect reference news articles for each event in the TiEBe timeline.

## Installing requirements
Set up the runtime in three commands.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt         
playwright install  
```

## Fetching references

### Single country-year
Use this command if you only need the news for a single country.

```bash
python scrape.py <country> <year>
```

| argument  | meaning                                                                            |
| --------- | ---------------------------------------------------------------------------------- |
| `country` | Folder that already contains `YEAR_in_COUNTRY_events.json` (the Wikipedia export). |
| `year`    | Four-digit year to process.                                                        |

The script writes:
```bash
<country>/extracted_events_<year>_<country>.json
```
Each event now has a links list whose items include:

| key              | description                                                 |
| ---------------- | ----------------------------------------------------------- |
| `link`           | URL that was visited                                        |
| `title`          | `<title>` tag of the page                                   |
| `extracted_text` | Cleaned article body (may be empty if quality rules or scrape failed) |
| `text` / `dates` | Metadata copied from the timeline dump                      |

### Batch mode
Scrape everything in one go.

```bash
bash run_all.sh
```
Open the script and adjust the countries=(...) and years=(...) arrays to suit your needs.

## Post-processing utilities

### Remove duplicate links
Keeps the live or archived link with the largest body of text for each event.

```bash
python helpers/remove_duplicate.py
```
Edit the hard-coded country and years variables at the bottom if necessary.

### Quick coverage counts
Gauge how much text you have (or how many events exist) per month.

``` bash
python helpers/count_news.py            # counts non-empty links
python helpers/count.py                 # counts raw timeline events
```
Each script prints one dictionary per year, keyed by the (Portuguese) month name.

