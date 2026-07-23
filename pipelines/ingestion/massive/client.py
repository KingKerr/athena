from __future__ import annotations

import time
from typing import Any

import httpx


class MassiveClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.massive.com",
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "athena/0.1",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.headers,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MassiveClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.get(path, params=params)
                response.raise_for_status()
                payload = response.json()

                if isinstance(payload, dict) and payload.get("status") not in (None, "OK", "DELAYED"):
                    raise RuntimeError(f"Massive API returned non-OK status: {payload.get('status')}")

                return payload
            except Exception as exc:
                last_exc = exc
                if attempt == self.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 5))

        raise RuntimeError(f"Massive request failed after {self.max_retries} attempts: {last_exc}") from last_exc

    def list_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        results_key: str = "results",
        max_pages: int = 25,
    ) -> list[dict[str, Any]]:
        params = dict(params or {})
        all_rows: list[dict[str, Any]] = []
        next_path: str | None = path
        next_params: dict[str, Any] | None = params
        page_count = 0

        while next_path and page_count < max_pages:
            payload = self.get(next_path, params=next_params)
            rows = payload.get(results_key, []) or []
            all_rows.extend(rows)

            next_url = payload.get("next_url")
            if next_url:
                next_path = next_url.replace(self.base_url, "")
                next_params = None
            else:
                next_path = None

            page_count += 1

        return all_rows