from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import csv
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
import os
import logging
from dataclasses import dataclass, field, fields, asdict

#create a custom options instance
options = webdriver.ChromeOptions()
#add headless mode to our options
options.add_argument("--headless")

API_KEY = "YOUR-SUPER-SECRET-API-KEY"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchData:
    name: str
    link: str
    result_number: int
    page_number: int

    def __post_init__(self):
        self.check_string_fields()
    
    def check_string_fields(self):
        for field in fields(self):
            if isinstance(getattr(self, field.name), str):
                if getattr(self, field.name) == '':
                    setattr(self, field.name, f"No {field.name}")
                    continue
                value = getattr(self, field.name)
                setattr(self, field.name, value.strip())

class DataPipeline:
    def __init__(self, csv_filename="", storage_queue_limit=50):
        self.names_seen = []
        self.storage_queue = []
        self.storage_queue_limit = storage_queue_limit
        self.csv_filename = csv_filename
        self.csv_file_open = False

    def save_to_csv(self):
        self.csv_file_open = True
        self.data_to_save = []
        self.data_to_save.extend(self.storage_queue)
        self.storage_queue.clear()
        if not self.data_to_save:
            return
        keys = [field.name for field in fields(self.data_to_save[0])]

        file_exists = os.path.isfile(self.csv_filename) and os.path.getsize(self.csv_filename) > 0
        with open(self.csv_filename, mode="a", newline="", encoding="UTF-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=keys)
            if not file_exists:
                writer.writeheader()
            for item in self.data_to_save:
                writer.writerow(asdict(item))
        self.csv_file_open = False

    def is_duplicate(self, input_data):
        if input_data.name in self.names_seen:
            logger.warning(f"Duplicate item found: {input_data.name}. Item dropped")
            return True
        self.names_seen.append(input_data.name)
        return False

    def add_data(self, scraped_data):
        if self.is_duplicate(scraped_data) == False:
            self.storage_queue.append(scraped_data)
            if len(self.storage_queue) >= self.storage_queue_limit and self.csv_file_open == False:
                self.save_to_csv()

    def close_pipeline(self):
        if self.csv_file_open:
            time.sleep(3)
        if len(self.storage_queue) > 0:
            self.save_to_csv()

def get_scrapeops_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'country': 'us'}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

#this function performs a search and parses the results
def search_page(query, page, location):
    #start Chrome with our custom options
    driver = webdriver.Chrome(options=options)
    #go to the page
    driver.get(get_scrapeops_url(f"https://www.google.com/search?q={query}&start={page * 10}"))
    #find each div containing site info...THEY'RE SUPER NESTED!!!
    divs = driver.find_elements(By.CSS_SELECTOR, "div > div > div > div > div > div > div > div > div > div > div > div > div > div")
    #list to hold our results
    results = []
    #index, this will be used to number the results
    index = 0
    #last link
    last_link = ""
    #iterate through our divs
    for div in divs:
        #find the title element
        title = div.find_elements(By.CSS_SELECTOR, "h3")
        link = div.find_elements(By.CSS_SELECTOR, "a")
        if len(title) > 0 and len(link) > 0:
            #result number on the page
            result_number = index        
            #site info object
            site_info = {"title": title[0].text, "link": link[0].get_attribute("href"), "result_number": result_number, "page": page}
            if site_info["link"] != last_link:
                #add the object to our list
                results.append(site_info)
                #increment the index
                index += 1
                #update the last link
                last_link = site_info["link"]
    #the scrape has finished, close the browser
    driver.quit()
    #return the result list
    return results
#function to search multiple pages, calls search_page() on each
def full_search(query, pages=3, location="United States"):
    #list for our full results
    full_results = []
    #list of page numbers
    page_numbers = list(range(0, pages))
    #open with a max of 5 threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        #call search page, pass all the following aruments into it
        future_results = executor.map(search_page, [query] * pages, page_numbers, [location] * pages)
        #for each thread result
        for page_result in future_results:
            #add it to the full_results
            full_results.extend(page_result)    
    #return the finalized list
    return full_results

if __name__ == "__main__":

    logger.info("Starting scrape")
    data_pipeline = DataPipeline(csv_filename="production-search.csv")

    search_results = full_search("cool stuff")

    for result in search_results:
        search_data = SearchData(name=result["title"], link=result["link"], result_number=result["result_number"] , page_number=result["page"])
        data_pipeline.add_data(search_data)

    data_pipeline.close_pipeline()
    logger.info("Scrape Complete")