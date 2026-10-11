"""proxy/proxy_scraper.py — scrape helpers"""
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


def scrape_providers(providers: List[Dict], download_fn, max_workers: int = 20) -> List:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(download_fn, p) for p in providers]
        for fut in as_completed(futs):
            try:
                results.extend(fut.result() or [])
            except Exception:
                pass
    return results


def scrape_free() -> List[str]:
    return []
