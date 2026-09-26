import os
import csv
import asyncio
import aiohttp
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = 'https://ordinances.davaocity.gov.ph/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# Guardrails to respect fragile hosting
MAX_CONCURRENT_DOWNLOADS = 3  # Never set this excessively high on municipal servers
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10)
PAGE_DELAY = 1.0              # Delay between pagination requests (seconds)
DOWNLOAD_DELAY = 0.5          # Delay between starting each PDF download (seconds)

semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)


async def fetch_page(session, url):
    """Fetch HTML content with timeout and error handling."""
    try:
        async with session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT) as response:
            if response.status == 200:
                return await response.text()
            print(f"[Warning] HTTP {response.status} when fetching {url}")
            return None
    except Exception as e:
        print(f"[Error] Failed to fetch {url}: {e}")
        return None


async def harvest_catalog(session, max_pages=5):
    """Phase 1: Sequential harvesting of metadata and PDF URLs."""
    ordinances = []
    current_url = BASE_URL
    page_count = 0

    while current_url and (max_pages is None or page_count < max_pages):
        page_count += 1
        print(f"[Catalog] Crawling Page {page_count}: {current_url}")

        html = await fetch_page(session, current_url)
        if not html:
            break

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if not table:
            print("[Warning] No table found on page. Stopping catalog crawl.")
            break

        rows = table.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 3:
                ord_no = cols[1].get_text(strip=True)
                description = cols[2].get_text(strip=True)
                
                pdf_tag = row.find('a', href=True)
                pdf_url = urljoin(current_url, pdf_tag['href']) if pdf_tag else None

                ordinances.append({
                    'ordinance_no': ord_no,
                    'description': description,
                    'pdf_url': pdf_url
                })

        # Locate 'Next' link using rel attribute or text fallback
        next_tag = soup.find('a', rel=lambda r: r and 'next' in r.lower()) or \
                   soup.find('a', string=lambda t: t and 'next' in t.lower())
                   
        if next_tag and next_tag.get('href'):
            current_url = urljoin(current_url, next_tag['href'])
            await asyncio.sleep(PAGE_DELAY)
        else:
            print("[Info] End of archive reached.")
            current_url = None

    return ordinances


async def download_single_pdf(session, item, output_dir):
    """Phase 2: Stream-download a single PDF file under semaphore control."""
    pdf_url = item['pdf_url']
    ord_no = item['ordinance_no']

    if not pdf_url:
        return

    safe_name = "".join(c for c in ord_no if c.isalnum() or c in ('-', '_')).strip()
    file_path = os.path.join(output_dir, f"{safe_name}.pdf")

    # Skip redownloading existing files
    if os.path.exists(file_path):
        return

    async with semaphore:
        await asyncio.sleep(DOWNLOAD_DELAY)
        try:
            async with session.get(pdf_url, headers=HEADERS, timeout=REQUEST_TIMEOUT) as res:
                if res.status == 200:
                    # Stream download in 64KB chunks to conserve memory
                    with open(file_path, 'wb') as f:
                        async for chunk in res.content.iter_chunked(65536):
                            f.write(chunk)
                    print(f"[Downloaded] {safe_name}.pdf")
                else:
                    print(f"[Broken Link] Ordinance {ord_no}: HTTP {res.status} ({pdf_url})")
        except Exception as e:
            print(f"[Failed] {ord_no}: {e}")


async def main(max_pages=5, download_pdfs=True):
    output_dir = 'downloads'
    if download_pdfs and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # TCPConnector limits maximum connection pools at the transport layer
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 1. Harvest records
        records = await harvest_catalog(session, max_pages=max_pages)
        print(f"\n[Info] Captured {len(records)} records. Saving CSV...")

        # 2. Write CSV index
        with open('davao_ordinances.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['ordinance_no', 'description', 'pdf_url'])
            writer.writeheader()
            writer.writerows(records)

        # 3. Concurrent downloads
        if download_pdfs and records:
            print(f"\n[Info] Downloading {len(records)} PDFs (Concurrency limit: {MAX_CONCURRENT_DOWNLOADS})...")
            tasks = [download_single_pdf(session, item, output_dir) for item in records]
            await asyncio.gather(*tasks)

    print("\nScrape job fully completed.")

if __name__ == '__main__':
    asyncio.run(main(max_pages=None, download_pdfs=False))