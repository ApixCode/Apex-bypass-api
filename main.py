from flask import Flask, request, jsonify
import requests
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from urllib.parse import urlparse
import time
import random

app = Flask(__name__)

# --- Configuration and Setup ---
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")

# --- Helper Functions ---
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_paste_id(url):
    """
    Extracts the unique ID from a Pastebin URL.
    Handles both standard and raw URLs.
    Example: 'https://pastebin.com/abcdef12' -> 'abcdef12'
    """
    match = re.search(r'pastebin\.com/(?:raw/)?([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def bypass_pastebin(url):
    """Bypasses a Pastebin link by scraping."""
    paste_id = get_paste_id(url)
    if not paste_id:
        return None  # Invalid Pastebin URL format

    raw_url = f"https://pastebin.com/raw/{paste_id}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(raw_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text

    except requests.exceptions.HTTPError as http_err:
        print(f"Pastebin HTTP error: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Pastebin Request error: {req_err}")
        return None
    except Exception as e:
        print(f"Pastebin General error: {e}")
        return None

def bypass_linkvertise(url):
    """Bypasses a Linkvertise link using Selenium."""
    try:
        # --- Selenium Setup ---
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  # REPLACE WITH A CURRENT USER AGENT

        # Use Service to manage the ChromeDriver instance.
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30) # Prevent infinite loading

        # --- Navigate to the Linkvertise Page ---
        driver.get(url)
        time.sleep(random.uniform(1, 3)) # Add a short delay after page load

        # --- Click the "Free Access" Button (Inspect and Update Selector) ---
        try:
            # **CRITICAL:** Inspect the HTML of the Linkvertise page and find the correct element. The ID or other selector might be different.
            # Example: WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "some-free-access-button"))).click()
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "connect-button"))).click() # UPDATE THIS!
            time.sleep(random.uniform(2, 4)) # Add a short delay after the click

        except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f"Error clicking 'Free Access' button: {e}")
            driver.save_screenshot("free_access_error.png")  # Save a screenshot for debugging
            driver.quit()
            return None
        except Exception as e:
            print(f"Unexpected error clicking 'Free Access': {e}")
            driver.save_screenshot("free_access_unexpected_error.png")
            driver.quit()
            return None

        # --- Click the "Continue" Button (Inspect and Update Selector) ---
        try:
            # **CRITICAL:** Inspect the HTML. The ID or other selector will likely be different.
            # Example: WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "another-continue-button"))).click()
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "link-success"))).click()  # UPDATE THIS!
            time.sleep(random.uniform(2, 4)) # Add a short delay

        except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f"Error clicking 'Continue' button: {e}")
            driver.save_screenshot("continue_error.png")
            driver.quit()
            return None
        except Exception as e:
            print(f"Unexpected error clicking 'Continue': {e}")
            driver.save_screenshot("continue_unexpected_error.png")
            driver.quit()
            return None

        # --- Get the Final URL ---
        final_url = driver.current_url
        driver.quit()
        return final_url

    except Exception as e:
        print(f"Selenium error: {e}")
        try:
            driver.save_screenshot("selenium_error.png")
            driver.quit()
        except:
            pass
        return None


@app.route("/api/apex-kazuma/bypass", methods=["GET"])
def bypass_api():
    """Bypasses a URL (Pastebin or Linkvertise)."""
    url = request.args.get("url")

    if not url or not is_valid_url(url):
        return jsonify({"success": False, "error": "Missing or invalid 'url' parameter"}), 400

    # --- Pastebin Bypass ---
    if "pastebin.com" in url:
        content = bypass_pastebin(url)
        if content:
            return jsonify({"success": True, "result": content})
        else:
            return jsonify({"success": False, "error": "Failed to bypass Pastebin"}), 404

    # --- Linkvertise Bypass ---
    elif "linkvertise.com" in url:
        final_url = bypass_linkvertise(url)
        if final_url:
            return jsonify({"success": True, "result": final_url})
        else:
            return jsonify({"success": False, "error": "Failed to bypass Linkvertise."})

    # --- Unsupported URL ---
    else:
        return jsonify({"success": False, "error": "Unsupported URL"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
    
