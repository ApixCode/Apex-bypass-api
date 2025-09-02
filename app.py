# app.py

from flask import Flask, request, jsonify
import requests
import re

# Initialize the Flask application
app = Flask(__name__)

# --- Helper function to get content from Pastebin ---
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
        response = requests.get(raw_url, timeout=5)
        # Raise an exception if the request was not successful (e.g., 404 Not Found)
        response.raise_for_status() 
        return response.text, None
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, or bad status codes
        return None, f"Could not fetch content from Pastebin: {e}"

# --- Helper function to get content from Pastedrop ---
def get_pastedrop_content(url):
    """
    Fetches raw text from a Pastedrop URL.
    Pastedrop serves raw content directly, so we just fetch the URL.
    """
    try:
        # Pastedrop URLs often need '/raw' appended for direct text
        if not url.endswith('/raw'):
            url += '/raw'
            
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastedrop: {e}"

# --- API Endpoint Definition ---
@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    # Get the 'url' parameter from the request query string (e.g., ?url=...)
    target_url = request.args.get('url')

    # --- Input Validation ---
    if not target_url:
        return jsonify({"error": "URL parameter is missing."}), 400

    content = None
    error_message = None

    # --- Logic to determine which site to scrape ---
    if 'pastebin.com' in target_url:
        content, error_message = get_pastebin_content(target_url)
    elif 'pastedrop.net' in target_url: # Note: Pastedrop often uses .net
        content, error_message = get_pastedrop_content(target_url)
    else:
        error_message = "Unsupported URL. Please use a valid Pastebin or Pastedrop URL."

    # --- Response Generation ---
    if error_message:
        return jsonify({"error": error_message}), 400

    # If successful, return the data in the desired format
    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)

# --- Run the Flask Application ---
if __name__ == '__main__':
    # Runs the app on localhost, port 5000
    # Use host='0.0.0.0' to make it accessible from your network
    app.run(debug=True, host='0.0.0.0', port=5000)
