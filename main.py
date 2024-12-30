from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from scrapegraphai.graphs import SmartScraperGraph
import os
import json
from typing import Optional
from datetime import datetime
import asyncio

port = int(os.getenv("PORT", 10000))

app = FastAPI()


# Allow requests from the Next.js app
app.add_middleware(
    CORSMiddleware,
     allow_origins=["*"],  # Update this to match your Next.js app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

job_urls = [
    "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=United%20States&trk=public_jobs_jobs-search-bar_search-submit&redirect=false&position=1&pageNum=0",
    "https://www.ycombinator.com/jobs"
]

class ScrapeResults:
    def __init__(self):
        self.data: Optional[list] = None
        self.is_scraping: bool = False
        self.last_updated: Optional[datetime] = None
    
    def set_results(self, new_results: list):
        self.data = new_results
        self.is_scraping = False
        self.last_updated = datetime.now()
    
    def clear(self):
        self.data = None
        self.is_scraping = False
        self.last_updated = None
    
    def start_scraping(self):
        self.is_scraping = True
        self.data = None

results_manager = ScrapeResults()

def scrape_job_posting(url: str) -> dict:
    graph_config = {
    "llm": {
        "api_key": OPENAI_API_KEY,
        "model": "openai/gpt-4o-mini",
    },
    "verbose": True,
    "headless": True,
    "playwright": {
        "browser_type": "chromium",
        "launch_options": {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process"
            ]
        },
        "context_options": {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    }
}
    
    SCRAPING_PROMPT = """Extract all entry-level software engineering jobs posted within the last week. For each job, return a JSON object with the following fields:
    {
        "job_title": "The title of the job position",
        "company_name": "The name of the hiring company",
        "job_url": "The URL linking to the job posting",
        "location": "The job location in the format 'city, state' (if available)",
        "date_posted": "The posting date of the job",
        "description": "A detailed description of the company and the job, sufficient for generating a tailored cover letter"
    }
    
    If any of the fields are missing or unavailable, leave them empty but include the field in the JSON object."""

    smart_scraper_graph = SmartScraperGraph(
        prompt=SCRAPING_PROMPT,
        source=url,
        config=graph_config
    )
    return smart_scraper_graph.run()




async def scrape_with_retries(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            # Add delay between retries
            if attempt > 0:
                await asyncio.sleep(5 * attempt)
            
            data = await asyncio.to_thread(scrape_job_posting, url)
            return data
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise e
            continue

async def scrape_all_jobs():
    temp_results = []
    for url in job_urls:
        try:
            data = await scrape_with_retries(url)
            temp_results.append({"url": url, "data": data})
        except Exception as e:
            temp_results.append({
                "url": url, 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    results_manager.set_results(temp_results)
    
    # Schedule clearing of results after 5 minutes
    await asyncio.sleep(300)
    results_manager.clear()
@app.get("/scrape")
async def scrape_jobs(background_tasks: BackgroundTasks):
    if results_manager.is_scraping:
        return {"message": "Scraping already in progress. Please check /results endpoint later."}
    
    results_manager.start_scraping()
    background_tasks.add_task(scrape_all_jobs)
    return {"message": "Scraping started. Check the /results endpoint for updates."}

@app.get("/results")
def get_results():
    if results_manager.is_scraping:
        return {"status": "scraping", "message": "Scraping in progress, please check back later"}
    elif results_manager.data is None:
        return {"status": "no_data", "message": "No results available. Try initiating a scrape first."}
    else:
        return {
            "status": "complete",
            "results": results_manager.data,
            "last_updated": results_manager.last_updated
        }