from selenium import webdriver
from selenium.webdriver.common.by import By
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
    #iterate through our pages
    for page in range(0, pages):
        #get the results of the page
        page_results = search_page(query, page, location)
        #add them to the full_results list
        full_results.extend(page_results)
    #return the finalized list
    return full_results
####this is our main program down here####
search_results = full_search("cool stuff")
#print our results
for result in search_results:
    print(result)