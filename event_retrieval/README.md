# tiebe-wikip

This repository contains scripts to collect events from Wikipedia for various countries and years. The main script processes data and generates output files in JSON format.

## How to Run

### Prerequisites
1. Ensure you have Python 3 installed on your system.
2. Install `pip` and `virtualenv` if not already installed.
3. Make sure the following files are present in the repository:
   - `main.py`
   - `run_all.sh`
   - `years.txt` (contains the list of years to process)
   - `countries.txt` (contains the list of countries to process)
   - `requirements.txt` (contains the required Python dependencies)

### Running All Cases with `run_all.sh`

The `run_all.sh` script automates the process of running the `main.py` script for all combinations of countries and years listed in `countries.txt` and `years.txt`. It also generates output files and logs for each execution.

#### Steps:
1. Open a terminal and navigate to the repository directory.
2. Run the following command:
   ```bash
   bash run_all.sh
3. The script will:
    - Create a virtual environment.
    - Install dependencies from `requirements.txt.`
    - Process all combinations of countries and years in parallel (up to 4 processes at a time).
    - Save the output files in the `output_events/<country>/` directory.
    - Save logs for each execution in the `logs/` directory.
    - Generate statistics in `stats/results.json`.
    - Identify possible irregular data executions using `check_all_execs.py`.



### Running Individual Cases with `main.py`
You can also run the `main.py` script for specific country-year combinations manually.

#### Example 1: Running for Brazil in 2016
1. Open a terminal and navigate to the repository directory.
2. Run the following command:
```bash
python3 main.py Brazil 2016
```
3. The output will be saved in the `output_events/Brazil/2016_in_Brazil_events.json` file.
 

#### Example 2: Running for the World in 2024
1. Open a terminal and navigate to the repository directory.
2. Run the following command:
```bash
python3 main.py World 2024
```
3. The output will be saved in the `output_events/World/2024_in_World_events.json` file.


### Output Files
- The output files are stored in the `output_events/<country>/` directory.
- Each file is named in the format `<year>_in_<country>_events.json.`

### Logs
- Logs for each execution are stored in the `logs/` directory
- Each log file is named in the format `<country>_<year>.log.`

### Troubleshooting
- If the script fails, check the logs in the `logs/` directory for details.
- Ensure that `countries.txt` and `years.txt` contain valid entries.
- Verify that the `requirements.txt` file includes all necessary dependencies.