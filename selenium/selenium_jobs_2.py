import csv
import random
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
import pandas as pd

# Set up logging
logging.basicConfig(filename='scraping.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

# Constants
desired_language = 'en-US'
BASE_DIR = 'C:\\Users\\aky\\AppData\\Local\\Programs\\Python\\Python38\\course-u\\src\\linkedin_scrapy\\'
csv_input_link = BASE_DIR + 'jobs\\jobs_clean_2.csv'
csv_output = BASE_DIR + 'selenium\\jobs_post_2.csv'
target_count = 10
save_to_csv = True

# User agents
user_agents = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; rv:85.0) Gecko/20100101 Firefox/85.0",
]

# Create Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--lang={}'.format(desired_language))

# Function to get a random user agent
def get_random_user_agent():
    return random.choice(user_agents)

# Function to clean the link
def clean_link(link):
    if link:
        parts = link.split('&')
        if parts:
            first_part = parts[0]
            return first_part.replace('ph.', '')
    return None

# Function to get text from an element
def get_text(xpath):
    try:
        return WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, xpath))).text
        #return driver.find_element(By.XPATH, xpath).text
    except:
        return None

# Function to extract job data
def extract_job_data(job, keyword):
    return {
        'link': clean_link(job.css('a.base-card__full-link ::attr(href)').get()),
        'keyword': keyword,
        'title': job.css('h3::text').get().strip(),
        'company': job.css('a.hidden-nested-link::text').get().strip(),
        'company_link': job.css('a.hidden-nested-link::attr(href)').get(),
        'date': job.css('time::attr(datetime)').get(),
    }

# Define a threshold for the number of scraped URLs before introducing a sleep
sleep_threshold = 50  # Adjust this value as needed

# Main scraping function
def scrape_jobs(url, row):
    driver = webdriver.Chrome(chrome_options=options)
    scraped_urls = set()
    success_count = 0
    skipped_count = 0
    need_login_count = 0
    has_missing_data_count = 0
    finished_count = 0
    
    df = pd.DataFrame(columns=['jobpost_id', 'Link', 'Job_Title', 'Company_Name', 'Company_link', 'Date',
                               'Keyword', 'Keyword_id', 'Location', 'Employment_Type', 'Job_Function',
                               'Industries', 'Seniority_Level', 'Job_Description'])

    total_count = 0

    while total_count < target_count:
        url = row['link']
        total_count += 1
        max_retries = 2
        retry_count = 0

        selected_user_agent = get_random_user_agent()
        options.add_argument(f"user-agent={selected_user_agent}")

        cleaned_url = clean_link(url)

        if cleaned_url not in scraped_urls:
            try:
                driver.get(cleaned_url)
                isLogin = get_text("//h1")
                if isLogin == 'Join LinkedIn':
                    logging.info("Sign in required. Skipping this URL...")
                    skipped_count += 1
                    need_login_count += 1
                    retry_count = max_retries
                    continue

                Job_Title = get_text("//h1")
                Location = get_text("//span[@class='topcard__flavor topcard__flavor--bullet']")
                Seniority_Level = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[1]")
                Employment_Type = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[2]")
                Job_Function = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[3]")
                Industries = get_text("(//span[@class='description__job-criteria-text description__job-criteria-text--criteria'])[4]")

                driver.find_element(By.XPATH, "//button[@aria-label='Show more, visually expands previously read content above']").click()
                Job_Description = driver.find_element(By.XPATH, "//div[@class='show-more-less-html__markup relative overflow-hidden']").get_attribute('innerHTML')

                if None in (Job_Title, Location, Employment_Type, Job_Function, Industries, Seniority_Level):
                    logging.info("One or more data points are missing. Skipping this URL...")
                    skipped_count += 1
                    retry_count = max_retries
                    has_missing_data_count += 1
                    continue
                else:
                    logging.info("Scraping successful!")

                data = {
                    'jobpost_id': success_count + 1,
                    'Link': cleaned_url,
                    'Job_Title': Job_Title,
                    'Company_Name': row['company'],
                    'Company_link': clean_link(row['company_link']),
                    'Date': row['date'],
                    'Keyword': row['keyword'],
                    'Keyword_id': keyword_id_mapping[row['keyword']],
                    'Location': Location,
                    'Seniority_Level': Seniority_Level,
                    'Employment_Type': Employment_Type,
                    'Job_Function': Job_Function,
                    'Industries': Industries,
                    'Job_Description': Job_Description
                }

                df = df.append(data, ignore_index=True)
                success_count += 1

                logging.info("Job Title: %s", Job_Title)
                logging.info("Company Name: %s", row['company'])
                logging.info("Date: %s", row['date'])
                logging.info("Keyword: %s", row['keyword'])
                logging.info("Location: %s", Location)
                logging.info("Employment Type: %s", Employment_Type)
                logging.info("Job Function: %s", Job_Function)
                logging.info("Industries: %s", Industries)
                logging.info("Seniority Level: %s", Seniority_Level)

                logging.info(Job_Description)
                logging.info("-" * 50)

            except TimeoutException:
                retry_count += 1
                logging.info("TimeoutException scraping %s", url)
            except Exception as e:
                logging.info("Error scraping %s: %s", url, str(e))

        scraped_urls.add(cleaned_url)
        finished_count += 1
        time.sleep(random.randint(1, 5))

        if total_count == target_count:
            logging.info("Target count reached. Exiting...")
            break

        # Introduce a sleep if the threshold is reached
        if finished_count % sleep_threshold == 0:
            sleep_duration = random.randint(180, 300)  # Sleep for 3-5 minutes
            logging.info("Reached the sleep threshold. Sleeping for %s seconds...", sleep_duration)
            time.sleep(sleep_duration)

    driver.quit()

    if save_to_csv:
        df.to_csv(csv_output, index=False, encoding='utf-8')

    print(f"Total URLs: {total_count} out of {target_count}")
    print(f"Scraped URLs: {success_count} out of {target_count}")
    print(f"Skipped URLs: {skipped_count} out of {target_count}")
    print(f"Need Login URLs: {need_login_count} out of {skipped_count} skipped")
    print(f"Missing Data URLs: {has_missing_data_count} out of {skipped_count} skipped")
    print(f"Finished URLs: {finished_count} out of {target_count}")
    print("Done!")

# Initialize the web driver (make sure the driver executable is in your PATH)
driver = webdriver.Chrome(chrome_options=options)

# Keyword ID mapping
keyword_id_mapping = {
    "software development": 1,
    "data and analytics": 2,
    "design and ui/ux": 3,
    "testing and quality assurance": 4,
    "networking and infrastructure": 5
}

# Main loop
with open(csv_input_link, 'r', encoding='utf-8') as csvfile:
    csvreader = csv.DictReader(csvfile)

    for row in csvreader:
        scrape_jobs(row['link'], row)
