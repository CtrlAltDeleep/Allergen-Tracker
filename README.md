# Allergen-Tracker
Personal project to help my sister compare diet, medication and other factors simultaneously to better understand allergy and eczema triggers.

**To use:**
- Ensure to update the *'privatekeys.json'* file with your unique API keys and Google sheet IDs (available in spreadsheet URL)
- Visit https://console.developers.google.com/ to create a project and an OAuth 2.0 Client ID for that project. Download the credentials.json file to the project folder.
- On the first run, a browser pop-up will prompt you to log into your Google account and allow access to the spreadsheets. 
*(Note: Some browsers may suspect Quickstart to be malicious - continue anyway)*
- A token.pickle file will be created. Do not modify/delete this to avoid the need to log in again.

**Purpose of Spreadsheets:** 
- Database: Google sheet which is user accessible,
- DATA_Compile: Google Sheet for dumping and storing data between runs, to minimise API requests and runtime

Deleep