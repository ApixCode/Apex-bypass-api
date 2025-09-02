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

# --- CORRECTED Helper function to get content from Pastedrop ---
def get_pastedrop_content(url):
    """
    Fetches raw text from a Pastedrop URL.
    It transforms the standard URL into the 'raw' version by replacing '/paste/' with '/raw/'.
    """
    # Check if the URL is valid and contains '/paste/'
    if "/paste/" not in url:
        return None, "Invalid Pastedrop URL. Must contain '/paste/'."

    # NEW: Replace '/paste/' with '/raw/' to get the correct raw content URL
    raw_url = url.replace("/paste/", "/raw/")
    
    try:
        response = requests.get(raw_url, timeout=5)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastedrop: {e}"

# --- API Endpoint Definition ---
@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    target_url = request.args.get('url')

    if not target_url:
        return jsonify({"error": "URL parameter is missing."}), 400

    content = None
    error_message = None

    # --- Logic to determine which site to scrape ---
    if 'pastebin.com' in target_url:
        content, error_message = get_pastebin_content(target_url)
    # UPDATED: Check for the correct Pastedrop domain
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
