# Web Scraper for Release Notes Extraction

This repository contains a Python-based web scraper designed to extract tabular data from release notes on a given website. The data is saved as CSV files for further analysis or integration into other workflows.

## Features

- **Configuration Management**: Uses a YAML configuration file to define URLs and HTML selectors.
- **Logging**: Comprehensive logging of all steps, including errors, with logs saved to a `logs` directory.
- **Dynamic URL Detection**: Automatically fetches the latest month's release notes based on the main page structure.
- **Table Extraction**: Extracts tabular data from HTML content, including additional metadata such as week info and source URL.
- **CSV Export**: Saves extracted tables as CSV files in a specified output directory.

## Requirements

- Python 3.7 or higher
- The following Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `pyyaml`


## Usage
Prepare the Configuration File: Create a config.yaml file with the following structure:

yaml
Copy
Edit
urls:
  main_url: "https://example.com/main-page"
  link_selectors:
    container: "div.container-class"
    list: "a.link-class"
Replace the placeholder values with the actual structure of the target website.

## Run the Script: Execute the script with:

python scraper.py
## The script will:

Load configuration from config.yaml.
Fetch the latest release notes URL from the main page.
Extract tables from the release notes page.
Save the tables as CSV files in the specified output directory.
Output: CSV files will be saved to the directory defined in the output_dir variable in the script. Logs will be saved to the logs directory.

# Directory Structure
```
.
├── scraper.py        # Main script
├── config.yaml       # Configuration file
├── logs/            # Logs directory
├── output/          # Output directory for CSV files
└── requirements.txt  # Python dependencies
```


## Logging
Logs provide detailed information about the scraping process, including:

Initialization
Configuration loading
HTML fetching
Table extraction and saving
Errors and warnings
Error Handling
The script is designed to handle and log errors gracefully. Key error-handling mechanisms include:

Logging missing configuration or invalid URLs.
Catching and logging exceptions during table extraction or file saving.

## Example Output

The script generates CSV files with the following structure:

| Header 1  | Header 2  | Week Info    | Source URL                | Table Title         |
|-----------|-----------|--------------|---------------------------|---------------------|
| Value 1   | Value 2   | Week X, 2024 | https://example.com/page  | Example Table Name  |

Each row corresponds to a record extracted from the tables on the release notes page, enriched with metadata like `Week Info` and `Source URL`.


## Customization

To adapt the scraper for a different website:

Update config.yaml with the correct URL and HTML selectors.
Modify the extract_tables function to handle specific HTML structures if necessary.

## License
This project is licensed under the MIT License.
