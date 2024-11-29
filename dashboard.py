import streamlit as st
import pandas as pd
import gspread
import requests
import json
import time
import random
import re
import os
from bs4 import BeautifulSoup
from langdetect import detect
from googletrans import Translator
from ratelimit import limits, sleep_and_retry
from oauth2client.service_account import ServiceAccountCredentials

LLM_API_URL = "<<your-api-endpoint-url-here>>"
LLM_API_KEY = "<<your-api-key-here>>"

def extract_information_using_llm(prompts):
    responses = []
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    for prompt in prompts:
        # Extract the Entity and convert Prompt from the JSON-like structure to string
        entity = prompt.get("Entity", "Unknown")
        prompt_text = str(prompt.get("ExtractedText", "No prompt text provided"))

        # Formatting payload for the chat API
        payload = {
            "model": "command-r",
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
        }

        try:
            response = requests.post(LLM_API_URL, headers=headers, json=payload)

            if response.status_code == 200:
                response_json = response.json()

                if "generations" in response_json:
                    if response_json["generations"][0]["text"]:
                        extracted_info = response_json["generations"][0]["text"]
                    else:
                        extracted_info = "LLM did not generate any text"
                else:
                    extracted_info = "Expected format not received from LLM"
            else:
                extracted_info = f"Request failed with status {response.status_code}"
        except Exception as e:
            print(f"Error: {str(e)}")
            extracted_info = "Exception occurred"

        # Append the extracted details to the responses
        responses.append({
            "Entity": entity,
            "Prompt": prompt_text,
            "Extracted Info": extracted_info
        })

        time.sleep(1)  # Rate limiting to avoid hitting API limits

    return responses

SCRAPER_API_URL = "<<your-api-endpoint-url-here>>"
SCRAPER_API_KEY = "<<your-api-key-here>>"

# Function to extract text from raw HTML using BeautifulSoup
def extract_text_from_html(raw_html):
    try:
        soup = BeautifulSoup(raw_html, "html.parser")

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Remove images, audio, and video elements
        for media_tag in soup.find_all(["img", "audio", "video"]):
            media_tag.decompose()

        # Remove all links
        for link in soup.find_all("a"):
            link.decompose()

        # Remove headers (h1, h2, h3, h4, h5, h6)
        for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            header.decompose()

        # Remove additional undesired tags if needed
        for unwanted_tag in soup.find_all(["footer", "nav"]):
            unwanted_tag.decompose()

        # Extract remaining main text
        extracted_text = soup.get_text(separator="\n", strip=True)
        return extracted_text
    except Exception as e:
        return f"Error occurred during extraction: {e}"

translator = Translator()

def clean_text(raw_text):
    # Split text by newlines
    lines = raw_text.split("\n")

    # Join lines with spaces
    text = " ".join(lines)

    # Replace multiple spaces with a single space
    text = " ".join(lines).replace("\n", " ")

    # Detect language and translate if needed
    detected_lang = detect(text)
    if detected_lang != 'en':
        try:
            text = translator.translate(text, src=detected_lang, dest='en').text
        except Exception as e:
            print(f"Translation failed: {e}")

    # Define patterns to exclude
    exclude_patterns = [
        r"Google Search|Search the web|Press|More|About [0-9,]+ results|\(.*?seconds\)|Feedback|People also ask|People also search for|\d+$|Google apps|https?://\S+|PDF|^$|Page\d+\ of\d+",
    ]
    exclude_regex = re.compile(r"|".join(exclude_patterns))

    # Remove unwanted patterns
    cleaned_text = exclude_regex.sub('', text).strip()

    # Ensure single spaces between words
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text

def process_html_and_clean_text(raw_html):
    # Extract text from HTML
    extracted_text = extract_text_from_html(raw_html)
    
    # Clean the extracted text
    cleaned_text = clean_text(extracted_text)
    
    return cleaned_text

