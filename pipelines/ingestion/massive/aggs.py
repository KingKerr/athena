from __future__ import annotations

from typing import Any

from .client import MassiveClient


class MassiveAggsAPI:
    def __init__(self, client: MassiveClient) -> None:
        self.client = client

    def get_range_bars(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        from_date: str,
        to_date: str,
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 5000,
    ) -> dict[str, Any]:
        path = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            "adjusted": str(adjusted).lower(),
            "sort": sort,
            "limit": min(limit, 50000),
        }
        return self.client.get(path, params=params)

    def get_daily_bars(
        self,
        ticker: str,
        from_date: str,
        to_date: str,
        adjusted: bool = True,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        payload = self.get_range_bars(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_date=from_date,
            to_date=to_date,
            adjusted=adjusted,
            sort="asc",
            limit=limit,
        )
        return payload.get("results", []) or []

    @staticmethod
    def normalize_bars(rows: list[dict[str, Any]], ticker: str) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for row in rows:
            normalized.append(
                {
                    "ticker": ticker,
                    "ts_ms": row.get("t"),
                    "open": row.get("o"),
                    "high": row.get("h"),
                    "low": row.get("l"),
                    "close": row.get("c"),
                    "volume": row.get("v"),
                    "vwap": row.get("vw"),
                    "transactions": row.get("n"),
                    "otc": row.get("otc", False),
                    "raw": row,
                }
            )

        return normalized