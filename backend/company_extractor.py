
import os
import json
import re
import requests
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


# === Environment Setup ===
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "OPENAI_API_KEY not set"

# === Constants ===
TARGET_KEYWORDS = [
    "about", "team", "mission", "values", "services", "solutions", "products",
    "industries", "clients", "case-studies", "projects", "blog", "insights",
    "resources", "news", "careers", "jobs", "contact"
]

# === Logger Setup ===
def setup_logger():
    logger = logging.getLogger("CompanyExtractor")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(ch)
    return logger

logger = setup_logger()

# === LangChain Setup ===
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=OPENAI_API_KEY)
summary_prompt = PromptTemplate.from_template("""
You are an analyst reviewing company web content.
Summarize the following page text. Focus on:
- Operational details (departments, workflows, key processes)
- Unique value propositions
- Opportunities for using AI (automation, content generation, decision support)

Text:
{text}

Structured summary:
""")
summary_chain = summary_prompt | llm

# === Discovery Functions ===
def discover_key_pages(company_url, keyword_list=TARGET_KEYWORDS):
    try:
        response = requests.get(company_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to retrieve homepage: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")
    all_links = [urljoin(company_url, a['href']) for a in soup.find_all('a', href=True)]
    internal_links = [link for link in all_links if urlparse(link).netloc == urlparse(company_url).netloc]
    unique_links = list(set(internal_links))

    def score_link(url):
        return sum(kw in url.lower() for kw in keyword_list)

    scored_links = [(url, score_link(url)) for url in unique_links]
    relevant_links = {kw: url for url, score in scored_links if score > 0 for kw in keyword_list if kw in url.lower()}

    result = {
        "company": urlparse(company_url).netloc,
        "root_url": company_url,
        "pages_to_scrape": relevant_links
    }

    logger.info("Discovered key pages:")
    logger.info(json.dumps(result, indent=2))
    return result

# === Scraping ===
def scrape_page_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ""

# === Summarization ===
def summarize_discovered_pages(discovery_result):
    summaries = {}
    for label, url in discovery_result.get("pages_to_scrape", {}).items():
        logger.info(f"Summarizing {label.title()}: {url}")
        text = scrape_page_text(url)
        if text:
            try:
                response = summary_chain.invoke({"text": text[:4000]})
                # Extract the text content from AIMessage
                summary_text = response.content if hasattr(response, 'content') else str(response)
                summaries[label] = {"url": url, "summary": summary_text}
            except Exception as e:
                logger.error(f"Failed to summarize {url}: {e}")
    return {"company": discovery_result["company"], "summaries": summaries}

# === File Helpers ===
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {path}")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compile_summaries_to_string(summary_json):
    summaries = summary_json.get("summaries", {})
    combined = []
    for section, content in summaries.items():
        summary_text = content.get("summary", "").strip()
        if summary_text:
            combined.append(f"[{section.title()} Page]\n{summary_text}\n")
    return "\n".join(combined)

def run_pipeline_for_url(company_url):
    discovery = discover_key_pages(company_url)
    if "error" in discovery:
        return {"error": discovery["error"]}

    summaries = summarize_discovered_pages(discovery)
    return summaries



# === Main Extractor Function ===
def extract_company_info(company_url: str):
    discovery = discover_key_pages(company_url)
    if "error" in discovery:
        return {"error": discovery["error"]}
    summary = summarize_discovered_pages(discovery)
    return summary

# # === Entry Point ===
# if __name__ == "__main__":
#     url = "https://www.accenture.com"
#     result = extract_company_info(url)
#     save_json(result, "company_summary.json")
#     print(compile_summaries_to_string(result))
