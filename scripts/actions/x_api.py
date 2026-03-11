"""
X (Twitter) API v2 wrapper.
Uses Bearer Token authentication.
Env: X_BEARER_TOKEN
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

BASE = "https://api.twitter.com/2"


def _get_token() -> str:
    token = os.environ.get("X_BEARER_TOKEN", "")
    if not token:
        raise Exception("X_BEARER_TOKEN not set")
    return token


def _get(endpoint: str, params: dict = None) -> dict:
    """Make authenticated GET request to X API v2."""
    token = _get_token()
    url = f"{BASE}/{endpoint}"
    if params:
        url += "?" + urlencode(params)

    req = Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "GadgetGeeksMarketingOrg/1.0")

    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"X API error {e.code}: {body}")


# ── Tweet Lookup ──────────────────────────────────────────

def get_tweet(tweet_id: str) -> dict:
    """Get a single tweet by ID with full details.

    Args:
        tweet_id: The tweet/post ID (numeric string)

    Returns:
        dict with 'data' containing tweet fields
    """
    params = {
        "tweet.fields": "created_at,public_metrics,author_id,conversation_id,context_annotations,entities,lang",
        "expansions": "author_id,referenced_tweets.id",
        "user.fields": "name,username,verified,public_metrics,description",
    }
    return _get(f"tweets/{tweet_id}", params)


def get_tweets(tweet_ids: list) -> dict:
    """Get multiple tweets by IDs (up to 100).

    Args:
        tweet_ids: List of tweet ID strings

    Returns:
        dict with 'data' containing list of tweets
    """
    params = {
        "ids": ",".join(tweet_ids[:100]),
        "tweet.fields": "created_at,public_metrics,author_id,context_annotations,entities",
        "expansions": "author_id",
        "user.fields": "name,username,verified,public_metrics",
    }
    return _get("tweets", params)


# ── Search ────────────────────────────────────────────────

def search_recent(query: str, max_results: int = 10) -> dict:
    """Search recent tweets (last 7 days).

    Args:
        query: Search query (supports X search operators)
               Examples:
                 "refurbished iPhone"
                 "refurbished phone -is:retweet lang:en"
                 "@BackMarket OR @Swappa"
        max_results: 10-100

    Returns:
        dict with 'data' containing list of matching tweets
    """
    params = {
        "query": query,
        "max_results": min(max(max_results, 10), 100),
        "tweet.fields": "created_at,public_metrics,author_id,context_annotations,entities,lang",
        "expansions": "author_id",
        "user.fields": "name,username,verified,public_metrics",
        "sort_order": "relevancy",
    }
    return _get("tweets/search/recent", params)


# ── User Lookup ───────────────────────────────────────────

def get_user(username: str) -> dict:
    """Get user profile by username (without @).

    Args:
        username: X username without the @ symbol

    Returns:
        dict with 'data' containing user fields
    """
    params = {
        "user.fields": "created_at,description,public_metrics,verified,url,location,pinned_tweet_id",
    }
    return _get(f"users/by/username/{username}", params)


def get_user_tweets(user_id: str, max_results: int = 10) -> dict:
    """Get recent tweets from a specific user.

    Args:
        user_id: The user's numeric ID
        max_results: 5-100

    Returns:
        dict with 'data' containing user's recent tweets
    """
    params = {
        "max_results": min(max(max_results, 5), 100),
        "tweet.fields": "created_at,public_metrics,entities,context_annotations",
        "exclude": "retweets,replies",
    }
    return _get(f"users/{user_id}/tweets", params)


# ── Trending / Popular ────────────────────────────────────

def search_popular(query: str, max_results: int = 10) -> dict:
    """Search for popular/engaging tweets on a topic.
    Sorts by relevancy which favors high-engagement tweets.

    Args:
        query: Search query
        max_results: 10-100
    """
    params = {
        "query": f"{query} -is:retweet lang:en",
        "max_results": min(max(max_results, 10), 100),
        "tweet.fields": "created_at,public_metrics,author_id,entities",
        "expansions": "author_id",
        "user.fields": "name,username,verified,public_metrics",
        "sort_order": "relevancy",
    }
    return _get("tweets/search/recent", params)


# ── Conversation Thread ───────────────────────────────────

def get_conversation(conversation_id: str, max_results: int = 20) -> dict:
    """Get replies in a conversation thread.

    Args:
        conversation_id: The conversation ID (usually same as original tweet ID)
        max_results: 10-100
    """
    params = {
        "query": f"conversation_id:{conversation_id}",
        "max_results": min(max(max_results, 10), 100),
        "tweet.fields": "created_at,public_metrics,author_id,in_reply_to_user_id",
        "expansions": "author_id",
        "user.fields": "name,username",
    }
    return _get("tweets/search/recent", params)


# ── Utility: Parse tweet URL ──────────────────────────────

def parse_tweet_url(url: str) -> str:
    """Extract tweet ID from an X/Twitter URL.

    Handles:
        https://x.com/user/status/123456789
        https://twitter.com/user/status/123456789
        https://x.com/user/status/123456789?s=20

    Returns:
        Tweet ID string
    """
    import re
    match = re.search(r'(?:x\.com|twitter\.com)/\w+/status/(\d+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not parse tweet ID from URL: {url}")


# ── Pre-built queries for refurbished phone niche ─────────

NICHE_QUERIES = {
    "refurb_general": '"refurbished phone" OR "refurbished iPhone" OR "refurbished Samsung" -is:retweet lang:en',
    "competitors": "@BackMarket OR @BuySwappa OR @Gazelle OR @decluttrhq OR @amazonrenewed -is:retweet lang:en",
    "deals": '"phone deal" OR "budget phone" OR "cheap iPhone" OR "phone under $" -is:retweet lang:en',
    "trust_concerns": '"refurbished worth it" OR "refurbished scam" OR "refurbished quality" -is:retweet lang:en',
    "sustainability": '"e-waste" OR "phone recycling" OR "right to repair" OR "sustainable phone" -is:retweet lang:en',
    "new_launches": '"iPhone 16" OR "Galaxy S25" OR "Pixel 9" OR "new phone price" -is:retweet lang:en',
}


def run_niche_scan(max_per_query: int = 10) -> dict:
    """Run all niche queries and return combined results.
    This is what ECHO calls daily to gather X intelligence.

    Returns:
        dict mapping query name to search results
    """
    results = {}
    for name, query in NICHE_QUERIES.items():
        try:
            data = search_recent(query, max_results=max_per_query)
            results[name] = data
            print(f"  X scan [{name}]: {len(data.get('data', []))} tweets")
        except Exception as e:
            print(f"  X scan [{name}] error: {e}")
            results[name] = {"error": str(e)}
    return results
