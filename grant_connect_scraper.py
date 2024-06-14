# scraping by the default sorting - starts with those closing soonest, ongoing at the end

# to activate venv: source venv/bin/activate

import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import re

driver = webdriver.Chrome()
driver.maximize_window()


# Opening CSV, writing header row
headers = ['Fund name', 'Total Amount Available', 'Estimated Grant Value', 'Location', 'Selection Process', 'Publish Date', 'Close Date & Time', 'Description', 'Eligibility', 'Grant Activity Timeframe', 'Agency', 'Primary Category', 'Secondary Category', 'Link']

file = open("grant_connect.csv", "w", newline='', encoding='utf-8')
writer = csv.writer(file)
writer.writerow(headers)

# Opening URL
url = 'https://www.grants.gov.au/Go/List'
driver.get(url)
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "mainContent"))) #update?

#Finding total number of grants
total_records = driver.find_element(By.XPATH, '/html/body/div[1]/div/main/div/form[2]/div/div/div/div[1]/strong').text

# Add all grant names and URLs to a list to be looped through later
grant_names_urls = []
while len(grant_names_urls) < int(total_records):
        try:
                grant_objects = driver.find_elements(By.CSS_SELECTOR, 'article[role="article"]')

                for grant_object in grant_objects:
                        grant_name = grant_object.find_element(By.CSS_SELECTOR, 'p.font20[role="heading"][aria-level="2"]').text.replace('–', '-')
                        grant_url_element = grant_object.find_element(By.CLASS_NAME, 'detail')
                        grant_url = grant_url_element.get_attribute('href')

                        grant_names_urls.append({'name': grant_name, 'url': grant_url})

                # After adding names and URLs to list, go to next page
                try:
                        next_page_button = driver.find_element(By.CSS_SELECTOR,  'li.next a[aria-label="Next Page"]')
                        next_page_button.click()

                except NoSuchElementException:
                        continue        

        except Exception as e:
            print(f"An error occurred: {e} for {grant_name}")
            continue

# Scraping info from each individual grant's URL
for grant in grant_names_urls:
        try:
                # Navigating to grant's URL
                driver.get(grant['url'])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'main[role="main"]'))) # update? maybe main is on the home page too


                # Assigning info from webpage to variables to write to CSV
                try:
                        total_amount = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Total Amount Available (AUD):')]/following-sibling::div[@class='list-desc-inner']/p").text
                except Exception as e:
                        total_amount = '' # change to 'Unknown'?

                try: 
                        estimated_value_element = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Estimated Grant Value (AUD):')]/following-sibling::div[@class='list-desc-inner']/p")
                        estimated_value = estimated_value_element.text
                except Exception as e:
                        estimated_value = '' 
                
                location = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Location:')]/following-sibling::div[@class='list-desc-inner']").text
                # if location is all states/territories, then location = 'National'
                if location == "ACT, NSW, VIC, SA, WA, QLD, NT, TAS" or location == 'ACT, NSW, VIC, SA, WA, QLD, NT, TAS, Administered Territories':
                        location = 'National'
                
                selection_process = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Selection Process:')]/following-sibling::div[@class='list-desc-inner']").text
                publish_date = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Publish Date:')]/following-sibling::div[@class='list-desc-inner']").text
                
                try:
                        close_date_long = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Close Date & Time:')]/following-sibling::div[@class='list-desc-inner']").text 
                        close_date_regex = r"^(.*?\(ACT Local Time\))"
                        match = re.search(close_date_regex, close_date_long)
                        close_date = match.group(1)
                except Exception as e:
                        close_date = 'Ongoing'

                try:
                        grant_timeframe = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Grant Activity Timeframe:')]/following-sibling::div[@class='list-desc-inner']").text
                except Exception as e:
                        grant_timeframe = '' 

                description = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Description:')]/following-sibling::div[@class='list-desc-inner']").text.replace('–', '-').replace("’", "'")
                eligibility = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Eligibility:')]/following-sibling::div[@class='list-desc-inner']").text.replace('–', '-').replace("’", "'")
                agency = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Agency:')]/following-sibling::div[@class='list-desc-inner']").text

                primary_category_long = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Primary Category:')]/following-sibling::div[@class='list-desc-inner']").text
                categories_regex = r"^\d+\s*-\s*"
                primary_category = re.sub(categories_regex, '', primary_category_long)

                try:
                        secondary_category_long = driver.find_element(By.XPATH, "//div[@class='list-desc']/span[contains(text(), 'Secondary Category:')]/following-sibling::div[@class='list-desc-inner']").text
                        secondary_category = re.sub(categories_regex, '', secondary_category_long)
                except Exception as e:
                        secondary_category = ''


        except Exception as e: # update
                print(f"An error occurred: {e} for {grant['name']}")
                writer.writerow([grant['name'], 'An error occured', '', '', '', '', '', '', '', '', '', '', '', ''])
                continue

        writer.writerow([grant['name'], total_amount, estimated_value, location, selection_process, publish_date, close_date, description, eligibility, grant_timeframe, agency, primary_category, secondary_category, grant['url']])
driver.quit()
file.close()

#updates: more robust error handling, e.g. timeouts