@sleep_and_retry
@limits(calls=10, period=60)
# Function to perform a web search for a query
def perform_web_search(query, scraper_api_key, scraper_api_url):
    params = {
        "api_key": scraper_api_key,
        "url": f"https://www.google.com/search?q={query}"
    }
    timeout = 30  # Timeout duration of 30 seconds
    try:
        response = requests.get(scraper_api_url, params=params, timeout=timeout)
        response.raise_for_status()
        raw_html = response.text  # Raw HTML content of the search page
        return raw_html
    except requests.exceptions.RequestException as e:
        print(f"Error during web search: {e}")
        return None

# Perform web search for each entity in the main column and extract meaningful text
def execute_web_search(data, main_column, query_template, scraper_api_key, scraper_api_url, num_entities=5):
    results = []

    # Sample 'num_entities' random entities from the column
    random_entities = random.sample(data[main_column].tolist(), num_entities)

    # Process each entity in the selected column
    for entity in random_entities:
        # Construct the query using the template
        query = query_template.replace(f"{{{main_column}}}", str(entity))
        print(f"Performing search for: {query}")

        # Perform the search
        raw_html = perform_web_search(query, SCRAPER_API_KEY, SCRAPER_API_URL)

        if raw_html:
            # Pass the raw HTML to the function to process and clean text
            cleaned_text = process_html_and_clean_text(raw_html)

            # Store the result
            results.append({
                "Entity": entity,
                "Query": query,
                "ExtractedText": cleaned_text  # The meaningful extracted content
            })

            # Delay to handle rate limiting
            time.sleep(2)  # Adjust delay as needed for API rate limits

    # Return results as JSON
    return results

# Google Sheets API Setup
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client

# Load data from Google Sheets
def load_google_sheet(sheet_url):
    client = authenticate_google_sheets()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# File upload or Google Sheets input
def upload_or_connect_data():
    st.title("File Upload & Google Sheets Connection")

    data = None
    st.subheader("Upload a CSV File or Connect to a Google Sheet")

    # File upload
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.success("CSV file uploaded successfully.")

    # Google Sheets connection
    st.write("OR")
    google_sheet_url = st.text_input("Enter Google Sheets URL")
    if google_sheet_url:
        try:
            data = load_google_sheet(google_sheet_url)
            st.success("Google Sheet connected successfully.")
        except Exception as e:
            st.error(f"Error connecting to Google Sheets: {e}")

    if data is not None:
        st.subheader("Preview of Uploaded Data")
        st.write(data.head())
        return data
    return None

# Main column selection
def select_main_column(data):
    st.subheader("Select the Main Column")
    if data is not None:
        columns = data.columns.tolist()
        main_column = st.selectbox("Select the main column (e.g., Company Name)", columns)
        return main_column
    return None

# Dynamic query input
def dynamic_query_input(main_column):
    st.subheader("Define Your Query Template")
    if main_column:
        st.info(f"Use `{{{main_column}}}` as a placeholder for dynamic queries.")
        query_template = st.text_area("Enter your query template (e.g., 'Get the email of {Company Name}')")
        return query_template
    return None

# Main Streamlit app
def main():
    st.sidebar.title("Dashboard Options")
    st.sidebar.info("Switch between tabs for different functionalities.")

    # Dashboard Tabs
    option = st.sidebar.selectbox("Choose an Option", ["File Upload", "Dynamic Query Input"])

    if option == "File Upload":
        data = upload_or_connect_data()
        if data is not None:
            select_main_column(data)
    elif option == "Dynamic Query Input":
        st.write("First, upload data via the File Upload tab.")
        data = upload_or_connect_data()
        if data is not None:
            main_column = select_main_column(data)
            query_template = dynamic_query_input(main_column)

            if main_column and query_template:
                if st.button("Execute Queries"):
                    results = execute_web_search(data, main_column, query_template, SCRAPER_API_KEY, SCRAPER_API_URL)

                    for result in results:
                        entity = result.get("Entity", "Unknown Entity")
                        raw_html = result.get("ExtractedText", "No text extracted")
                        cleaned_text = process_html_and_clean_text(raw_html)

                    # Send the results to LLM for information extraction
                    extracted_data = extract_information_using_llm(results)
                    st.subheader("Extracted Information")
                    st.table(extracted_data)

if __name__ == "__main__":
    main()
