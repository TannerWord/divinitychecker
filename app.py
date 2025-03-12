from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os
import subprocess
import time

app = Flask(__name__)

# ✅ Install Chrome
CHROME_PATH = "/tmp/chrome/chrome-linux64/chrome"
CHROMEDRIVER_PATH = "/tmp/chromedriver/chromedriver-linux64/chromedriver"

def install_chrome():
    if not os.path.exists(CHROME_PATH):
        print("🔄 Downloading and installing Chrome...")
        os.makedirs("/tmp/chrome", exist_ok=True)
        subprocess.run(
            "curl -Lo /tmp/chrome/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip && "
            "unzip /tmp/chrome/chrome.zip -d /tmp/chrome/ && chmod +x /tmp/chrome/chrome-linux64/chrome",
            shell=True, check=True
        )
        print("✅ Chrome Installed Successfully")

def install_chromedriver():
    if not os.path.exists(CHROMEDRIVER_PATH):
        print("🔄 Downloading and installing ChromeDriver...")
        os.makedirs("/tmp/chromedriver", exist_ok=True)
        subprocess.run(
            "curl -Lo /tmp/chromedriver/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip && "
            "unzip /tmp/chromedriver/chromedriver.zip -d /tmp/chromedriver/ && chmod +x /tmp/chromedriver/chromedriver-linux64/chromedriver",
            shell=True, check=True
        )
        print("✅ ChromeDriver Installed Successfully")

install_chrome()
install_chromedriver()

# 🔗 Website & Credentials
LOGIN_URL = "https://dilutiontracker.com/login"
USERNAME = "your_email@example.com"
PASSWORD = "your_password"

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = CHROME_PATH
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login(driver):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in with email')]")))
    login_button.click()
    time.sleep(5)

def scrape_ticker(ticker):
    driver = get_driver()
    login(driver)
    ticker_url = f"https://dilutiontracker.com/app/search/{ticker}?a=231sb8"
    driver.get(ticker_url)
    time.sleep(5)
    
    def extract_text(by, identifier):
        try:
            return driver.find_element(by, identifier).text.strip()
        except:
            return "Not Found"
    
    data = {
        "Ticker": extract_text(By.CLASS_NAME, "ticker"),
        "Market Cap": extract_text(By.XPATH, "//span[contains(text(), 'Mkt Cap')]/following::span[@class='mr-4 pr-1']"),
        "Float": extract_text(By.XPATH, "//div[@id='company-description-float-wrapper']//span[@class='mr-4 pr-1']"),
        "Institutional Ownership": extract_text(By.XPATH, "//span[contains(text(), 'Inst Own')]/following::span[1]"),
        "Overall Risk": extract_text(By.ID, "drOverallRisk"),
        "Offering Ability": extract_text(By.ID, "drOfferingAbility"),
        "Historical": extract_text(By.ID, "drHistorical"),
        "Cash Need": extract_text(By.ID, "drCashNeed"),
        "Cash Position": extract_text(By.XPATH, "//p[contains(text(), 'Cash Position')]/following-sibling::p"),
    }
    driver.quit()
    return data

# ✅ Webhook Endpoint for n8n
@app.route('/run_ticker_check', methods=['POST'])
def run_ticker_check():
    try:
        request_data = request.get_json()
        ticker = request_data.get("ticker")
        if not ticker:
            return jsonify({"status": "error", "message": "Ticker parameter is required"}), 400
        data = scrape_ticker(ticker)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ Start the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)













