# Company Information Extractor

A **React + Flask** web application that extracts and summarizes key information from company websites using LangChain and GPT-4.

## Features
- **Frontend**: Modern React interface with responsive design  
- **Backend**: Flask API for processing and AI summarization  
- **Core Functionality**:
  - Discovers important pages (About, Team, Products, etc.)
  - Scrapes and cleans page content
  - Generates AI-powered summaries using GPT-4
- **User Experience**:
  - Real-time loading states
  - Error handling with user-friendly messages
  - Clean, categorized output

## Prerequisites
### Backend (Flask)
- Python 3.8+
- OpenAI API key (in `.env`)
- Chrome browser (for Selenium, if needed)

### Frontend (React)
- Node.js 16+
- npm/yarn

## Architecture
```mermaid
flowchart TD
    A[React Frontend] -->|POST URL| B[Flask API]
    B --> C[Company Extractor]
    C --> D[LangChain/GPT-4]
    C --> E[BeautifulSoup]
    D --> B
    E --> B
    B -->|JSON Results| A

sequenceDiagram
    participant User
    participant React as React Frontend
    participant Flask
    participant Extractor
    
    User->>React: Enters URL
    React->>Flask: POST /api/extract {url}
    Flask->>Extractor: extract_company_info(url)
    Extractor->>Extractor: Discover pages (BeautifulSoup)
    Extractor->>Extractor: Scrape content
    Extractor->>Extractor: Generate summaries (LangChain/GPT-4)
    Extractor->>Flask: Return JSON
    Flask->>React: Return {company, summaries}
    React->>User: Display formatted results
```


# How to Run

## Backend (Flask)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python app.py
```

## Frontend (React)
```bash
cd frontend
npm install
npm start
```
Access at: [http://localhost:3000](http://localhost:3000)

## Key Technologies
| Component       | Technology Stack       |
|----------------|------------------------|
| **Frontend**   | React, Axios, CSS      |
| **Backend**    | Flask, Flask-CORS      |
| **Scraping**   | BeautifulSoup, Requests|
| **AI**         | LangChain, OpenAI GPT-4|

## Troubleshooting
**React shows default page**:
- Verify `src/App.js` replaces all default content  
- Check browser console for errors (`F12`)

**CORS errors**:
- Ensure `flask-cors` is installed and configured  
- Confirm backend runs on port 5000

**Missing summaries**:
- Check if target website blocks scraping  
- Verify OpenAI API key in `.env`

---

### Key Changes from Original:
1. **Dual setup instructions** for React + Flask  
2. **Clear separation** of frontend/backend components  
3. **Updated diagrams** showing full-stack flow  
4. **Simplified troubleshooting** for common issues  
5. **Modern tech stack** documentation


