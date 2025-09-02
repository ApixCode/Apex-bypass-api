# app.py

from flask import Flask, request, jsonify
import requests
import re
from bs4 import BeautifulSoup

# Initialize the Flask application
app = Flask(__name__)


def get_pastebin_content(url):
    """
    Fetches raw text from a Pastebin URL via its /raw endpoint.
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
    Scrapes the Pastedrop page to extract the raw text content.
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


def get_pastefy_content(url):
    """
    Fetches raw text from a Pastefy URL via its /raw endpoint.
    """
    parts = url.split('?')
    base_url = parts[0]
    query_string = f"?{parts[1]}" if len(parts) > 1 else ""

    if '/raw' in base_url:
        raw_url = url
    else:
        raw_url = base_url.rstrip('/') + '/raw' + query_string

    try:
        response = requests.get(raw_url, timeout=5)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from Pastefy: {e}"


def get_justpasteit_content(url):
    """
    Scrapes the JustPaste.it page by parsing the simplified HTML served to scripts.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content_paragraph = soup.find('p')

        if content_paragraph:
            raw_text = content_paragraph.get_text(strip=True)
            return raw_text, None
        else:
            return None, "Could not find the main '<p>' tag on the simplified JustPaste.it page."
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from JustPaste.it: {e}"


# <-- FINAL, VERIFIED FUNCTION FOR CTXT.IO -->
def get_ctxt_content(url):
    """
    Fetches content from ctxt.io by using its official JSON API.
    This version correctly captures the full path as the paste identifier.
    """
    # THIS IS THE FIX: The regex now captures the ENTIRE path after the domain.
    match = re.search(r'ctxt\.io/(.+)', url)
    if not match:
        return None, "Invalid ctxt.io URL format. Could not find paste ID."
    
    # paste_id will now correctly be "2/AAD4_LFXEg"
    paste_id = match.group(1).rstrip('/')
    
    # Construct the correct API URL
    api_url = f"https://ctxt.io/api/v1/paste/{paste_id}"

    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if 'content' in data:
            return data['content'], None
        else:
            return None, "API response from ctxt.io is valid but did not contain a 'content' key."

    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from ctxt.io API: {e}"
    except ValueError:
        return None, "Failed to parse JSON response from ctxt.io API."


@app.route('/api/apex', methods=['GET'])
def get_paste_components():
    """
    The main API endpoint.
    """
    target_url = request.args.get('url')

    if not target_url:
        return jsonify({"error": "URL parameter is missing."}), 400

    content = None
    error_message = None

    if 'pastebin.com' in target_url:
        content, error_message = get_pastebin_content(target_url)
    elif 'paste-drop.com' in target_url:
        content, error_message = get_pastedrop_content(target_url)
    elif 'pastefy.app' in target_url:
        content, error_message = get_pastefy_content(target_url)
    elif 'justpaste.it' in target_url:
        content, error_message = get_justpasteit_content(target_url)
    elif 'ctxt.io' in target_url:
        content, error_message = get_ctxt_content(target_url)
    else:
        error_message = "Unsupported URL. Please use a valid Pastebin, paste-drop.com, Pastefy, JustPaste.it, or ctxt.io URL."

    if error_message:
        return jsonify({"error": error_message}), 400

    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
