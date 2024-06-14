# to activate venv: source venv_name/bin/activate

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
import time
import os
import tkinter as tk
from tkinter import ttk

driver = webdriver.Chrome()

# Helper function to check if elements are on main part of webpage, if not, they are 'Unknown'
def find_element_or_unknown(xpath, driver=driver):
    try:
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script('arguments[0].scrollIntoView(true);', element)
        return element.text
    except:
        return ""
    
# Helper function for elements that change their location on webpage (on the side columns - located by following a parent element). If not found they are "Unknown"
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

# Function that will filter results by industry/industries that user selects from listbox
def industry_filter(driver):
    #Driver navigating to the website's industries filter
    find_industry_button = driver.find_element(By.XPATH, '//*[@id="industry"]/div/div/div[1]/div')
    find_industry_button.click()
    time.sleep(2) # update?
    
    root = tk.Tk()
    root.title("Select Industries")
    
    # Availale industries on webiste -- MAY NEED UPDATING
    industries = [
        "General - Non-Industry Specific",
        "Aeronautics",
        "Agriculture",
        "Automotive and Marine",
        "Building, Construction and Engineering",
        "Defence",
        "Education",
        "Energy and Renewables",
        "Finance and Business Services",
        "Food and Beverage",
        "Healthcare, Medical, Biotechnology and Nanotechnology",
        "Information Technology and Communication (ICT)",
        "Media and Entertainment",
        "Mining",
        "Textile, Clothing and Footwear",
        "Tourism",
        "Other - Not Listed"
    ]
          
    # Creating an empty list that users' selected industries will be added to
    selected_industries = []
    
    
    def on_select(event):
        selected_industries.clear()
        selections = listbox.curselection()
        for i in selections:
            selected_industries.append(listbox.get(i))    
        
    label = tk.Label(root, text="Select the industry/industries that you wish to filter for:")
    label.pack(pady=10) # 10 pixels of padding above and below 
    
    # Creating a listbox widget
    listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
    for industry in industries:
        listbox.insert(tk.END, industry)
    listbox.pack(pady=10)
    listbox.bind('<<ListboxSelect>>', on_select)
    
    def on_submit():
        for i in selected_industries:
            select_industry_button = driver.find_element(By.XPATH, f"//div[@class='FilterItem_subItemTitle__0hHSn' and text()='{i}']")
            select_industry_button.click()
            time.sleep(2) #update?
        root.destroy()

    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=20)

    root.mainloop()
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


headers = ['Fund name', 'Min funding', 'Max funding', 'Funding pool', 'Status', 'Opening date', 'Closing date', 'Closing info', 'Funding type', 'Co-contribution?', 'Competitive?', 'Description', 'Who can apply?', 'Department', 'Industries', 'Link']

# Opening CSV, writing header row
file = open("grant_guru_by_industry.csv", "w", newline='', encoding='utf-8')
writer = csv.writer(file)
writer.writerow(headers)

