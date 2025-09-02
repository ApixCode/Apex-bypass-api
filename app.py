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


# <-- FINAL, VERIFIED, SCRAPING-BASED FUNCTION FOR JUSTPASTE.IT -->
def get_justpasteit_content(url):
    """
    Scrapes the main JustPaste.it page to extract the raw text content from its HTML.
    This is a robust method that does not rely on hidden endpoints.
    """
    try:
        # Use the provided URL directly, not a modified one.
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        # Parse the page's HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # The paste content is located in a div with the class "article-content"
        content_div = soup.find('div', class_='article-content')

        if content_div:
            # Extract the text, preserving line breaks between paragraphs
            raw_text = content_div.get_text(separator='\n', strip=True)
            return raw_text, None
        else:
            # This error triggers if JustPaste.it changes their website structure
            return None, "Could not find the 'article-content' div on the JustPaste.it page."

    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch content from JustPaste.it: {e}"


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
