import time
import json
import os
import subprocess
import undetected_chromedriver as uc
from flask import Flask, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ Install Chrome in a writable directory (/tmp/chrome/)
def install_chrome():
    chrome_path = "/tmp/chrome/chrome-linux64/chrome"
    if not os.path.exists(chrome_path):
        print("🔄 Downloading and installing Chrome...")
        os.makedirs("/tmp/chrome", exist_ok=True)
        subprocess.run(
            "curl -Lo /tmp/chrome/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip && unzip /tmp/chrome/chrome.zip -d /tmp/chrome/ && chmod +x /tmp/chrome/chrome-linux64/chrome",
            shell=True,
            check=True
        )
        print("✅ Chrome Installed Successfully")

# ✅ Install ChromeDriver in a writable directory (/tmp/chromedriver/)
def install_chromedriver():
    driver_path = "/tmp/chromedriver/chromedriver-linux64/chromedriver"
    if not os.path.exists(driver_path):
        print("🔄 Downloading and installing ChromeDriver...")
        os.makedirs("/tmp/chromedriver", exist_ok=True)
        subprocess.run(
            "curl -Lo /tmp/chromedriver/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip && unzip /tmp/chromedriver/chromedriver.zip -d /tmp/chromedriver/ && chmod +x /tmp/chromedriver/chromedriver-linux64/chromedriver",
            shell=True,
            check=True
        )
        print("✅ ChromeDriver Installed Successfully")

# ✅ Ensure Chrome & ChromeDriver are installed
install_chrome()
install_chromedriver()

# 🔥 Initialize Flask App
app = Flask(__name__)

# 🔒 Hardcoded Login Details
LOGIN_URL = "https://ventureresorts.trackhs.com/owner"
USERNAME = "wordpropertiesmanagement@gmail.com"
PASSWORD = "DivinityManagement777"

def scrape_reservations():
    """Runs the scraper and returns reservation data as a list of dictionaries."""

    # ✅ Setup Undetected Chrome WebDriver
    options = uc.ChromeOptions()
    options.binary_location = "/tmp/chrome/chrome-linux64/chrome"  # ✅ Manually set Chrome path
    options.add_argument("--headless")  # Run in headless mode for Render
    options.add_argument("--no-sandbox")  # Required for Render
    options.add_argument("--disable-dev-shm-usage")  # Prevents memory issues
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
    options.add_argument("--disable-gpu")

    # ✅ Manually specify ChromeDriver path
    driver = uc.Chrome(
        options=options,
        browser_executable_path="/tmp/chrome/chrome-linux64/chrome",
        driver_executable_path="/tmp/chromedriver/chromedriver-linux64/chromedriver"
    )

    try:
        # Open TrackHS login page
        driver.get(LOGIN_URL)
        time.sleep(3)

        # Wait for login form
        wait = WebDriverWait(driver, 10)
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))

        # Enter credentials and login
        username_input.send_keys(USERNAME)
        time.sleep(1)
        password_input.send_keys(PASSWORD)
        time.sleep(1)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

        # Wait for login
        time.sleep(5)

        # ✅ Navigate to Reservations Page
        reservations_url = "https://ventureresorts.trackhs.com/owner/availability/"
        driver.get(reservations_url)
        time.sleep(5)

        # ✅ Force select "100 rows" using JavaScript
        try:
            row_selector = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "DataTables_Table_0_length"))
            )
            driver.execute_script("arguments[0].value = '100'; arguments[0].dispatchEvent(new Event('change'));", row_selector)
            time.sleep(3)
        except Exception:
            pass  # Continue if it fails

        # 🔍 Step 1: Find Table Headers and Determine Column Positions
        header_cells = driver.find_elements(By.XPATH, "//table/thead/tr/th")
        column_map = {}

        for index, cell in enumerate(header_cells):
            header_text = cell.text.strip().lower()
            if "guest" in header_text or "name" in header_text:
                column_map["guest_name"] = index
            elif "check-in" in header_text or "arrival" in header_text:
                column_map["check_in"] = index
            elif "check-out" in header_text or "departure" in header_text:
                column_map["check_out"] = index
            elif "type" in header_text or "unit" in header_text:
                column_map["type"] = index
            elif "income" in header_text or "total" in header_text or "amount" in header_text:
                column_map["income"] = index
            elif "nights" in header_text or "stay" in header_text:
                column_map["nights"] = index

        # 🔍 Step 2: Extract Reservation Data Using Mapped Columns
        reservations = []
        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) > max(column_map.values()):
                guest_name = cells[column_map["guest_name"]].text.strip()
                check_in = cells[column_map["check_in"]].text.strip()
                check_out = cells[column_map["check_out"]].text.strip()
                res_type = cells[column_map["type"]].text.strip()
                income = cells[column_map["income"]].text.strip()
                nights = cells[column_map["nights"]].text.strip() if "nights" in column_map else "N/A"

                if not guest_name or guest_name.isdigit():
                    continue
                if not check_in or not check_out:
                    continue
                if guest_name in ["S", "M", "T", "W", "T", "F"]:
                    continue

                reservations.append({
                    "Guest Name": guest_name,
                    "Check-in": check_in,
                    "Check-out": check_out,
                    "Nights": nights,
                    "Type": res_type,
                    "Income": income
                })

        return reservations

    except Exception as e:
        return {"error": str(e)}

    finally:
        try:
            driver.quit()
            del driver
        except Exception:
            pass


# 🔥 Flask Route to Trigger Scraper
@app.route("/scrape", methods=["GET"])
def scrape():
    reservations = scrape_reservations()
    return jsonify(reservations)


# ✅ Start Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