def scrape_grants(total_count, driver):
    grants_scraped = 0
    grants_processed = 0
    current_loaded_grants = 0
    last_grant = 0
    grants_name_url = []

    while grants_processed < total_count:
        while grants_processed < total_count:
            try:
                fund_name_elements = driver.find_elements(By.CLASS_NAME, 'ResultItemStyle_title__EZ8KP')
                fund_url_elements = driver.find_elements(By.CLASS_NAME, 'ResultItemStyle_linkContainer__WP0dx')
                current_loaded_grants = len(fund_name_elements)

                if current_loaded_grants >= total_count:
                    break
                last_grant = fund_name_elements[-1]
                driver.execute_script('arguments[0].scrollIntoView(true);', last_grant)
                WebDriverWait(driver, 10).until(lambda driver: len(driver.find_elements(By.CLASS_NAME, 'ResultItemStyle_title__EZ8KP')) > current_loaded_grants)
        
            except TimeoutException or NoSuchElementException:
                print('No more grants to load')
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
                
        for i in range(grants_processed, len(fund_name_elements)):
            if i >= total_count:
                break
            name = fund_name_elements[i].text.replace('–', '-') 
            url = fund_url_elements[i].get_attribute('href')
            grants_name_url.append({'name': name, 'url': url})

        grants_processed = len(fund_name_elements)

    for grant in grants_name_url: 
        try:
            driver.get(grant['url'])
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Overview"]/p/p[1]')))

            description = find_element_or_unknown('//*[@id="Overview"]/p', driver)
            max_funding = find_changing_element('Max Funding', driver)
            min_funding = find_changing_element('Min Funding', driver)
            status = find_changing_element('Status', driver)
            opening_date = find_changing_element('Opening Date', driver)
            closing_date = find_changing_element('Closing Date', driver)
            closing_info = find_changing_element('Closing Info', driver)
            funding_pool = find_changing_element('Total Funding Pool', driver)
            competitive = find_changing_element('Competitive', driver)

            try:
                contribution_header = driver.find_element(By.XPATH, "//span[contains(@class, 'Sidebar_detailKey__90Jx_') and contains(text(), 'Requires')]")
                contribution_elements = contribution_header.find_elements(By.XPATH, ".//following::div[contains(@class, 'Sidebar_infoWithExtra__62Qzq')][1]")
                driver.execute_script('arguments[0].scrollIntoView(true);', contribution_elements[0])
                contribution = contribution_elements[0].text
            except Exception as e:                
                contribution = ""

            industries = find_changing_element('Industries', driver)
            funding_type = find_changing_element('Funding Type', driver)
            department = find_changing_element('Department', driver)
            who = find_element_or_unknown('//*[@id="WhoCanApply"]/p', driver)

            writer.writerow([grant['name'], min_funding, max_funding, funding_pool, status, opening_date, closing_date, closing_info, funding_type, contribution, competitive, description, who, department, industries, grant['url']])
            grants_scraped += 1

        except Exception as e:
            print(f"An error occurred: {e} for {grant['name']}")
            writer.writerow([grant['name'], 'An error occurred', '', '', '', '', '', '', '', '', '', '', '', ''])
            continue
        print(f"grant: {grant}")



def main():
    driver = webdriver.Chrome()
    driver.maximize_window()

    login_url = 'https://grantguru.com/au/login'
    driver.get(login_url)
    time.sleep(5)
    #WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, "login")))

    load_dotenv()
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    email_input = driver.find_element(By.NAME, "login")
    password_input = driver.find_element(By.NAME, 'password')
    login_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div[1]/form/button')

    email_input.send_keys(email)
    password_input.send_keys(password)
    login_button.click()
    time.sleep(5)
    # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[2]/div/div/div/ul/li[1]')))

    find_grants_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[2]/div/div/div/ul/li[1]')
    find_grants_button.click()
    time.sleep(5)
    #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]')))
    
    # Filtering for industry/industries
    industry_filter(driver)
    
    # Sorting results by 'Recent alert'
    sort_button = driver.find_element(By.CLASS_NAME, 'GSortStyle_label__phn9R')
    #sort_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]') # update to class_name?
    sort_button.click()
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/div/div/div')))
    recent_alert_button = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/div/div/ul/li[3]')
    recent_alert_button.click()
    time.sleep(3)
    #WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[2]/div/span[2]')))

    # Finding total number of grants
    total_count_and_worth = driver.find_element(By.XPATH, '//*[@id="main-layout"]/div[5]/div[4]/div/div/div[1]/div/div[1]/div[1]/span').text
    match = re.search(r'\d+', total_count_and_worth)
    total_count = int(match.group()) if match else 'N/A'
    print('total_count: ', total_count)

    # Scrape
    scrape_grants(total_count, driver)

    print(f'{total_count} grants scraped and written to grant_guru_by_industry.csv')
    driver.quit() 
    time.sleep(5) # break to read file before it closes
    file.close()
    
if __name__ == "__main__":
    main()


# check department
# add industry names to file
# spot check