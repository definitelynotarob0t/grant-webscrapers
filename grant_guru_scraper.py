# to activate venv: source venv/bin/activate

import time
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import os
from dotenv import load_dotenv


driver = webdriver.Chrome()

# Helper function to check if elements are on main part of webpage, if not, they will be blank
def find_element_or_unknown(xpath, driver=driver):
    try:
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script('arguments[0].scrollIntoView(true);', element)
        return element.text
    except:
        return ""
    
# Helper function for elements that change their location on webpage (on the side columns - located by following a parent element). If not found they will be blank
def find_changing_element(element_to_find, driver=driver):
    try:
        key_elements = driver.find_elements(By.CLASS_NAME, "Sidebar_detailKey__90Jx_")

        for key_element in key_elements:
            if key_element.text == element_to_find:
                value_elements = key_element.find_elements(By.XPATH, ".//following::div[contains(@class, 'Sidebar_infoWithExtra__62Qzq')][1]")
                if value_elements:
                    driver.execute_script('arguments[0].scrollIntoView(true);', key_element)
                    return value_elements[0].text
        return ""
    except Exception as e:
        print(f"An error occurred while trying to find{element_to_find}: {e}")
        return ""

headers = ['Fund name', 'Min funding', 'Max funding', 'Funding pool', 'Status', 'Opening date', 'Closing date', 'Closing info', 'Funding type', 'Co-contribution?', 'Competitive?', 'Description', 'Who can apply?', 'Department', 'Link', 'Industries']

# Opening CSV, writing header row
file = open("grant_guru.csv", "w", newline='', encoding='utf-8')
writer = csv.writer(file)
writer.writerow(headers)

# Scroll until loaded all grants from today to user_date
def scroll_and_load(user_date, driver):
    grants_name_url = []
    scroll_continue = True

    while scroll_continue:
        new_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        try: #  logic if scroll is needed to load all requested grants
            WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.body.scrollHeight") > new_height)
            time.sleep(1)
            
        except TimeoutException: 
            # logic if scroll is not needed to load all requested grants
            if driver.execute_script("return document.body.scrollHeight") == new_height: 
                scroll_continue = False
            else:
                print("Timeout while waiting for the page to load")

        grant_objects = driver.find_elements(By.CLASS_NAME, 'ResultItemStyle_container__UYc1r')
        for grant_object in grant_objects:
            try: 
                date_element = grant_object.find_element(By.XPATH, ".//th[contains(text(), 'Notice')]/following-sibling::td/span/span[last()]")
                grant_date = datetime.strptime(date_element.text.strip(), '%d %b %Y')

                if grant_date < user_date:
                    scroll_continue = False
                    return grants_name_url
            
            except Exception as e:
                print(f'Error parsing date: {e}')

            # Extracting the grant name
            grant_name_element = grant_object.find_element(By.XPATH, ".//h2[@class='ResultItemStyle_title__EZ8KP']")
            grant_name = grant_name_element.text.replace('–', '-')

            # Extracting the grant URL
            grant_url_element = grant_object.find_element(By.XPATH, ".//a[@class='ResultItemStyle_linkContainer__WP0dx']")
            grant_url = grant_url_element.get_attribute('href')

            # Collect the data in a dictionary and append to the list
            grants_name_url.append({'name': grant_name, 'url': grant_url})

    return grants_name_url

def main():
    driver.maximize_window()
    
    # Opening URL and logging in
    login_url = 'https://grantguru.com/au/login'
    driver.get(login_url)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, "login")))
    
    load_dotenv()
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    email_input = driver.find_element(By.NAME, "login")
    password_input = driver.find_element(By.NAME, 'password')
    login_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div[1]/form/button')

    email_input.send_keys(email)
    password_input.send_keys(password)
    login_button.click()
    time.sleep(5) #update

    # Navigating to grants page
    find_grants_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[2]/div/div/div/ul/li[1]')
    find_grants_button.click()
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]')))

    # Sorting results by 'Recent alert'
    sort_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]')
    sort_button.click()
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/div/div/div')))
    recent_alert_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/div/div/ul/li[3]')
    recent_alert_button.click()
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]')))

    user_input = input('Enter the date (DD MMM YYYY) until which you want grant information: ')
    try:
        user_date = datetime.strptime(user_input, '%d %b %Y')
    except ValueError:
        print("Invalid input. Please enter the date in the format 'DD MMM YYYY'.")
        try:
            user_date = datetime.strptime(user_input, '%d %b %Y')
        except ValueError:
            return

    grants_name_url = scroll_and_load(user_date, driver)
    grants_scraped = 0

    # Scraping logic
    for grant in grants_name_url: 
    
        print(f'{grant = }')
        try:
            # Navigating to grant's URL
            driver.get(grant['url'])
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Overview"]/p/p[1]')))

            # Finding info and assigning to variables (roughly ordered by what appears on page)
            description = find_element_or_unknown('//*[@id="Overview"]/p')
            max_funding = find_changing_element('Max Funding')
            min_funding = find_changing_element('Min Funding')
            status = find_changing_element('Status')
            opening_date = find_changing_element('Opening Date')
            closing_date = find_changing_element('Closing Date')
            closing_info = find_changing_element('Closing Info')
            funding_pool = find_changing_element('Total Funding Pool')
            competitive = find_changing_element('Competitive')

            ## Contribution header is split by a <br>, cannot use helper functions
            try:
                contribution_header = driver.find_element(By.XPATH, "//span[contains(@class, 'Sidebar_detailKey__90Jx_') and contains(text(), 'Requires')]")
                contribution_elements = contribution_header.find_elements(By.XPATH, ".//following::div[contains(@class, 'Sidebar_infoWithExtra__62Qzq')][1]")
                driver.execute_script('arguments[0].scrollIntoView(true);', contribution_elements[0])
                contribution = contribution_elements[0].text
            except Exception as e:                
                contribution = ""

            industries = find_changing_element('Industries')
            funding_type = find_changing_element('Funding Type')
            department = find_changing_element('Department')
            who = find_element_or_unknown('//*[@id="WhoCanApply"]/p')

            # Writing grant info into CSV
            writer.writerow([grant['name'], min_funding, max_funding, funding_pool, status, opening_date, closing_date, closing_info, funding_type, contribution, competitive, description, who, department, grant['url'], industries])
            grants_scraped += 1

        except Exception as e:
            print(f"An error occurred: {e} for {grant['name']}")
            writer.writerow([grant['name'], 'An error occured', '', '', '', '', '', '', '', '', '', '', '', ''])
            continue

    print(f'{len(grants_name_url)} grants scraped and written to grant_guru.csv')

if __name__ == "__main__":
    main()
    driver.quit() 
    time.sleep(5) # break to read file before it closes
    file.close()

# spot check
# add logins to gitignore ? 
# update wait times