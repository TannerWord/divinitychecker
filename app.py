from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os
import subprocess

app = Flask(__name__)

# ✅ Install Chrome & ChromeDriver if not present
def install_chrome():
    if not os.path.exists("/usr/bin/google-chrome"):
        subprocess.run("curl -o /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb", shell=True, check=True)
        subprocess.run("apt install -y /tmp/chrome.deb", shell=True, check=True)

install_chrome()  # Ensure Chrome is installed


def get_booking_data():
    """Scrapes booking data and returns it as a dictionary"""

    # ✅ Setup Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("--no-sandbox")  # Required for running in Render
    options.add_argument("--disable-dev-shm-usage")  # Prevents memory issues
    options.binary_location = "/usr/bin/google-chrome"  # Explicitly set Chrome binary path

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.cabinsofthesmokymountains.com/pigeon-forge-cabin-rental/Divinity.html/1229")

    # ✅ Wait for the calendar to load
    driver.implicitly_wait(5)

    # ✅ Extract month names dynamically
    current_month = driver.find_element(By.CLASS_NAME, "monthOneTxt").text.split(" - ")[0]
    next_month = driver.find_element(By.CLASS_NAME, "monthTwoTxt").text.split(" - ")[0]

    # ✅ Extract booked dates
    current_month_booked_dates = [
        td.text.strip() for td in driver.find_elements(By.CSS_SELECTOR, "#monthOne .bookedDate")
    ]
    next_month_booked_dates = [
        td.text.strip() for td in driver.find_elements(By.CSS_SELECTOR, "#monthTwo .bookedDate")
    ]

    # ✅ Close the browser
    driver.quit()

    # ✅ Convert dates to integers (if they are numeric)
    current_month_booked_dates = sorted(
        [int(date) for date in current_month_booked_dates if date.isdigit()]
    )
    next_month_booked_dates = sorted(
        [int(date) for date in next_month_booked_dates if date.isdigit()]
    )

    # ✅ Function to calculate booking percentage
    def calculate_booking_percentage(booked_days, total_days):
        booked_count = len(set(booked_days))
        return (booked_count / total_days) * 100

    # ✅ Dictionary for number of days in each month
    month_days = {
        "January": 31, "February": 29, "March": 31, "April": 30,
        "May": 31, "June": 30, "July": 31, "August": 31,
        "September": 30, "October": 31, "November": 30, "December": 31
    }

    # ✅ Get total days in each month
    days_in_current_month = month_days.get(current_month, 30)
    days_in_next_month = month_days.get(next_month, 30)

    # ✅ Format booked dates
    current_month_booked_formatted = [f"{current_month} {day}" for day in current_month_booked_dates]
    next_month_booked_formatted = [f"{next_month} {day}" for day in next_month_booked_dates]

    # ✅ Calculate booking percentages
    percent_current_month = calculate_booking_percentage(current_month_booked_dates, days_in_current_month)
    percent_next_month = calculate_booking_percentage(next_month_booked_dates, days_in_next_month)

    # ✅ Return the booking data
    return {
        "current_month": {
            "name": current_month,
            "booked_dates": current_month_booked_formatted,
            "booking_percentage": round(percent_current_month, 2)
        },
        "next_month": {
            "name": next_month,
            "booked_dates": next_month_booked_formatted,
            "booking_percentage": round(percent_next_month, 2)
        }
    }

# ✅ Webhook Endpoint for n8n
@app.route('/run_booking_check', methods=['POST'])
def run_script():
    """Runs the Selenium script when triggered by a webhook"""
    try:
        data = get_booking_data()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ Start the Flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)









