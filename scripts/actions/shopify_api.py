"""
Shopify Admin GraphQL API wrapper.
API Version: 2026-01
Store: gadgetgeekspro.myshopify.com
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


_cached_token = None


def _get_access_token() -> str:
    """Get a valid Shopify access token, refreshing via client credentials if needed."""
    global _cached_token

    # If a static token is set, use it
    static_token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    if static_token:
        return static_token

    # If we already refreshed this run, reuse it
    if _cached_token:
        return _cached_token

    # Auto-refresh using client credentials grant (token expires every 24h)
    store = os.environ.get("SHOPIFY_STORE", "gadgetgeekspro.myshopify.com")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise Exception("Neither SHOPIFY_ACCESS_TOKEN nor SHOPIFY_CLIENT_ID/SECRET set")

    url = f"https://{store}/admin/oauth/access_token"
    body = (
        f"grant_type=client_credentials"
        f"&client_id={client_id}"
        f"&client_secret={client_secret}"
    ).encode("utf-8")

    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            _cached_token = result["access_token"]
            print(f"  Shopify token refreshed (expires in {result.get('expires_in', '?')}s)")
            return _cached_token
    except (HTTPError, KeyError) as e:
        raise Exception(f"Failed to refresh Shopify token: {e}")


def query_shopify(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against the Shopify Admin API.

    Args:
        query: GraphQL query string
        variables: Optional query variables
    """
    store = os.environ.get("SHOPIFY_STORE", "gadgetgeekspro.myshopify.com")
    token = _get_access_token()

    if not token:
        raise Exception("Could not obtain Shopify access token")

    url = f"https://{store}/admin/api/2026-01/graphql.json"

    data = {"query": query}
    if variables:
        data["variables"] = variables

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }

    body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "errors" in result:
                raise Exception(f"GraphQL errors: {result['errors']}")
            return result.get("data", result)
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Shopify API error {e.code}: {error_body}")


# Common queries
PRODUCTS_QUERY = """
query GetProducts($first: Int!) {
  products(first: $first) {
    edges {
      node {
        id
        title
        description
        handle
        productType
        tags
        priceRange {
          minVariantPrice { amount currencyCode }
          maxVariantPrice { amount currencyCode }
        }
        seo {
          title
          description
        }
      }
    }
  }
}
"""

ORDERS_QUERY = """
query GetRecentOrders($first: Int!) {
  orders(first: $first, sortKey: CREATED_AT, reverse: true) {
    edges {
      node {
        id
        name
        totalPriceSet { shopMoney { amount } }
        createdAt
        lineItems(first: 5) {
          edges {
            node {
              title
              quantity
            }
          }
        }
      }
    }
  }
}
"""

CUSTOMERS_QUERY = """
query GetCustomers($first: Int!) {
  customers(first: $first, sortKey: UPDATED_AT, reverse: true) {
    edges {
      node {
        id
        email
        ordersCount
        totalSpent
        tags
        createdAt
      }
    }
  }
}
"""
