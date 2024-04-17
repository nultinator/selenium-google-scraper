from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
from concurrent.futures import ThreadPoolExecutor
#create a custom options instance
options = webdriver.ChromeOptions()
#add headless mode to our options
options.add_argument("--headless")
#this function performs a search and parses the results
def search_page(query, page, location):
    #start Chrome with our custom options
    driver = webdriver.Chrome(options=options)
    #go to the page
    driver.get(f"https://www.google.com/search?q={query}&start={page * 10}&location={location}")
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
        #find the link element
        link = div.find_elements(By.CSS_SELECTOR, "a")
        #result number on the page
        result_number = index
        #if we have a result
        if len(title) > 0:
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
####this is our main program down here####
#results from the search
search_results = full_search("cool stuff")
#path to the csv file
path_to_csv = "concurrency.csv"
#open the file in write mode
with open(path_to_csv, "w") as file:
    #format the file based on the keys of the first result
    writer = csv.DictWriter(file, search_results[0].keys())
    #write the headers
    writer.writeheader()
    #write each object as a row in the file
    writer.writerows(search_results)
