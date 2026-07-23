from __future__ import annotations

from typing import Any

from .client import MassiveClient


class MassiveNewsAPI:
    def __init__(self, client: MassiveClient) -> None:
        self.client = client

    def get_ticker_news(
        self,
        ticker: str,
        published_utc_gte: str | None = None,
        published_utc_lte: str | None = None,
        limit: int = 50,
        sort: str = "published_utc",
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "ticker": ticker,
            "limit": min(limit, 1000),
            "sort": sort,
            "order": order,
        }

        if published_utc_gte and published_utc_lte:
            params["published_utc"] = f"{published_utc_gte}/{published_utc_lte}"
        elif published_utc_gte:
            params["published_utc.gte"] = published_utc_gte
        elif published_utc_lte:
            params["published_utc.lte"] = published_utc_lte

        return self.client.list_all_pages("/v2/reference/news", params=params)

    @staticmethod
    def normalize_news(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for row in rows:
            normalized.append(
                {
                    "news_id": row.get("id"),
                    "title": row.get("title"),
                    "description": row.get("description"),
                    "article_url": row.get("article_url"),
                    "image_url": row.get("image_url"),
                    "author": row.get("author"),
                    "published_utc": row.get("published_utc"),
                    "keywords": row.get("keywords") or [],
                    "tickers": row.get("tickers") or [],
                    "publisher_name": (row.get("publisher") or {}).get("name"),
                    "publisher_homepage_url": (row.get("publisher") or {}).get("homepage_url"),
                    "publisher_logo_url": (row.get("publisher") or {}).get("logo_url"),
                    "insights": row.get("insights") or [],
                    "raw": row,
                }
            )

        return normalized