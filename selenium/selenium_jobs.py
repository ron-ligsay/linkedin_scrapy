import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import time
import pandas as pd
import logging

# set up logging
logging.basicConfig(filename='scraping.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

# Set the desired language
desired_language = 'en-US'

# Create Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--lang={}'.format(desired_language))

# Initialize the web driver (make sure the driver executable is in your PATH)

driver = webdriver.Chrome(chrome_options=options) #,executable_path=driver_path

BASE_DIR = 'C:\\Users\\aky\\AppData\\Local\\Programs\\Python\\Python38\\course-u\\src\\linkedin_scrapy\\selenium\\'
csv_input_link = BASE_DIR + 'jobs1.csv'
csv_output = BASE_DIR + 'jobs_post.csv'

# Define a set to store scraped URLs
scraped_urls = set()

target_count = 100
total_count = 0
success_count = 0
skipped_count = 0
finished_count = 0

save_to_csv = True


# get text by xpath
def get_text(xpath):
    try:
        return driver.find_element(By.XPATH, xpath).text
    except:
        return None

display = True
log = False

def show_report(message, data=None):
    if display:
        print(message, data)
    if log:
        logging.info(message, data)

# Create the CSV file and write the header row
fieldnames = ['jobpost_id','Link', 'Job_Title', 'Company_Name', 'Company_link','Date','Keyword','Location', 'Employment_Type', 'Job_Function', 'Industries', 'Seniority_Level','Job_Description']
df = pd.DataFrame(columns=fieldnames)

# include column in csv_input_link
# columns_to_include = ['link','keyword','title','company','company_link','date']

# Read links from a CSV file (assuming 'links.csv' has a 'url' column)
with open(csv_input_link, 'r', encoding='utf-8') as csvfile:
    csvreader = csv.DictReader(csvfile)

    for row in csvreader:
        url = row['link']
        total_count += 1
        try:
            # Remove ".ph" from the URL
            cleaned_url = url.replace('ph.', '')

            # Remove unnecessary query parameters
            cleaned_url = cleaned_url.split('?')[0]
            
            # Check if the URL has been scraped before
            if cleaned_url not in scraped_urls:
                # Display url
                show_report("Now Scraping Link: ", cleaned_url)
                print(total_count, " out of ", target_count)

                # Open the URL in the web driver
                driver.get(cleaned_url)

                # Pause for a few seconds after opening the page
                #time.sleep(30)
                
                Job_Title = get_text("//h1")
                
                #Company_Name = get_text("//a[@class='topcard__org-name-link topcard__flavor--black-link']")
                Location = get_text("//span[@class='topcard__flavor topcard__flavor--bullet']")
                Seniority_Level = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[1]")
                Employment_Type = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[2]")
                Job_Function = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[3]")
                Industries = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[4]")
                
                
                # click see more
                driver.find_element(By.XPATH,"//button[@aria-label='Show more, visually expands previously read content above']").click()
                # get html content
                Job_Description = driver.find_element(By.XPATH,"//div[@class='show-more-less-html__markup relative overflow-hidden']").get_attribute('innerHTML')
                
                #Company_Description = get_text()
                #Company_Website = get_text()

                # Check if any of the scraped data is empty
                if None in (Job_Title, Location, Employment_Type, Job_Function, Industries, Seniority_Level): #Company_Name, 
                    # Skip this URL
                    show_report("One or more data points are missing. Skipping this URL...")
                    skipped_count += 1
                    continue
                else:        
                    show_report("Scraping successful!")
                    # Write data to the CSV file
                    #  ['jobpost_id','Link', 'Job_Title', 'Company_Name', 'Company_link','Date','Keyword','Location', 'Employment_Type', 'Job_Function', 'Industries', 'Seniority_Level','Description']
                
                if save_to_csv:
                    data = {
                        'jobpost_id': success_count+1,
                        'Link': cleaned_url,
                        'Job_Title': Job_Title,
                        'Company_Name': row['company'],
                        'Company_link': row['company_link'], # 'Company_Link': Company_Link,
                        'Date' : row['date'],
                        'Keyword': row['keyword'], # 'Keyword': Keyword,
                        'Location': Location,
                        'Seniority_Level': Seniority_Level,
                        'Employment_Type': Employment_Type,
                        'Job_Function': Job_Function,
                        'Industries': Industries,
                        
                        'Job_Description': Job_Description
                    }

                    # Append the data to the DataFrame
                    df = df.append(data, ignore_index=True)
                    success_count += 1

                    # Print for Verification
                    #show_report(Job_Title, " from ", Company_Name)
                    show_report("Job Title: ", Job_Title)
                    show_report("Company Name: ", row['company'])
                    show_report("Date: ", row['date'])
                    show_report("Keyword: ", row['keyword'])
                    show_report("Location: ", Location)
                    show_report("Employment Type: ", Employment_Type)
                    show_report("Job Function: ", Job_Function)
                    show_report("Industries: ", Industries)
                    show_report("Seniority Level: ", Seniority_Level)
                    # print html content with tags
                    show_report(Job_Description)
                    #print("Job Description: ", Job_Description)

                    show_report("-"*50)

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

        finished_count += 1

        # exit after N link
        if total_count == target_count:
           show_report("Target count reached. Exiting...")
           break
        

# Close the web driver when done
driver.quit()

# Save the DataFrame to a CSV file
if save_to_csv:
    df.to_csv(csv_output, index=False, encoding='utf-8')


# Print some stats
print(f"Total URLs: {total_count} out of {target_count}")
print(f"Scraped URLs: {success_count} out of {target_count}")
print(f"Skipped URLs: {skipped_count} out of {target_count}")
print(f"Finished URLs: {finished_count} out of {target_count}")
print("Done!")
