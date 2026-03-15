#!/usr/bin/env python3
"""
Google Analytics 4 + Google Search Console API client.
Fetches real data and saves it as JSON for the SIGNAL agent to analyze.

Usage:
    python scripts/actions/google_analytics.py

Requires environment variables:
    GOOGLE_SERVICE_ACCOUNT_KEY  - JSON key file contents (string)
    GA4_PROPERTY_ID             - GA4 property ID (e.g., 527689586)
    GSC_SITE_URL                - Search Console site URL (e.g., sc-domain:gadgetgeekspro.com)
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed.")
    print("Run: pip install google-api-python-client google-auth")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "departments" / "analytics" / "google-api-data.json"

# Scopes needed
GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
ALL_SCOPES = GA4_SCOPES + GSC_SCOPES


def get_credentials():
    """Build credentials from the service account JSON key in env var."""
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
    if not key_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")

    key_data = json.loads(key_json)
    credentials = service_account.Credentials.from_service_account_info(
        key_data, scopes=ALL_SCOPES
    )
    return credentials


def fetch_ga4_data(credentials, property_id: str) -> dict:
    """Fetch GA4 data: top pages, traffic sources, device breakdown."""
    service = build("analyticsdata", "v1beta", credentials=credentials)

    today = datetime.now(timezone.utc).date()
    current_start = (today - timedelta(days=7)).isoformat()
    current_end = (today - timedelta(days=1)).isoformat()
    previous_start = (today - timedelta(days=14)).isoformat()
    previous_end = (today - timedelta(days=8)).isoformat()

    results = {
        "property_id": property_id,
        "current_period": f"{current_start} to {current_end}",
        "previous_period": f"{previous_start} to {previous_end}",
        "top_pages": [],
        "traffic_sources": [],
        "device_breakdown": [],
        "overall_metrics": {},
    }

    # --- Top Pages Report ---
    try:
        response = service.properties().runReport(
            property=f"properties/{property_id}",
            body={
                "dateRanges": [
                    {"startDate": current_start, "endDate": current_end, "name": "current"},
                    {"startDate": previous_start, "endDate": previous_end, "name": "previous"},
                ],
                "dimensions": [{"name": "pagePath"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "bounceRate"},
                    {"name": "averageSessionDuration"},
                    {"name": "conversions"},
                    {"name": "totalRevenue"},
                    {"name": "screenPageViews"},
                ],
                "limit": 25,
                "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            },
        ).execute()

        for row in response.get("rows", []):
            page_path = row["dimensionValues"][0]["value"]
            metrics_current = [m["value"] for m in row["metricValues"][:6]]
            # Previous period metrics are in indices 6-11 if present
            metrics_previous = [m["value"] for m in row["metricValues"][6:12]] if len(row["metricValues"]) > 6 else [0] * 6

            results["top_pages"].append({
                "page": page_path,
                "current": {
                    "sessions": int(metrics_current[0] or 0),
                    "bounce_rate": round(float(metrics_current[1] or 0), 4),
                    "avg_session_duration": round(float(metrics_current[2] or 0), 1),
                    "conversions": int(float(metrics_current[3] or 0)),
                    "revenue": round(float(metrics_current[4] or 0), 2),
                    "pageviews": int(metrics_current[5] or 0),
                },
                "previous": {
                    "sessions": int(metrics_previous[0] or 0),
                    "bounce_rate": round(float(metrics_previous[1] or 0), 4),
                    "avg_session_duration": round(float(metrics_previous[2] or 0), 1),
                    "conversions": int(float(metrics_previous[3] or 0)),
                    "revenue": round(float(metrics_previous[4] or 0), 2),
                    "pageviews": int(metrics_previous[5] or 0),
                },
            })
        print(f"  GA4 Top Pages: {len(results['top_pages'])} pages fetched")
    except Exception as e:
        results["top_pages_error"] = str(e)
        print(f"  GA4 Top Pages ERROR: {e}")

    # --- Traffic Sources Report ---
    try:
        response = service.properties().runReport(
            property=f"properties/{property_id}",
            body={
                "dateRanges": [
                    {"startDate": current_start, "endDate": current_end, "name": "current"},
                    {"startDate": previous_start, "endDate": previous_end, "name": "previous"},
                ],
                "dimensions": [
                    {"name": "sessionSource"},
                    {"name": "sessionMedium"},
                ],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "conversions"},
                    {"name": "totalRevenue"},
                ],
                "limit": 15,
                "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            },
        ).execute()

        for row in response.get("rows", []):
            source = row["dimensionValues"][0]["value"]
            medium = row["dimensionValues"][1]["value"]
            metrics_current = [m["value"] for m in row["metricValues"][:3]]
            metrics_previous = [m["value"] for m in row["metricValues"][3:6]] if len(row["metricValues"]) > 3 else [0] * 3

            results["traffic_sources"].append({
                "source_medium": f"{source} / {medium}",
                "current": {
                    "sessions": int(metrics_current[0] or 0),
                    "conversions": int(float(metrics_current[1] or 0)),
                    "revenue": round(float(metrics_current[2] or 0), 2),
                },
                "previous": {
                    "sessions": int(metrics_previous[0] or 0),
                    "conversions": int(float(metrics_previous[1] or 0)),
                    "revenue": round(float(metrics_previous[2] or 0), 2),
                },
            })
        print(f"  GA4 Traffic Sources: {len(results['traffic_sources'])} sources fetched")
    except Exception as e:
        results["traffic_sources_error"] = str(e)
        print(f"  GA4 Traffic Sources ERROR: {e}")

    # --- Device Breakdown ---
    try:
        response = service.properties().runReport(
            property=f"properties/{property_id}",
            body={
                "dateRanges": [
                    {"startDate": current_start, "endDate": current_end, "name": "current"},
                    {"startDate": previous_start, "endDate": previous_end, "name": "previous"},
                ],
                "dimensions": [{"name": "deviceCategory"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "conversions"},
                    {"name": "activeUsers"},
                ],
                "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            },
        ).execute()

        for row in response.get("rows", []):
            device = row["dimensionValues"][0]["value"]
            metrics_current = [m["value"] for m in row["metricValues"][:3]]
            metrics_previous = [m["value"] for m in row["metricValues"][3:6]] if len(row["metricValues"]) > 3 else [0] * 3

            results["device_breakdown"].append({
                "device": device,
                "current": {
                    "sessions": int(metrics_current[0] or 0),
                    "conversions": int(float(metrics_current[1] or 0)),
                    "active_users": int(metrics_current[2] or 0),
                },
                "previous": {
                    "sessions": int(metrics_previous[0] or 0),
                    "conversions": int(float(metrics_previous[1] or 0)),
                    "active_users": int(metrics_previous[2] or 0),
                },
            })
        print(f"  GA4 Device Breakdown: {len(results['device_breakdown'])} categories fetched")
    except Exception as e:
        results["device_breakdown_error"] = str(e)
        print(f"  GA4 Device Breakdown ERROR: {e}")

    # --- Overall Metrics ---
    try:
        response = service.properties().runReport(
            property=f"properties/{property_id}",
            body={
                "dateRanges": [
                    {"startDate": current_start, "endDate": current_end, "name": "current"},
                    {"startDate": previous_start, "endDate": previous_end, "name": "previous"},
                ],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "totalUsers"},
                    {"name": "newUsers"},
                    {"name": "bounceRate"},
                    {"name": "averageSessionDuration"},
                    {"name": "conversions"},
                    {"name": "totalRevenue"},
                ],
            },
        ).execute()

        if response.get("rows"):
            row = response["rows"][0]
            metrics_current = [m["value"] for m in row["metricValues"][:7]]
            metrics_previous = [m["value"] for m in row["metricValues"][7:14]] if len(row["metricValues"]) > 7 else [0] * 7

            results["overall_metrics"] = {
                "current": {
                    "sessions": int(metrics_current[0] or 0),
                    "total_users": int(metrics_current[1] or 0),
                    "new_users": int(metrics_current[2] or 0),
                    "bounce_rate": round(float(metrics_current[3] or 0), 4),
                    "avg_session_duration": round(float(metrics_current[4] or 0), 1),
                    "conversions": int(float(metrics_current[5] or 0)),
                    "revenue": round(float(metrics_current[6] or 0), 2),
                },
                "previous": {
                    "sessions": int(metrics_previous[0] or 0),
                    "total_users": int(metrics_previous[1] or 0),
                    "new_users": int(metrics_previous[2] or 0),
                    "bounce_rate": round(float(metrics_previous[3] or 0), 4),
                    "avg_session_duration": round(float(metrics_previous[4] or 0), 1),
                    "conversions": int(float(metrics_previous[5] or 0)),
                    "revenue": round(float(metrics_previous[6] or 0), 2),
                },
            }
        print(f"  GA4 Overall Metrics: fetched")
    except Exception as e:
        results["overall_metrics_error"] = str(e)
        print(f"  GA4 Overall Metrics ERROR: {e}")

    return results


def fetch_gsc_data(credentials, site_url: str) -> dict:
    """Fetch Google Search Console data: queries, pages, crawl status."""
    service = build("searchconsole", "v1", credentials=credentials)

    today = datetime.now(timezone.utc).date()
    # GSC data has 2-3 day lag
    current_start = (today - timedelta(days=10)).isoformat()
    current_end = (today - timedelta(days=3)).isoformat()
    previous_start = (today - timedelta(days=17)).isoformat()
    previous_end = (today - timedelta(days=10)).isoformat()

    results = {
        "site_url": site_url,
        "current_period": f"{current_start} to {current_end}",
        "previous_period": f"{previous_start} to {previous_end}",
        "top_queries": [],
        "top_pages": [],
        "previous_queries": {},
        "previous_pages": {},
    }

    # --- Top Queries (current period) ---
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": current_start,
                "endDate": current_end,
                "dimensions": ["query"],
                "rowLimit": 50,
                "type": "web",
            },
        ).execute()

        for row in response.get("rows", []):
            results["top_queries"].append({
                "query": row["keys"][0],
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            })
        print(f"  GSC Top Queries: {len(results['top_queries'])} queries fetched")
    except Exception as e:
        results["top_queries_error"] = str(e)
        print(f"  GSC Top Queries ERROR: {e}")

    # --- Top Queries (previous period for comparison) ---
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": previous_start,
                "endDate": previous_end,
                "dimensions": ["query"],
                "rowLimit": 50,
                "type": "web",
            },
        ).execute()

        for row in response.get("rows", []):
            results["previous_queries"][row["keys"][0]] = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            }
        print(f"  GSC Previous Queries: {len(results['previous_queries'])} queries fetched")
    except Exception as e:
        results["previous_queries_error"] = str(e)
        print(f"  GSC Previous Queries ERROR: {e}")

    # --- Top Pages (current period) ---
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": current_start,
                "endDate": current_end,
                "dimensions": ["page"],
                "rowLimit": 30,
                "type": "web",
            },
        ).execute()

        for row in response.get("rows", []):
            results["top_pages"].append({
                "page": row["keys"][0],
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            })
        print(f"  GSC Top Pages: {len(results['top_pages'])} pages fetched")
    except Exception as e:
        results["top_pages_error"] = str(e)
        print(f"  GSC Top Pages ERROR: {e}")

    # --- Top Pages (previous period for comparison) ---
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": previous_start,
                "endDate": previous_end,
                "dimensions": ["page"],
                "rowLimit": 30,
                "type": "web",
            },
        ).execute()

        for row in response.get("rows", []):
            results["previous_pages"][row["keys"][0]] = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            }
        print(f"  GSC Previous Pages: {len(results['previous_pages'])} pages fetched")
    except Exception as e:
        results["previous_pages_error"] = str(e)
        print(f"  GSC Previous Pages ERROR: {e}")

    # --- Query + Page combined (for high-impression/low-CTR detection) ---
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": current_start,
                "endDate": current_end,
                "dimensions": ["query", "page"],
                "rowLimit": 100,
                "type": "web",
            },
        ).execute()

        high_impression_low_ctr = []
        for row in response.get("rows", []):
            impressions = row.get("impressions", 0)
            ctr = row.get("ctr", 0)
            position = row.get("position", 0)
            # High impressions, low CTR, within striking distance
            if impressions > 50 and ctr < 0.02 and 3 <= position <= 20:
                high_impression_low_ctr.append({
                    "query": row["keys"][0],
                    "page": row["keys"][1],
                    "clicks": row.get("clicks", 0),
                    "impressions": impressions,
                    "ctr": round(ctr, 4),
                    "position": round(position, 1),
                })

        results["high_impression_low_ctr"] = sorted(
            high_impression_low_ctr, key=lambda x: x["impressions"], reverse=True
        )[:20]
        print(f"  GSC Quick Wins: {len(results['high_impression_low_ctr'])} opportunities found")
    except Exception as e:
        results["high_impression_low_ctr_error"] = str(e)
        print(f"  GSC Quick Wins ERROR: {e}")

    return results


def main():
    """Fetch all Google API data and save to JSON file."""
    print("=" * 60)
    print("  GOOGLE API DATA FETCH")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    property_id = os.environ.get("GA4_PROPERTY_ID", "")
    site_url = os.environ.get("GSC_SITE_URL", "")

    if not property_id:
        print("ERROR: GA4_PROPERTY_ID not set")
        sys.exit(1)

    try:
        credentials = get_credentials()
        print("  Credentials loaded successfully")
    except Exception as e:
        print(f"ERROR: Failed to load credentials: {e}")
        sys.exit(1)

    output = {
        "fetch_time": datetime.now(timezone.utc).isoformat(),
        "ga4": {},
        "gsc": {},
    }

    # Fetch GA4 data
    print("\n[GA4] Fetching Google Analytics 4 data...")
    try:
        output["ga4"] = fetch_ga4_data(credentials, property_id)
        print("[GA4] Done.")
    except Exception as e:
        output["ga4"] = {"error": str(e)}
        print(f"[GA4] FAILED: {e}")

    # Fetch GSC data (only if site URL is configured)
    if site_url:
        print("\n[GSC] Fetching Google Search Console data...")
        try:
            output["gsc"] = fetch_gsc_data(credentials, site_url)
            print("[GSC] Done.")
        except Exception as e:
            output["gsc"] = {"error": str(e)}
            print(f"[GSC] FAILED: {e}")
    else:
        output["gsc"] = {"error": "GSC_SITE_URL not configured — skipping Search Console data"}
        print("\n[GSC] SKIPPED — GSC_SITE_URL not set")

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nData saved to: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
