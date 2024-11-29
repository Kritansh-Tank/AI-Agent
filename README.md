# AI-Agent

Project Overview:

You will create an AI agent that reads through a dataset (CSV or Google Sheets) and performs a web search to retrieve specific information for each entity in a chosen column. The AI will leverage an LLM to parse web results based on the user's query and format the extracted data in a structured output. The project includes building a simple dashboard where users can upload a file, define search queries, and view/download the results. 

Key Features & Requirements -
Here’s a breakdown of each feature you’ll be building, along with details on the expected outcome  for each -

1. Dashboard for File Upload and Google Sheets Connection 
        a. Goal:  Allow users to upload a CSV file or connect to a Google Sheet directly for data input. 
	b. Expected Outcome:  
                 (i) Users can upload a CSV file with a simple "Browse" button or enter Google Sheet credentials to link to a sheet. 
                 (ii) Display the available columns from the CSV or Google Sheet, allowing the user to select the main column (e.g., company names). 
                 (iii) Show a preview of the uploaded data. 
        c. Technical Details : Integrate with the Google Sheets API for real-time Google Sheet access, allowing  users to authenticate and pull data from their sheets. 

2. Dynamic Query Input with Prompt Template 
	a. Goal:  Allow users to specify the type of information they want to retrieve for each entity in  the main column. 
	b. Expected Outcome:  
	         (i) A text input box where users can define a custom prompt, such as "Get me the  email address of {company}". 
                 (ii) Ensure users understand they can use placeholders (e.g., {company} )  that will be  dynamically replaced by each entity in the selected column. 

3. Automated Web Search for Information Retrieval 
	a. Goal: Perform web searches for each entity using the custom prompt and gather relevant  web results. 
	b. Expected Outcome: 
	          (i) For each entity in the selected column, your agent should conduct a web search  (e.g., “Get me the email address of {company}”). 
                  (ii) Gather and store search results (e.g., URLs, snippets) for each entity. 
                  (iii) Consider using SerpAPI, ScraperAPI , or other web scraping/search APIs, ensuring proper API usage limits. 
	c. Technical Details: 
	           (i) Implement logic to handle rate limiting and avoid potential blocking. 
                   (ii) Store each entity's results in a structured format, ready for further processing by the  LLM. 

4. Passing Results to an LLM for Parsing and Information Extraction 
	a. Goal:  Use an LLM to extract specific information based on the user-defined prompt and  web results. 
	b. Expected Outcome:  
	         (i) Send each entity’s search results to the LLM, along with a backend prompt like “Extract the email address of {company} from the following web results.”. This  prompt could be asked from the user as well. 
                 (ii) Ensure the LLM processes the search results and extracts the requested information (e.g., email, address, etc.) for each entity. 
	c. Technical Details: 
	          (i) Implement LLM integration (e.g., Groq or OpenAI’s GPT API) for processing the data.
                  (ii) Handle any errors gracefully, such as retrying failed queries or notifying the user if data retrieval is unsuccessful. 

5. Displaying and Storing the Extracted Information 
	a. Goal:  Show extracted data in a user-friendly format and provide an option to download the  data. 
	b. Expected Outcome:  
	         (i) Display the extracted data in a table format within the dashboard, organized by entity and extracted information. 
                 (ii) Offer an option to download the results as a CSV or update a connected Google Sheet with the extracted information. 
	c. Technical Details: Provide a “Download CSV” button and an option to update the Google Sheet.  

Technical Stack Suggestions -
Below is a list of recommended technologies: 
●	Dashboard/UI: Streamlit, Flask
●	Data Handling: pandas for CSV files; Google Sheets API for Sheets
●	Search API: SerpAPI, ScraperAPI, or another search service
●	LLM API: Groq or OpenAI’s GPT API
●	Backend: Python
●	Agents: Langchain
