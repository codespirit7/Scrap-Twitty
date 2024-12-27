import time
import pickle
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient


#Load environment variables
load_dotenv()


# configure the proxy
proxy_username = os.getenv("proxy_username")
proxy_password = os.getenv("proxy_password")
proxy_address = os.getenv("proxy_address")
proxy_port = os.getenv("proxy_port")


# configure the mongoDB atlas database
mongo_uri = os.getenv("mongo_uri")
client = MongoClient(mongo_uri)
db = client['twitter']
collection = db['data.trends']


# twitter credentials
twiter_username = os.getenv("twiter_username")
twitter_password = os.getenv("twitter_password")


# formulate the proxy url with authentication
proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_address}:{proxy_port}"


# set selenium-wire options to use the proxy
seleniumwire_options = {
    "proxy": {
        "http": proxy_url,
        "https": proxy_url
    },
}


# set Chrome options to run in headless mode
options = Options()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--disable-gpu")  # Disable GPU (Windows workaround)
options.add_argument("--no-sandbox")  # Bypass OS security model (Linux workaround)
options.add_argument("--disable-dev-shm-usage")  # Overcome shared memory issues
options.add_argument("--window-size=1920,1080")  # Ensure proper viewport size
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# initialize the Chrome driver with service, selenium-wire options, and chrome options
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    seleniumwire_options=seleniumwire_options,
    options=options
)



# Scrapping logic for Twitter

# file to save twitter login session
COOKIE_FILE = "twitter_cookies.pkl"

# save twitter login session into a file 
def save_cookies(driver, filepath):
    try:
        with open(filepath, "wb") as file:
            pickle.dump(driver.get_cookies(), file)
    except Exception as e:
        print("An error occurred in function: save_cookies", e)
        return


# loads twitter login session from a file for every scrap
def load_cookies(driver, filepath):
    try:
        with open(filepath, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
    except Exception as e:
        print("An error occurred in function: load_cookies", e)
        return


# Login twitter with credentials and saves the session into a file
def login_and_save_cookies(driver):
    """Login to Twitter and save cookies."""
    try:
        driver.get("https://x.com/i/flow/login")
        time.sleep(20)  # Wait for the page to load

        # Enter username
        username_field = driver.find_element('name', "text")
        username_field.send_keys(twiter_username)
        username_field.send_keys(Keys.RETURN)
        time.sleep(20)

        # Enter password
        password_field = driver.find_element('name', "password")
        password_field.send_keys(twitter_password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(20)

        # Save cookies after login
        save_cookies(driver, COOKIE_FILE)
    
    except Exception as e:
        print("An error occurred in function: login_and_save_cookies", e)
        return

#scrapping twitter homepage
def fetch_trending_topics(driver):
    try:
        # Wait until the elements are present on the page
        spans = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@data-testid="trend"]//div[2]/span[1]'))
        )

        # Extract the text of each span and store it in a list
        span_texts = [span.text for span in spans]

        # Print the list of texts in console
        print(span_texts)
        
        return span_texts

    except Exception as e:
        print("An error occurred in function  : fetch_trending_topics", e)
        return []


#store results in mongoDB
def store_results_in_mongo(unique_id, trends, timestamp, ip_address):
    
    try:
        numbered_trends = {f"Trend {i + 1}": trend for i, trend in enumerate(trends)}

        data = {
        "unique_id": unique_id,
        "trends": numbered_trends,
        "timestamp": timestamp,
        "ip_address": ip_address,
        }
    
        doc = collection.insert_one(data)
        return doc

    except Exception as e:
        print("An error occurred in function: store_results_in_mongo", e)
        return

  
# start of the script -> main function
def ScrapTwitter():
    #Load a session using saved cookies.
    try:
        driver.get("https://x.com/")
        time.sleep(3)
        load_cookies(driver, COOKIE_FILE)
        driver.refresh()
        time.sleep(5)  # Wait for the session to restore

        trending_topics = fetch_trending_topics(driver)

        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get IP address (from proxy)
        driver.get("https://api.ipify.org?format=json")
        
        # Get the IP address from the response
        ip_element = driver.find_element(By.TAG_NAME, "pre")
        print("Current IP Address:", ip_element.text)
        ip_text = ip_element.text 
        try:
            ip_data = json.loads(ip_text)  # Convert text to a dictionary
            ip_address = ip_data["ip"]  # Extract the IP address
        except json.JSONDecodeError:
            # If not JSON formatted, fallback to raw text
             ip_address = ip_text.strip()

        print("Current IP Address:", ip_address)

        # Store results in MongoDB
        store_results_in_mongo(unique_id, trending_topics, timestamp, ip_address)

        fetched_document = collection.find_one({"unique_id": unique_id}, {"_id": 0})  #Exclude the MongoDB ID
        
        driver.quit()

        print(fetched_document)

        return fetched_document

    except Exception as e:
        print("An error occurred in function: scrapTwitter", e)
        
        return []




"""For First-time login  and to save cookies, run the below command as well and comment it after that"""
# login_and_save_cookies(driver)


#To scrap the twitter trends
# trends = ScrapTwitter()

#print the twitter trends on console
# print(f"Data stored successfully: {trends}")


# release the resources and close the browser
# driver.quit()
