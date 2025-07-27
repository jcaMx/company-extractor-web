
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
import time

# Selenium imports
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available - using requests only")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

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

# === Selenium Setup ===
def setup_driver():
    """Create and configure Chrome driver for both local and Render"""
    if not SELENIUM_AVAILABLE:
        return None
        
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional options for Render
        if os.environ.get('RENDER'):
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')  # Optional: disable JS for faster loading
        
        driver = uc.Chrome(options=options)
        
        # Remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

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

# === Selenium Scraping Functions ===
def scrape_page_text_selenium(url):
    """Scrape page content using Selenium"""
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            return ""
        
        logger.info(f"Scraping with Selenium: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Remove script and style elements
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        logger.info(f"Successfully scraped {url} with Selenium")
        return text
        
    except Exception as e:
        logger.error(f"Failed to scrape {url} with Selenium: {e}")
        return ""
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def discover_key_pages_selenium(company_url, keyword_list=TARGET_KEYWORDS):
    """Discover pages using Selenium instead of requests"""
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            return {"error": "Failed to setup Chrome driver"}
        
        logger.info(f"Discovering pages with Selenium: {company_url}")
        driver.get(company_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
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

        logger.info("Discovered key pages with Selenium:")
        logger.info(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        return {"error": f"Failed to retrieve homepage: {e}"}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def summarize_discovered_pages_selenium(discovery_result):
    """Summarize pages using Selenium scraping"""
    summaries = {}
    for label, url in discovery_result.get("pages_to_scrape", {}).items():
        logger.info(f"Summarizing {label.title()} with Selenium: {url}")
        
        # Add delay between requests
        time.sleep(3)
        
        text = scrape_page_text_selenium(url)
        if text:
            try:
                response = summary_chain.invoke({"text": text[:4000]})
                summary_text = response.content if hasattr(response, 'content') else str(response)
                summaries[label] = {"url": url, "summary": summary_text}
                logger.info(f"Successfully summarized {label}")
            except Exception as e:
                logger.error(f"Failed to summarize {url}: {e}")
    return {"company": discovery_result["company"], "summaries": summaries}

# === Original Requests Functions ===
def discover_key_pages(company_url, keyword_list=TARGET_KEYWORDS):
    try:
        response = requests.get(company_url, headers=HEADERS, timeout=10)
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

def scrape_page_text(url):
    try:
        time.sleep(1.5)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ""

def summarize_discovered_pages(discovery_result):
    summaries = {}
    for label, url in discovery_result.get("pages_to_scrape", {}).items():
        logger.info(f"Summarizing {label.title()}: {url}")
        
        # sleep for 2 seconds to avoid rate limiting
        time.sleep(2)
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

# === Main Function with Smart Fallback ===
def extract_company_info(company_url: str):
    """Main function with smart fallback between Selenium and requests"""
    
    # Try Selenium first if available
    if SELENIUM_AVAILABLE:
        logger.info("Attempting to use Selenium for scraping...")
        try:
            discovery = discover_key_pages_selenium(company_url)
            if "error" in discovery:
                logger.warning(f"Selenium discovery failed: {discovery['error']}, falling back to requests")
                # Fall back to requests
                discovery = discover_key_pages(company_url)
                if "error" in discovery:
                    return {"error": discovery["error"]}
                summary = summarize_discovered_pages(discovery)
                return summary
            else:
                # Selenium discovery succeeded, use Selenium for summarization
                summary = summarize_discovered_pages_selenium(discovery)
                return summary
        except Exception as e:
            logger.error(f"Selenium failed completely: {e}, falling back to requests")
            # Fall back to requests
            discovery = discover_key_pages(company_url)
            if "error" in discovery:
                return {"error": discovery["error"]}
            summary = summarize_discovered_pages(discovery)
            return summary
    else:
        # Selenium not available, use requests
        logger.info("Selenium not available, using requests")
        discovery = discover_key_pages(company_url)
        if "error" in discovery:
            return {"error": discovery["error"]}
        summary = summarize_discovered_pages(discovery)
        return summary

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
