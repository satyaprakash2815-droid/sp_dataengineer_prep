"""Q10: call a public API with timeout, error handling, retry + backoff; save JSON."""
import json
import time
from pathlib import Path

import requests

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def fetch_json(url, out_path, retries=3, timeout=5, backoff=1.0, logger=None):
    """GET url, retry on timeouts / connection errors / 429 / 5xx with exponential backoff."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)      # always set a timeout
            if resp.status_code in RETRYABLE_STATUS:
                raise requests.HTTPError(f"retryable status {resp.status_code}")
            resp.raise_for_status()                        # other 4xx -> fail fast
            data = resp.json()
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return data
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
        except requests.HTTPError as e:
            if resp.status_code not in RETRYABLE_STATUS:   # 404, 401... retrying won't help
                raise
            last_error = e
        except ValueError as e:                            # response was not valid JSON
            raise RuntimeError(f"invalid JSON from {url}") from e
        if logger:
            logger.warning(f"attempt {attempt}/{retries} failed: {last_error}")
        if attempt < retries:
            time.sleep(backoff * 2 ** (attempt - 1))       # 1s, 2s, 4s ...
    raise RuntimeError(f"giving up after {retries} attempts: {last_error}")


if __name__ == "__main__":
    data = fetch_json("https://jsonplaceholder.typicode.com/posts/1", "output/api_response.json")
    print(data)
