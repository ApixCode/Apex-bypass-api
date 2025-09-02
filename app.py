# app.py

from flask import Flask, request, jsonify
import requests
import re
from bs4 import BeautifulSoup # <-- IMPORT BEAUTIFUL SOUP

# Initialize the Flask application
app = Flask(__name__)

# --- Helper function to get content from Pastebin ---
# (This function remains the same)
def get_pastebin_content(url):
    """
    Fetches raw text from a Pastebin URL.
    It transforms the standard URL into the 'raw' version.
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

# --- FULLY CORRECTED Helper function to get content from Pastedrop ---
def get_pastedrop_content(url):
    """
    Fetches and PARSES a Pastedrop URL to extract the raw text content.
    """
    if "/paste/" not in url:
        return None, "Invalid Pastedrop URL. Must contain '/paste/'."

    raw_url = url.replace("/paste/", "/raw/")
    
    try:
        response = requests.get(raw_url, timeout=5)
        response.raise_for_status()

        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the specific div with class="content" that holds the text
        content_div = soup.find('div', class_='content')

        if content_div:
            # Extract the text and strip any leading/trailing whitespace
            raw_text = content_div.get_text(strip=True)
            return raw_text, None
        else:
            # If we can't find that specific div, the page structure might have changed
            return None, "Could not find the content container on the Pastedrop page."

    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastedrop: {e}"

# --- API Endpoint Definition ---
# (This function remains the same)
@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    target_url = request.args.get('url')

    if not target_url:
        return jsonify({"error": "URL parameter is missing."}), 400

    content = None
    error_message = None

    if 'pastebin.com' in target_url:
        content, error_message = get_pastebin_content(target_url)
    elif 'paste-drop.com' in target_url:
        content, error_message = get_pastedrop_content(target_url)
    else:
        error_message = "Unsupported URL. Please use a valid Pastebin or paste-drop.com URL."

    if error_message:
        return jsonify({"error": error_message}), 400

    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)

# --- Run the Flask Application ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
