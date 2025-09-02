# app.py

from flask import Flask, request, jsonify
import requests
import re
from bs4 import BeautifulSoup

# Initialize the Flask application
app = Flask(__name__)


def get_pastebin_content(url):
    """
    Fetches raw text from a Pastebin URL.
    It transforms the standard URL into the 'raw' version.
    """
    # Use a regular expression to find the Paste ID
    match = re.search(r'pastebin\.com/([a-zA-Z0-9]+)', url)
    if not match:
        return None, "Invalid Pastebin URL format."
    
    paste_id = match.group(1)
    # Construct the raw content URL
    raw_url = f"https://pastebin.com/raw/{paste_id}"
    
    try:
        # Make the HTTP request
        response = requests.get(raw_url, timeout=5)
        # Raise an exception if the request was not successful (e.g., 404 Not Found)
        response.raise_for_status() 
        return response.text, None
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, or bad status codes
        return None, f"Could not fetch content from Pastebin: {e}"


def get_pastedrop_content(url):
    """
    Fetches and PARSES a Pastedrop URL to extract the raw text content.
    """
    # Validate the URL structure
    if "/paste/" not in url:
        return None, "Invalid Pastedrop URL. Must contain '/paste/'."

    # Construct the URL that contains the content (as HTML)
    raw_html_url = url.replace("/paste/", "/raw/")
    
    try:
        response = requests.get(raw_html_url, timeout=5)
        response.raise_for_status()

        # Use BeautifulSoup to parse the returned HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the specific div with class="content" which holds the paste text
        content_div = soup.find('div', class_='content')

        if content_div:
            # Extract the text and strip any leading/trailing whitespace
            raw_text = content_div.get_text(strip=True)
            return raw_text, None
        else:
            # This error triggers if Pastedrop changes their website structure
            return None, "Could not find the content container on the Pastedrop page."

    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastedrop: {e}"


@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    """
    The main API endpoint. It takes a URL, determines the service,
    and returns the paste content in the specified JSON format.
    """
    # Get the 'url' parameter from the request (e.g., ?url=...)
    target_url = request.args.get('url')

    if not target_url:
        return jsonify({"error": "URL parameter is missing."}), 400

    content = None
    error_message = None

    # Determine which function to call based on the URL's domain
    if 'pastebin.com' in target_url:
        content, error_message = get_pastebin_content(target_url)
    elif 'paste-drop.com' in target_url:
        content, error_message = get_pastedrop_content(target_url)
    else:
        error_message = "Unsupported URL. Please use a valid Pastebin or paste-drop.com URL."

    # If there was an error during fetching/parsing, return it
    if error_message:
        return jsonify({"error": error_message}), 400

    # If successful, build and return the final JSON response
    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)


# This part allows you to run the app locally for testing
if __name__ == '__main__':
    # Use host='0.0.0.0' to make it accessible from other devices on your network
    app.run(debug=True, host='0.0.0.0', port=5000)
