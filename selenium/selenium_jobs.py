import csv
from selenium import webdriver
from selenium.webdriver.common.by import By

# Initialize the web driver (make sure the driver executable is in your PATH)
driver = webdriver.Chrome()
csvfile_path = '../jobs/jobs1.csv'

# Read links from a CSV file (assuming 'links.csv' has a 'url' column)
with open('links.csv', 'r', encoding='utf-8') as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        url = row['link']
        try:
            # Open the URL in the web driver
            driver.get(url)

            # Add your scraping logic here
            # For example, you can find elements by their XPath or CSS selector
            # and extract data from them using .text
            element = driver.find_element(By.XPATH, '//h1')
            data = element.text
            print(f"Data from {url}: {data}")

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

# Close the web driver when done
driver.quit()
