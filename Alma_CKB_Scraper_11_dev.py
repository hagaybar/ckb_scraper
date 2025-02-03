import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import yaml
from datetime import datetime
import logging
import sys

def setup_logging():
    """Sets up logging to both a file and console output."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"scraper_{timestamp}.log")
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
    """Loads YAML configuration file."""
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
    """Fetches the HTML content of a given URL."""
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
    """Finds and returns the latest month's URL from the main page."""
    try:
        main_url = config['urls']['main_url']
        logging.info(f"Accessing main URL: {main_url}")
        response = requests.get(main_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.debug("Successfully parsed main page HTML")
        
        # Locate container holding the latest link
        container = soup.select_one(config['urls']['link_selectors']['container'])
        if not container:
            logging.error("Content container not found using selector")
            return None
        
        # Find the latest link inside the container
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

def extract_tables(html_content, source_url):
    """Extracts tables from HTML content and returns them in structured format."""
    logging.info("Beginning table extraction")
    soup = BeautifulSoup(html_content, 'html.parser')
    rnsub_divs = soup.find_all('div', class_=lambda x: x and 'rnsub' in x)
    logging.info(f"Found {len(rnsub_divs)} rnsub divisions")
    extracted_tables = []
    
    for idx, div in enumerate(rnsub_divs, 1):
        logging.debug(f"Processing division {idx}/{len(rnsub_divs)}")
        week_info = div.find('span', class_='AlmaRNTag')
        week_info = week_info.text.strip() if week_info else "Unknown Week"
        tables = div.find_all('table')
        
        for table_idx, table in enumerate(tables, 1):
            try:
                # Locate table title
                title_element = table.find_previous('h2')
                table_title = title_element.text.strip() if title_element else "Untitled Table"
                
                # Extract headers
                headers = [th.text.strip() for th in table.find_all('th')]
                rows = table.find_all('tr')[1:]  # Skip header row
                table_data = []
                
                for row in rows:
                    cells = [cell.text.strip() for cell in row.find_all('td')]
                    row_data = {headers[i]: cells[i] for i in range(len(headers))}
                    row_data.update({'week_info': week_info, 'source_url': source_url, 'table_title': table_title})
                    table_data.append(row_data)
                
                extracted_tables.append({'headers': headers + ['week_info', 'source_url', 'table_title'], 'rows': table_data, 'table_title': table_title})
            except Exception as e:
                logging.error(f"Error processing table {table_idx}: {str(e)}")
    
    logging.info(f"Completed table extraction. Total tables extracted: {len(extracted_tables)}")
    return extracted_tables

def manage_output_folders(base_dir):
    """Manages output directories, rotating 'current' data to 'last time'."""
    current_dir = os.path.join(base_dir, "current")
    last_time_dir = os.path.join(base_dir, "last time")
    os.makedirs(current_dir, exist_ok=True)
    os.makedirs(last_time_dir, exist_ok=True)

    if os.listdir(current_dir):
        logging.info("Moving current files to last time directory")
        for file_name in os.listdir(current_dir):
            source_path = os.path.join(current_dir, file_name)
            destination_path = os.path.join(last_time_dir, file_name)

            # Check if the file already exists in 'last_time' and delete it
            if os.path.exists(destination_path):
                os.remove(destination_path)

        # Move (rename) the file
        os.rename(source_path, destination_path)    

def save_tables(extracted_tables, output_dir):
    """Saves extracted tables as CSV files."""
    logging.info(f"Saving tables to directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    for idx, table in enumerate(extracted_tables, 1):
        try:
            df = pd.DataFrame(table['rows'])
            filename = os.path.join(output_dir, f"table_{idx}.csv")
            df.to_csv(filename, index=False)
            logging.info(f"Saved table '{table['table_title']}' to {filename}")
        except Exception as e:
            logging.error(f"Error saving table {idx}: {str(e)}")

def main():
    """Main execution function handling all operations."""
    try:
        setup_logging()
        config = load_config("config.yaml")
        latest_url = get_latest_month_url(config)
        if not latest_url:
            logging.error("Could not retrieve the latest month URL. Exiting.")
            return
        
        html_content = fetch_html(latest_url)
        tables = extract_tables(html_content, latest_url)
        base_output_dir = r"C:\Users\masedet\Tel-Aviv University\masedet - Documents\Data\CKB"
        manage_output_folders(base_output_dir)
        save_tables(tables, os.path.join(base_output_dir, "current"))
        logging.info("Web scraping process completed successfully")
    except Exception as e:
        logging.critical(f"Critical error in main process: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
