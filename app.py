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
    """
    match = re.search(r'pastebin\.com/([a-zA-Z0-9]+)', url)
    if not match:
        return None, "Invalid Pastebin URL format."
    
    paste_id = match.group(1)
    raw_url = f"https://pastebin.com/raw/{paste_id}"
    
    try:
        response = requests.get(raw_url, timeout=5)
        response.raise_for_status() 
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastebin: {e}"


def get_pastedrop_content(url):
    """
    Fetches and PARSES a Pastedrop URL to extract the raw text content.
    """
    if "/paste/" not in url:
        return None, "Invalid Pastedrop URL. Must contain '/paste/'."

    raw_html_url = url.replace("/paste/", "/raw/")
    
    try:
        response = requests.get(raw_html_url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', class_='content')

        if content_div:
            raw_text = content_div.get_text(strip=True)
            return raw_text, None
        else:
            return None, "Could not find the content container on the Pastedrop page."
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastedrop: {e}"


# <-- NEW FUNCTION FOR PASTEFTY -->
def get_pastefy_content(url):
    """
    Fetches raw text from a Pastefy URL.
    """
    # Regex to find the Paste ID from various Pastefy URL formats
    match = re.search(r'pastefy\.app/([a-zA-Z0-9]+)', url)
    if not match:
        return None, "Invalid Pastefy URL format."

    paste_id = match.group(1)
    # Construct the raw content URL, which is simply /{paste_id}/raw
    raw_url = f"https://pastefy.app/{paste_id}/raw"

    try:
        response = requests.get(raw_url, timeout=5)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastefy: {e}"


@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    """
    The main API endpoint. It takes a URL, determines the service,
    and returns the paste content in the specified JSON format.
    """
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
    # <-- ADDED PASTEFTY SUPPORT -->
    elif 'pastefy.app' in target_url:
        content, error_message = get_pastefy_content(target_url)
    else:
        # <-- UPDATED ERROR MESSAGE -->
        error_message = "Unsupported URL. Please use a valid Pastebin, paste-drop.com, or Pastefy URL."

    if error_message:
        return jsonify({"error": error_message}), 400

    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
