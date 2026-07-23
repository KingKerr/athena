from __future__ import annotations

from typing import Any

from .client import MassiveClient


class MassiveFilingsAPI:
    def __init__(self, client: MassiveClient) -> None:
        self.client = client

    def get_risk_factors(
        self,
        ticker: str | None = None,
        cik: str | None = None,
        filing_date_gte: str | None = None,
        filing_date_lte: str | None = None,
        limit: int = 100,
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "limit": min(limit, 1000),
            "order": order,
        }

        if ticker:
            params["ticker"] = ticker
        if cik:
            params["cik"] = cik
        if filing_date_gte:
            params["filing_date.gte"] = filing_date_gte
        if filing_date_lte:
            params["filing_date.lte"] = filing_date_lte

        return self.client.list_all_pages("/stocks/filings/vX/risk-factors", params=params)

    def get_filing_sections(
        self,
        ticker: str | None = None,
        cik: str | None = None,
        filing_date_gte: str | None = None,
        filing_date_lte: str | None = None,
        form_type: str | None = None,
        limit: int = 100,
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "limit": min(limit, 1000),
            "order": order,
        }

        if ticker:
            params["ticker"] = ticker
        if cik:
            params["cik"] = cik
        if filing_date_gte:
            params["filing_date.gte"] = filing_date_gte
        if filing_date_lte:
            params["filing_date.lte"] = filing_date_lte
        if form_type:
            params["form_type"] = form_type

        return self.client.list_all_pages("/stocks/filings/10-K/vX/sections", params=params)

    @staticmethod
    def normalize_risk_factors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for row in rows:
            normalized.append(
                {
                    "ticker": row.get("ticker"),
                    "cik": row.get("cik"),
                    "company_name": row.get("company_name"),
                    "filing_date": row.get("filing_date"),
                    "form_type": row.get("form_type"),
                    "accession_number": row.get("accession_number"),
                    "primary_category": row.get("primary_category"),
                    "secondary_category": row.get("secondary_category"),
                    "tertiary_category": row.get("tertiary_category"),
                    "supporting_text": row.get("supporting_text"),
                    "raw": row,
                }
            )

        return normalized

    @staticmethod
    def normalize_filing_sections(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for row in rows:
            normalized.append(
                {
                    "ticker": row.get("ticker"),
                    "cik": row.get("cik"),
                    "company_name": row.get("company_name"),
                    "filing_date": row.get("filing_date"),
                    "form_type": row.get("form_type"),
                    "accession_number": row.get("accession_number"),
                    "section_name": row.get("section_name"),
                    "section_text": row.get("text") or row.get("section_text"),
                    "raw": row,
                }
            )

        return normalized