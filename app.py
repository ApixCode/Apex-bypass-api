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


def get_pastefy_content(url):
    """
    Fetches raw text from a Pastefy URL, preserving necessary query parameters like 'hash'.
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


# <-- FINAL, VERIFIED FUNCTION FOR JUSTPASTE.IT -->
def get_justpasteit_content(url):
    """
    Fetches raw text from a JustPaste.it URL using the correct /download/{id} path.
    """
    match = re.search(r'justpaste\.it/([a-zA-Z0-9]+)', url)
    if not match:
        return None, "Invalid JustPaste.it URL format. Could not find paste ID."
    
    paste_id = match.group(1)

    # THIS IS THE FIX: The correct endpoint is /download/, not /txt/
    raw_url = f"https://justpaste.it/download/{paste_id}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(raw_url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from JustPaste.it: {e}"


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
    elif 'pastefy.app' in target_url:
        content, error_message = get_pastefy_content(target_url)
    elif 'justpaste.it' in target_url:
        content, error_message = get_justpasteit_content(target_url)
    else:
        error_message = "Unsupported URL. Please use a valid Pastebin, paste-drop.com, Pastefy, or JustPaste.it URL."

    if error_message:
        return jsonify({"error": error_message}), 400

    response_data = {
        "result": content,
        "server": "https://discord.gg/HFKek35x58"
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
