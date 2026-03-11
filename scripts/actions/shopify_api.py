"""
Shopify Admin GraphQL API wrapper.
API Version: 2026-01
Store: gadgetgeekspro.myshopify.com
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def query_shopify(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against the Shopify Admin API.

    Args:
        query: GraphQL query string
        variables: Optional query variables
    """
    store = os.environ.get("SHOPIFY_STORE", "gadgetgeekspro.myshopify.com")
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")

    if not token:
        raise Exception("SHOPIFY_ACCESS_TOKEN not set")

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
