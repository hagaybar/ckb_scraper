import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import yaml
from datetime import datetime
import logging
import sys

# Configure logging
def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a timestamp for the log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"scraper_{timestamp}.log")
    
    # Configure logging format and handlers
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Logging initialized. Log file: {log_file}")

def load_config(config_path):
    try:
        logging.info(f"Loading configuration from {config_path}")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logging.info("Configuration loaded successfully")
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        raise

def fetch_html(url):
    logging.info(f"Fetching HTML content from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"Successfully fetched content (status code: {response.status_code})")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to fetch HTML content: {str(e)}")
        raise

def get_latest_month_url(config):
    try:
        main_url = config['urls']['main_url']
        logging.info(f"Accessing main URL: {main_url}")
        
        response = requests.get(main_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.debug("Successfully parsed main page HTML")
        
        container = soup.select_one(config['urls']['link_selectors']['container'])
        if not container:
            logging.error("Content container not found using selector")
            return None
        
        latest_link = container.select_one(config['urls']['link_selectors']['list'])
        if latest_link and 'href' in latest_link.attrs:
            full_url = latest_link['href']
            logging.info(f"Found latest release notes URL: {full_url}")
            return full_url
        
        logging.error("Could not find latest release notes link")
        return None
        
    except requests.RequestException as e:
        logging.error(f"Error accessing main URL: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while getting latest month URL: {str(e)}")
        return None

def extract_tables(html_content, source_url):
    logging.info("Beginning table extraction")
    soup = BeautifulSoup(html_content, 'html.parser')
    rnsub_divs = soup.find_all('div', class_=lambda x: x and 'rnsub' in x)
    logging.info(f"Found {len(rnsub_divs)} rnsub divisions")

    extracted_tables = []
    for idx, div in enumerate(rnsub_divs, 1):
        logging.debug(f"Processing division {idx}/{len(rnsub_divs)}")
        week_info = div.find('span', class_='AlmaRNTag')
        week_info = week_info.text.strip() if week_info else "Unknown Week"
        logging.debug(f"Week info: {week_info}")

        tables = div.find_all('table')
        logging.debug(f"Found {len(tables)} tables in division {idx}")

        for table_idx, table in enumerate(tables, 1):
            try:
                title_element = table.find_previous('h2')
                table_title = title_element.text.strip() if title_element else "Untitled Table"
                logging.info(f"Processing table: {table_title}")

                headers = [th.text.strip() for th in table.find_all('th')]
                rows = table.find_all('tr')[1:]
                logging.debug(f"Found {len(rows)} rows in table {table_idx}")
                
                table_data = []
                for row_idx, row in enumerate(rows, 1):
                    try:
                        cells = [cell.text.strip() for cell in row.find_all('td')]
                        row_data = {headers[i]: cells[i] for i in range(len(headers))}
                        row_data.update({
                            'week_info': week_info,
                            'source_url': source_url,
                            'table_title': table_title
                        })
                        table_data.append(row_data)
                    except Exception as e:
                        logging.error(f"Error processing row {row_idx} in table '{table_title}': {str(e)}")

                extracted_tables.append({
                    'headers': headers + ['week_info', 'source_url', 'table_title'],
                    'rows': table_data,
                    'table_title': table_title
                })
                logging.info(f"Successfully extracted table: {table_title} with {len(table_data)} rows")
            except Exception as e:
                logging.error(f"Error processing table {table_idx} in division {idx}: {str(e)}")

    logging.info(f"Completed table extraction. Total tables extracted: {len(extracted_tables)}")
    return extracted_tables

def save_tables(extracted_tables, output_dir):
    logging.info(f"Saving tables to directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    saved_count = 0
    for idx, table in enumerate(extracted_tables, 1):
        try:
            df = pd.DataFrame(table['rows'])
            filename = os.path.join(output_dir, f"table_{idx}.csv")
            df.to_csv(filename, index=False)
            logging.info(f"Saved table '{table['table_title']}' to {filename}")
            saved_count += 1
        except Exception as e:
            logging.error(f"Error saving table {idx}: {str(e)}")
    
    logging.info(f"Successfully saved {saved_count} out of {len(extracted_tables)} tables")

def main():
    try:
        setup_logging()
        logging.info("Starting web scraping process")
        
        config = load_config("config.yaml")
        latest_url = get_latest_month_url(config)
        
        if not latest_url:
            logging.error("Could not retrieve the latest month URL. Exiting.")
            return

        logging.info(f"Fetching data from {latest_url}")
        html_content = fetch_html(latest_url)
        tables = extract_tables(html_content, latest_url)
        
        output_dir = r"C:\Users\masedet\Tel-Aviv University\masedet - Documents\Data\CKB"
        save_tables(tables, output_dir)
        
        logging.info("Web scraping process completed successfully")
        
    except Exception as e:
        logging.critical(f"Critical error in main process: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()