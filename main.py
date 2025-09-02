from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # Import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urlencode, parse_qs
import time

app = Flask(__name__)

# --- Configuration and Setup ---
# Make sure you have chromedriver installed and accessible in your PATH
# Or specify the path to the driver:
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")  # Default: /usr/bin/chromedriver.  Make sure it's correct on Vercel!

# --- Helper Functions ---
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def bypass_linkvertise(url):
    """
    Bypasses a Linkvertise link using Selenium.

    Args:
        url: The Linkvertise URL.

    Returns:
        The final destination URL if successful, or None if there's an error.
    """
    try:
        # --- Selenium Setup ---
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")  # Required for some environments (like Vercel)
        chrome_options.add_argument("--disable-dev-shm-usage")  #  Saves memory
        # Set a user agent.  This helps prevent bot detection.  You can find many user agents online.
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

        # Use Service to manage the ChromeDriver instance.  This is the recommended approach.
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30) # Set a timeout to prevent infinite loading

        # --- Navigate to the Linkvertise Page ---
        driver.get(url)

        # --- Wait for and Click the "Free Access" Button (Modify Selectors if needed) ---
        try:
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "connect-button"))  # Changed selector
            ).click()
            time.sleep(3) # Add a short delay to allow the page to load after the click

        except Exception as e:
            print(f"Error clicking 'Free Access' button: {e}")
            driver.quit()
            return None

        # --- Wait for the Continue Button (Modify Selectors if needed) ---
        try:
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "link-success"))  # Changed selector
            ).click()
            time.sleep(3) # Add a short delay

        except Exception as e:
            print(f"Error clicking 'Continue' button: {e}")
            driver.quit()
            return None

        # --- Get the Final URL ---
        final_url = driver.current_url
        driver.quit()
        return final_url

    except Exception as e:
        print(f"Selenium error: {e}")
        try:
            driver.quit() # Ensure the driver is quit even if there's an error.
        except:
            pass
        return None



@app.route("/api/apex-kazuma/bypass", methods=["GET"])
def bypass_api():
    """
    Bypasses a URL (Pastebin or Linkvertise).

    Args:
        url: The URL to bypass (Pastebin or Linkvertise).

    Returns:
        JSON response with the bypassed content or an error message.
    """
    url = request.args.get("url")

    if not url or not is_valid_url(url):
        return jsonify({"success": False, "error": "Missing or invalid 'url' parameter"}), 400

    # --- Pastebin Bypass (Reusing the previous code) ---
    if "pastebin.com" in url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            content_element = soup.find("textarea", class_="textarea")
            if content_element:
                content = content_element.text.strip()
                return jsonify({"success": True, "result": content})
            else:
                return jsonify({"success": False, "error": "Content not found. Pastebin structure might have changed."}), 404
        except requests.exceptions.RequestException as e:
            return jsonify({"success": False, "error": f"Request failed: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500

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
  
