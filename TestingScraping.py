import requests
from bs4 import BeautifulSoup

def get_abstract_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": "MyApp (myemail@example.com)"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("abstract", "No abstract found")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {doi}: {e}")
        return None
    
def get_abstract_from_crossref(doi):
    """ Retrieve abstract using the CrossRef API. """
    if not doi:
        return "DOI not found."

    api_url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": "DailyArticleApp (your_email@example.com)"}  # Change to your email

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("abstract", "No abstract available.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching DOI {doi}: {e}")
        return "Error retrieving abstract."
