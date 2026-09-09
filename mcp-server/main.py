"""
Tiendanube/Nuvemshop MCP Server

A Model Context Protocol server for interacting with the Tiendanube/Nuvemshop API.
Supports products, orders, customers, categories, and more.

Installation:
    uv add "mcp[cli]" requests pydantic

Usage:
    # Test with MCP Inspector
    uv run mcp dev tiendanube_server.py
    
    # Install in Claude Desktop
    uv run mcp install tiendanube_server.py
    
    # Run directly
    python tiendanube_server.py

Environment Variables:
    TIENDANUBE_ACCESS_TOKEN: Your Tiendanube API access token
    TIENDANUBE_STORE_ID: Your store ID
    TIENDANUBE_BASE_URL: Base URL (default: https://api.tiendanube.com/v1)
"""

import os
from typing import Any, Optional
from dataclasses import dataclass

import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

# Configuration
@dataclass
class TiendanubeConfig:
    """Tiendanube API configuration"""
    access_token: str
    store_id: str
    user_agent: str
    base_url: str = "https://api.tiendanube.com/v1"
    
    @property
    def api_url(self) -> str:
        return f"{self.base_url}/{self.store_id}"
    
    @property
    def headers(self) -> dict[str, Any]:
        return {
            "Authentication": f"bearer {self.access_token}",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": f"{self.user_agent}"
        }


# Initialize FastMCP server
mcp = FastMCP(
    "Nuvemshop Dev",
    instructions="""
    This server provides access to the Tiendanube/Nuvemshop e-commerce API.
    
    Available operations:
    - Products: list_products, get_product, get_product_by_sku, create_product, update_product, delete_product, update_product_stock_price
    - Orders: list_orders, get_order, get_order_history_values, get_order_history_editions, create_order, update_order, close_order, open_order, cancel_order
    - Customers: list_customers, get_customer, create_customer, update_customer,  delete_customer
    - Categories: list_categories, get_category, create_category, update_category, delete_category
    - Store: get_store
    - Coupons: list_coupons, get_coupon, create_coupon,
    - Billing: create_billing_plan, update_billing_plan, delete_billing_plan, get_subscription, update_subscription, create_extra_charge
    - Webhooks: list_webhooks, get_webhook, create_webhook, update_webhook, delete_webhook
    - Theme (Nuvemshop CLI): theme_list, theme_current, theme_pull, theme_diff, theme_push, theme_publish, theme_preview, theme_performance, theme_fork
    Avaliabe Resources:
    - tiendanube://store
    - tiendanube://orders/summary
    - tiendanube://products/low-stock
    Avaliable Prompts:
    - analyze_product_performance
    - customer_segmentation
    - order_fulfillment_analysis
    - revenue_analysis
    - abandoned_orders_recovery
    - inventory_management_analysis
    - variant_optimization
    - billing_analysis
    - subscription_management
    
    All operations require proper authentication via access token and store ID.
    """,
    host="0.0.0.0", port=8080
)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    return Response({'status': 'ok'}, media_type="application/json")


# Helper function to get config
def get_config() -> TiendanubeConfig:
    """Get Nuvemshop configuration from environment variables"""
    access_token = os.getenv("TIENDANUBE_ACCESS_TOKEN", "")
    store_id = os.getenv("TIENDANUBE_STORE_ID", "")
    base_url = os.getenv("TIENDANUBE_BASE_URL", "https://api.nuvemshop.com.br/2025-03")
    user_agent = os.getenv("TIENDANUBE_USER_AGENT", "nuvemshop-dev-mcp (denis.palhares22@gmail.com)")

    if not access_token:
        raise ValueError("TIENDANUBE_ACCESS_TOKEN environment variable is required")
    if not store_id:
        raise ValueError("TIENDANUBE_STORE_ID environment variable is required")

    return TiendanubeConfig(
        access_token=access_token,
        store_id=store_id,
        base_url=base_url,
        user_agent=user_agent
    )


def make_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    json_data: Optional[dict] = None
) -> dict:
    """Make HTTP request to Tiendanube API"""
    config = get_config()
    url = f"{config.api_url}{endpoint}"
    
    response = requests.request(
        method=method,
        url=url,
        headers=config.headers,
        params=params,
        json=json_data,
        timeout=30
    )
    
    if response.status_code == 204:
        return {"success": True}
    
    response.raise_for_status()
    return response.json()


# ============================================================================
# PRODUCTS
# ============================================================================

@mcp.tool()
def list_products(
    page: int = 1,
    per_page: int = 30,
    ids: Optional[str] = None,
    since_id: Optional[int] = None,
    language: Optional[str] = None,
    query: Optional[str] = None,
    handle: Optional[str] = None,
    category_id: Optional[int] = None,
    published: Optional[bool] = None,
    free_shipping: Optional[bool] = None,
    max_stock: Optional[int] = None,
    min_stock: Optional[int] = None,
    has_promotional_price: Optional[bool] = None,
    has_weight: Optional[bool] = None,
    has_all_dimensions: Optional[bool] = None,
    has_weight_and_all_dimensions: Optional[bool] = None,
    created_at_min: Optional[str] = None,
    created_at_max: Optional[str] = None,
    updated_at_min: Optional[str] = None,
    updated_at_max: Optional[str] = None,
    sort_by: str = "user",
    fields: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    List all products in the store.
    
    Args:
        page: Page number (default: 1)
        per_page: Results per page (max: 200, default: 30)
        ids: Comma-separated product IDs (max 30 IDs)
        since_id: Show products after this ID
        language: Search in specific language
        query: Search products by name, description or SKU
        handle: Show products with specific URL handle
        category_id: Filter by category ID
        published: Filter by published status (true/false)
        free_shipping: Filter by free shipping (true/false)
        max_stock: Show products with stock ≤ this value
        min_stock: Show products with stock ≥ this value
        has_promotional_price: Filter products with promotional price (true/false)
        has_weight: Filter products with defined weight (true/false)
        has_all_dimensions: Filter products with depth, width, height (true/false)
        has_weight_and_all_dimensions: Filter products with all shipping info (true/false)
        created_at_min: Show products created after date (ISO 8601)
        created_at_max: Show products created before date (ISO 8601)
        updated_at_min: Show products updated after date (ISO 8601)
        updated_at_max: Show products updated before date (ISO 8601)
        sort_by: Sort criteria (user, price-ascending, price-descending, 
                 name-ascending, name-descending, created-at-ascending, 
                 created-at-descending, best-selling, cost-ascending, cost-descending)
        fields: Comma-separated fields to include (e.g., "id,name,price")
    
    Returns:
        List of products with variants, images, categories, and attributes
    
    Note:
        A new Product API with multi-inventory support is being rolled out.
        Contact Tiendanube to activate this version for your stores.
    """
    params = {
        "page": page,
        "per_page": min(per_page, 200),
        "sort_by": sort_by
    }
    
    if ids:
        params["ids"] = ids
    if since_id:
        params["since_id"] = since_id
    if language:
        params["language"] = language
    if query:
        params["q"] = query
    if handle:
        params["handle"] = handle
    if category_id:
        params["category_id"] = category_id
    if published is not None:
        params["published"] = "true" if published else "false"
    if free_shipping is not None:
        params["free_shipping"] = "true" if free_shipping else "false"
    if max_stock is not None:
        params["max_stock"] = max_stock
    if min_stock is not None:
        params["min_stock"] = min_stock
    if has_promotional_price is not None:
        params["has_promotional_price"] = "true" if has_promotional_price else "false"
    if has_weight is not None:
        params["has_weight"] = "true" if has_weight else "false"
    if has_all_dimensions is not None:
        params["has_all_dimensions"] = "true" if has_all_dimensions else "false"
    if has_weight_and_all_dimensions is not None:
        params["has_weight_and_all_dimensions"] = "true" if has_weight_and_all_dimensions else "false"
    if created_at_min:
        params["created_at_min"] = created_at_min
    if created_at_max:
        params["created_at_max"] = created_at_max
    if updated_at_min:
        params["updated_at_min"] = updated_at_min
    if updated_at_max:
        params["updated_at_max"] = updated_at_max
    if fields:
        params["fields"] = fields
    
    return make_request("GET", "/products", params=params)


@mcp.tool()
def get_product(product_id: int, fields: Optional[str] = None) -> dict:
    """
    Get a single product by ID.
    
    Args:
        product_id: The product ID
        fields: Comma-separated list of fields to include (e.g., "id,name,price")
    
    Returns:
        Product details
    """
    params = {}
    if fields:
        params["fields"] = fields
    
    return make_request("GET", f"/products/{product_id}", params=params)


@mcp.tool()
def get_product_by_sku(sku: str) -> dict:
    """
    Get a product by SKU (returns the first product found with matching variant SKU).
    
    Args:
        sku: The product variant SKU
    
    Returns:
        Product details
    """
    return make_request("GET", f"/products/sku/{sku}")


@mcp.tool()
def create_product(
    name: dict,
    variants: list[dict],
    description: Optional[dict] = None,
    images: Optional[list] = None,
    categories: Optional[list] = None,
    attributes: Optional[list] = None,
    published: bool = True,
    free_shipping: bool = False,
    video_url: Optional[str] = None,
    seo_title: Optional[str] = None,
    seo_description: Optional[str] = None,
    brand: Optional[str] = None,
    tags: Optional[str] = None
) -> dict:
    """
    Create a new product.
    
    Args:
        name: Product name in multiple languages (required)
            Example: {"en": "Product", "es": "Producto", "pt": "Produto"}
        variants: List of product variants (required), each with:
            - price (required): Variant price as string (e.g., "29.99")
            - stock: Stock quantity (omit or "" for unlimited)
            - stock_management: Set automatically (true if stock ≥ 0, false if unlimited)
            - promotional_price: Promotional price as string
            - sku: Stock keeping unit
            - weight: Weight in kg as string
            - width, height, depth: Dimensions as strings
            - cost: Cost price as string
            - values: List of attribute values (e.g., [{"en": "Small"}])
        description: Product description in multiple languages (HTML supported)
        images: List of image objects (max 9 recommended, 250 absolute max)
            Each image: {"src": "http://example.com/image.jpg"}
        categories: List of category IDs (will replace all if sent empty)
        attributes: List of product attributes (max 3)
            Each attribute: {"en": "Color"} or {"es": "Tamaño"}
            Same name cannot be repeated
        published: Whether the product is published (default: true)
        free_shipping: Whether the product has free shipping
        video_url: YouTube video URL (must be HTTPS)
        seo_title: SEO title for search engines
        seo_description: SEO description
        brand: Product brand name
        tags: Comma-separated tags
    
    Returns:
        Created product with full details including generated handles and IDs
    
    Limits:
        - Max 100,000 products per store
        - Max 250 images per product (recommend 9 per call, use POST /products/{id}/images for more)
        - Max 1,000 variants per product
        - Max 3 attributes per product
    
    Example:
        create_product(
            name={"en": "T-Shirt", "pt": "Camiseta"},
            description={"en": "<p>Premium cotton</p>"},
            variants=[
                {
                    "price": "29.99",
                    "stock": 100,
                    "sku": "TSH-BLK-M",
                    "weight": "0.2",
                    "values": [{"en": "Black"}, {"en": "Medium"}]
                }
            ],
            attributes=[{"en": "Color"}, {"en": "Size"}],
            categories=[123, 456],
            images=[{"src": "https://example.com/tshirt.jpg"}],
            tags="clothing, summer, casual"
        )
    
    Stock Management:
        - Set stock to "" (empty string) for unlimited/infinite stock
        - stock_management is automatic: false for unlimited, true for tracked
        - You cannot manually set stock_management via API
    """
    data = {
        "name": name,
        "variants": variants,
        "published": published,
        "free_shipping": free_shipping
    }
    
    if description:
        data["description"] = description
    if images:
        data["images"] = images
    if categories is not None:
        data["categories"] = categories
    if attributes:
        data["attributes"] = attributes
    if video_url:
        data["video_url"] = video_url
    if seo_title:
        data["seo_title"] = seo_title
    if seo_description:
        data["seo_description"] = seo_description
    if brand:
        data["brand"] = brand
    if tags:
        data["tags"] = tags
    
    return make_request("POST", "/products", json_data=data)


@mcp.tool()
def update_product(
    product_id: int,
    name: Optional[dict] = None,
    description: Optional[dict] = None,
    published: Optional[bool] = None,
    free_shipping: Optional[bool] = None,
    categories: Optional[list] = None,
    tags: Optional[str] = None,
    video_url: Optional[str] = None,
    seo_title: Optional[str] = None,
    seo_description: Optional[str] = None,
    brand: Optional[str] = None,
    attributes: Optional[list] = None
) -> dict:
    """
    Update an existing product.
    
    Args:
        product_id: The product ID
        name: Product name in multiple languages
        description: Product description in multiple languages
        published: Whether the product is published
        free_shipping: Whether the product has free shipping
        categories: List of category IDs (empty list removes all categories)
        tags: Comma-separated tags
        video_url: YouTube video URL (must be HTTPS)
        seo_title: SEO title
        seo_description: SEO description
        brand: Product brand
        attributes: Product attributes (max 3)
    
    Returns:
        Updated product details
    
    Important Notes:
        - If product has categories and you send categories=[], all categories are removed
        - To keep current categories, omit the categories field entirely
        - To update variant prices/stock, use PUT /products/{id}/variants/{variant_id}
        - For products without variants (single variant), update the "virtual" variant
        - Use update_product_stock_price() for bulk stock/price updates
    """
    data = {}
    
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if published is not None:
        data["published"] = published
    if free_shipping is not None:
        data["free_shipping"] = free_shipping
    if categories is not None:
        data["categories"] = categories
    if tags is not None:
        data["tags"] = tags
    if video_url is not None:
        data["video_url"] = video_url
    if seo_title is not None:
        data["seo_title"] = seo_title
    if seo_description is not None:
        data["seo_description"] = seo_description
    if brand is not None:
        data["brand"] = brand
    if attributes is not None:
        data["attributes"] = attributes
    
    return make_request("PUT", f"/products/{product_id}", json_data=data)


@mcp.tool()
def delete_product(product_id: int) -> dict:
    """
    Delete a product.
    
    Args:
        product_id: The product ID
    
    Returns:
        Success confirmation
    """
    return make_request("DELETE", f"/products/{product_id}")


# ============================================================================
# PRODUCT VARIANTS
# ============================================================================

@mcp.tool()
def list_product_variants(
    product_id: int,
    since_id: Optional[int] = None,
    created_at_min: Optional[str] = None,
    created_at_max: Optional[str] = None,
    updated_at_min: Optional[str] = None,
    updated_at_max: Optional[str] = None,
    fields: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    List all variants for a specific product.
    
    Args:
        product_id: The product ID (required)
        since_id: Show variants after this ID
        created_at_min: Show variants created after date (ISO 8601)
        created_at_max: Show variants created before date (ISO 8601)
        updated_at_min: Show variants updated after date (ISO 8601)
        updated_at_max: Show variants updated before date (ISO 8601)
        fields: Comma-separated fields to include
    
    Returns:
        List of variants with:
        - price, promotional_price
        - stock, stock_management
        - dimensions (weight, width, height, depth)
        - sku, barcode, mpn
        - age_group, gender
        - cost
        - values (attribute values)
    
    Note:
        Products can have up to 1,000 variants
    """
    params = {}
    
    if since_id:
        params["since_id"] = since_id
    if created_at_min:
        params["created_at_min"] = created_at_min
    if created_at_max:
        params["created_at_max"] = created_at_max
    if updated_at_min:
        params["updated_at_min"] = updated_at_min
    if updated_at_max:
        params["updated_at_max"] = updated_at_max
    if fields:
        params["fields"] = fields
    
    return make_request("GET", f"/products/{product_id}/variants", params=params)


@mcp.tool()
def get_product_variant(product_id: int, variant_id: int, fields: Optional[str] = None) -> dict:
    """
    Get a single product variant by ID.
    
    Args:
        product_id: The product ID
        variant_id: The variant ID
        fields: Comma-separated fields to include
    
    Returns:
        Variant details including all properties
    """
    params = {}
    if fields:
        params["fields"] = fields
    
    return make_request("GET", f"/products/{product_id}/variants/{variant_id}", params=params)


@mcp.tool()
def create_product_variant(
    product_id: int,
    values: list[dict],
    price: Optional[str] = None,
    promotional_price: Optional[str] = None,
    stock: Optional[int] = None,
    sku: Optional[str] = None,
    barcode: Optional[str] = None,
    mpn: Optional[str] = None,
    weight: Optional[str] = None,
    width: Optional[str] = None,
    height: Optional[str] = None,
    depth: Optional[str] = None,
    cost: Optional[str] = None,
    age_group: Optional[str] = None,
    gender: Optional[str] = None,
    image_id: Optional[int] = None
) -> dict:
    """
    Create a new variant for a product.
    
    Args:
        product_id: The product ID (required)
        values: List of attribute values (required)
            Example: [{"en": "Large"}, {"en": "Red"}]
            Must match product's attributes count and order
        price: Variant price as string (e.g., "29.99", null for contact-only)
        promotional_price: Sale price (shown as crossed-out comparison)
        stock: Stock quantity (omit or "" for unlimited)
        sku: Stock keeping unit (unique identifier)
        barcode: Barcode (GTIN, EAN, ISBN, etc.)
        mpn: Manufacturer Part Number
        weight: Weight in kg as string
        width: Width in cm as string
        height: Height in cm as string
        depth: Depth in cm as string
        cost: Cost price as string (must be > 0)
        age_group: Demographic ("newborn", "infant", "toddler", "kids", "adult")
        gender: Gender ("female", "male", "unisex")
        image_id: ID of product image to associate with variant
    
    Returns:
        Created variant details
    
    Errors:
        - 422: Variants cannot be repeated
        - 422: Product not allowed to have more than 1000 variants
        - 422: Invalid age_group or gender
    
    Important:
        - Variant values combination must be unique
        - Values list must match product's attributes count
        - stock_management is automatic (cannot be set manually)
        - Max 1,000 variants per product
    """
    data = {"values": values}
    
    if price is not None:
        data["price"] = price
    if promotional_price is not None:
        data["promotional_price"] = promotional_price
    if stock is not None:
        data["stock"] = stock
    if sku:
        data["sku"] = sku
    if barcode:
        data["barcode"] = barcode
    if mpn:
        data["mpn"] = mpn
    if weight:
        data["weight"] = weight
    if width:
        data["width"] = width
    if height:
        data["height"] = height
    if depth:
        data["depth"] = depth
    if cost:
        data["cost"] = cost
    if age_group:
        data["age_group"] = age_group
    if gender:
        data["gender"] = gender
    if image_id:
        data["image_id"] = image_id
    
    return make_request("POST", f"/products/{product_id}/variants", json_data=data)


@mcp.tool()
def update_product_variant(
    product_id: int,
    variant_id: int,
    values: Optional[list[dict]] = None,
    price: Optional[str] = None,
    promotional_price: Optional[str] = None,
    stock: Optional[int] = None,
    sku: Optional[str] = None,
    barcode: Optional[str] = None,
    mpn: Optional[str] = None,
    weight: Optional[str] = None,
    width: Optional[str] = None,
    height: Optional[str] = None,
    depth: Optional[str] = None,
    cost: Optional[str] = None,
    age_group: Optional[str] = None,
    gender: Optional[str] = None,
    image_id: Optional[int] = None
) -> dict:
    """
    Update an existing product variant.
    
    Args:
        product_id: The product ID
        variant_id: The variant ID
        values: New attribute values
        price: New price
        promotional_price: New promotional price
        stock: New stock (use "" for unlimited)
        sku: New SKU
        barcode: New barcode
        mpn: New MPN
        weight: New weight in kg
        width: New width in cm
        height: New height in cm
        depth: New depth in cm
        cost: New cost price
        age_group: New age group
        gender: New gender
        image_id: New image ID
    
    Returns:
        Updated variant details
    
    Note:
        Only provided fields will be updated. Omitted fields remain unchanged.
        To set unlimited stock, use stock=""
    """
    data = {}
    
    if values is not None:
        data["values"] = values
    if price is not None:
        data["price"] = price
    if promotional_price is not None:
        data["promotional_price"] = promotional_price
    if stock is not None:
        data["stock"] = stock
    if sku is not None:
        data["sku"] = sku
    if barcode is not None:
        data["barcode"] = barcode
    if mpn is not None:
        data["mpn"] = mpn
    if weight is not None:
        data["weight"] = weight
    if width is not None:
        data["width"] = width
    if height is not None:
        data["height"] = height
    if depth is not None:
        data["depth"] = depth
    if cost is not None:
        data["cost"] = cost
    if age_group is not None:
        data["age_group"] = age_group
    if gender is not None:
        data["gender"] = gender
    if image_id is not None:
        data["image_id"] = image_id
    
    return make_request("PUT", f"/products/{product_id}/variants/{variant_id}", json_data=data)


@mcp.tool()
def replace_all_product_variants(product_id: int, variants: list[dict]) -> dict:
    """
    Replace entire variant collection for a product (batch operation).
    
    This is a destructive operation that:
    - Creates new variants for value combinations that don't exist
    - Updates existing variants that match value combinations
    - DELETES variants not included in the request
    
    Args:
        product_id: The product ID
        variants: List of variants, each with:
            - values (required): List of attribute values
            - price, promotional_price, stock, sku, etc. (optional)
    
    Returns:
        Complete updated variant collection
    
    Example:
        replace_all_product_variants(
            product_id=1234,
            variants=[
                {
                    "values": [{"en": "Small"}],
                    "price": "19.99",
                    "stock": 10
                },
                {
                    "values": [{"en": "Large"}],
                    "price": "24.99",
                    "stock": 5
                }
            ]
        )
    
    Errors:
        - 400: Invalid input format, empty values, or missing variants
        - 422: Validation error, repeated values, or > 1000 variants
    
    Warning:
        This operation DELETES variants not included in the request!
        Use update_product_variant() for individual updates.
    """
    return make_request("PUT", f"/products/{product_id}/variants", json_data=variants)


@mcp.tool()
def batch_update_product_variants(product_id: int, variants: list[dict]) -> dict:
    """
    Partially update multiple variants (non-destructive batch operation).
    
    This operation:
    - Updates only the variants specified
    - Does NOT create new variants
    - Does NOT delete existing variants
    
    Args:
        product_id: The product ID
        variants: List of variants to update, each MUST include:
            - id (required): Variant ID
            - values: New attribute values (must be unique)
            - Other fields to update (price, stock, sku, etc.)
    
    Returns:
        Complete updated variant collection
    
    Example:
        batch_update_product_variants(
            product_id=1234,
            variants=[
                {
                    "id": 143,
                    "price": "19.99",
                    "stock": 20
                },
                {
                    "id": 144,
                    "price": "24.99",
                    "stock": 15
                }
            ]
        )
    
    Preconditions:
        - Each variant must include the 'id' field
        - Each variant ID must exist for this product
        - Each variant must belong to this product
        - Value combinations must be unique
    
    Errors:
        - 404: Product not found
        - 422: Variants cannot be repeated (includes duplicate_variant_ids)
        - 422: Variant doesn't exist or doesn't belong to product
    
    Note:
        This is safer than replace_all_product_variants() as it won't delete variants.
    """
    return make_request("PATCH", f"/products/{product_id}/variants", json_data=variants)


@mcp.tool()
def delete_product_variant(product_id: int, variant_id: int) -> dict:
    """
    Delete a product variant.
    
    Args:
        product_id: The product ID
        variant_id: The variant ID to delete
    
    Returns:
        Success confirmation
    
    Warning:
        This permanently deletes the variant. Consider updating stock to 0 instead.
    """
    return make_request("DELETE", f"/products/{product_id}/variants/{variant_id}")


@mcp.tool()
def update_variant_stock(
    product_id: int,
    action: str,
    value: Optional[int] = None,
    variant_id: Optional[int] = None
) -> dict:
    """
    Update stock for one or all variants of a product.
    
    Args:
        product_id: The product ID (required)
        action: Type of update (required)
            - "replace": Replace current stock with new value
            - "variation": Add/subtract from current stock
        value: Stock value (required)
            For "replace":
                - Positive number: Set to that stock
                - 0: Set to stockout
                - null: Set to unlimited/infinite stock
            For "variation":
                - Positive number: Add to current stock
                - Negative number: Remove from current stock
        variant_id: Specific variant ID (optional)
            - If provided: Only update this variant
            - If omitted: Update ALL variants of this product
    
    Returns:
        List of all updated variants
    
    Examples:
        # Set all variants to 10 units
        update_variant_stock(1234, "replace", 10)
        
        # Set specific variant to unlimited stock
        update_variant_stock(1234, "replace", None, variant_id=143)
        
        # Add 5 units to specific variant
        update_variant_stock(1234, "variation", 5, variant_id=144)
        
        # Remove 3 units from all variants
        update_variant_stock(1234, "variation", -3)
    
    Note:
        - Removing more stock than available results in stock of 0 (not an error)
        - Use value=None with action="replace" for unlimited stock
    
    Errors:
        - 404: Product not found
        - 422: Invalid action (must be 'replace' or 'variation')
    """
    data = {
        "action": action,
        "value": value
    }
    
    if variant_id is not None:
        data["id"] = variant_id
    
    return make_request("POST", f"/products/{product_id}/variants/stock", json_data=data)


@mcp.tool()
def set_variant_extra_shipping_days(
    variant_id: int,
    additional_days: int
) -> dict:
    """
    Set extra shipping days for a product variant (using Metafields).
    
    For products that need extra days for manufacturing or preparation,
    this sets additional days to be considered in shipment calculations.
    
    Args:
        variant_id: The product variant ID
        additional_days: Number of extra days (e.g., 5)
    
    Returns:
        Created metafield details
    
    Note:
        The key MUST be "additional_days" for the system to recognize it.
        This uses the Metafields API with specific namespace and key.
    """
    data = {
        "key": "additional_days",
        "value": str(additional_days),
        "namespace": "shipping_rules",
        "owner_id": variant_id,
        "owner_resource": "Product_Variant"
    }

    return make_request("POST", "/metafields", json_data=data)

@mcp.tool()
def update_product_stock_price(updates: list[dict]) -> dict:
    """
    Update stock and/or price for multiple product variants at once.
    Max 50 variants can be updated at once.
    
    Args:
        updates: List of update objects, each with:
            - id: product_id
            - variants: list of variant updates with:
                - id: variant_id
                - price: new price (optional)
                - inventory_levels: [{"stock": quantity}] (optional)
    
    Example:
        [
            {
                "id": 12345,
                "variants": [
                    {
                        "id": 67890,
                        "price": 1000,
                        "inventory_levels": [{"stock": 300}]
                    }
                ]
            }
        ]
    
    Returns:
        Update results for each variant
    """
    return make_request("PATCH", "/products/stock-price", json_data=updates)


# ============================================================================
# ORDERS
# ============================================================================

@mcp.tool()
def list_orders(
    page: int = 1,
    per_page: int = 30,
    since_id: Optional[int] = None,
    status: Optional[str] = None,
    channels: Optional[str] = None,
    payment_status: Optional[str] = None,
    shipping_status: Optional[str] = None,
    created_at_min: Optional[str] = None,
    created_at_max: Optional[str] = None,
    updated_at_min: Optional[str] = None,
    updated_at_max: Optional[str] = None,
    fields: Optional[str] = None,
    aggregates: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    List all orders. Use webhooks for real-time updates instead of frequent polling.
    
    Args:
        page: Page number
        per_page: Results per page (max: 200)
        since_id: Show orders after this ID
        status: Filter by order status ("any", "open", "closed", "cancelled")
        channels: Filter by sales channel ("form", "store", "api", "meli", "pos")
        payment_status: Filter by payment status ("any", "pending", "authorized", 
                       "paid", "abandoned", "refunded", "voided")
        shipping_status: Filter by shipping status ("any", "unpacked", "unfulfilled", "fulfilled")
        created_at_min: Show orders created after date (ISO 8601)
        created_at_max: Show orders created before date (ISO 8601)
        updated_at_min: Show orders updated after date (ISO 8601)
        updated_at_max: Show orders updated before date (ISO 8601)
        fields: Comma-separated fields to include (e.g., "id,number,total")
        aggregates: Include "fulfillment_orders" for complete fulfillment details
    
    Returns:
        List of orders with customer, products, shipping, and payment details
    
    Best Practices:
        - Use webhooks (order/created, order/paid, order/packed) instead of polling
        - Import by period using created_at_min/max to avoid unnecessary calls
        - Use specific fields parameter to reduce payload size
    """
    params = {"page": page, "per_page": min(per_page, 200)}
    
    if since_id:
        params["since_id"] = since_id
    if status:
        params["status"] = status
    if channels:
        params["channels"] = channels
    if payment_status:
        params["payment_status"] = payment_status
    if shipping_status:
        params["shipping_status"] = shipping_status
    if created_at_min:
        params["created_at_min"] = created_at_min
    if created_at_max:
        params["created_at_max"] = created_at_max
    if updated_at_min:
        params["updated_at_min"] = updated_at_min
    if updated_at_max:
        params["updated_at_max"] = updated_at_max
    if fields:
        params["fields"] = fields
    if aggregates:
        params["aggregates"] = aggregates
    
    return make_request("GET", "/orders", params=params)


@mcp.tool()
def get_order(order_id: int, fields: Optional[str] = None, aggregates: Optional[str] = None) -> dict:
    """
    Get a single order by ID.
    
    Args:
        order_id: The order ID
        fields: Comma-separated fields to include
        aggregates: Include "fulfillment_orders" for complete fulfillment details
    
    Returns:
        Complete order details including:
        - Customer information
        - Products list with variants, prices, and images
        - Billing and shipping addresses
        - Payment details (method, installments, gateway)
        - Shipping information and status
        - Discounts and coupons
        - Fulfillment orders (if aggregates="fulfillment_orders")
    """
    params = {}
    if fields:
        params["fields"] = fields
    if aggregates:
        params["aggregates"] = aggregates
    
    return make_request("GET", f"/orders/{order_id}", params=params)


@mcp.tool()
def get_order_history_values(order_id: int) -> dict:
    """
    Get all order total value alterations (edits and refunds).
    
    Args:
        order_id: The order ID
    
    Returns:
        List of value changes with:
        - status: PENDING, CANCELLED, or PAID
        - total_delta: Difference from previous value
        - total_paid_diff: Amount paid/refunded (non-zero only if PAID)
        - gateway_method: Payment method (credit_card, debit_card, cash, wire_transfer, pix, other)
        - gateway_name: Custom gateway name (if method is "other")
        - closed_at: When transaction reached final state
        - happened_at: When modification occurred
    """
    return make_request("GET", f"/orders/{order_id}/history/values")


@mcp.tool()
def get_order_history_editions(order_id: int) -> dict:
    """
    Get all order editions changelog.
    
    Args:
        order_id: The order ID
    
    Returns:
        List of editions with:
        - product_changes: Products added/removed with quantities
        - shipping_costs: Shipping cost changes per fulfillment
        - transaction_information: Related payment transaction
        - reason: Reason for the edition
        - happened_at: When edition occurred
    """
    return make_request("GET", f"/orders/{order_id}/history/editions")


@mcp.tool()
def create_order(
    products: list[dict],
    customer: dict,
    billing_address: Optional[dict] = None,
    shipping_address: Optional[dict] = None,
    currency: str = "USD",
    language: str = "en",
    gateway: str = "not-provided",
    payment_status: str = "pending",
    status: str = "open",
    shipping_status: str = "unpacked",
    shipping_pickup_type: str = "pickup",
    shipping_store_branch_name: Optional[str] = None,
    shipping_min_delivery_date: Optional[str] = None,
    shipping_max_delivery_date: Optional[str] = None,
    shipping_tracking_number: Optional[str] = None,
    shipping_tracking_url: Optional[str] = None,
    shipping_cost_owner: Optional[str] = None,
    shipping_cost_customer: Optional[str] = None,
    note: Optional[str] = None,
    owner_note: Optional[str] = None,
    inventory_behaviour: str = "bypass",
    discount_coupon: Optional[str] = None,
    extra: Optional[dict] = None
) -> dict:
    """
    Create a new order via API.
    
    Args:
        products: List of products, each with:
            - variant_id (required): Product variant ID
            - quantity (required): Quantity
            - price (optional): Custom price (defaults to variant price)
        customer: Customer object with:
            - name: Customer name (required)
            - email: Customer email (required)
            - phone: Phone number (optional)
            - document: Document/ID number (optional)
        billing_address: Billing address with:
            - first_name, last_name, address, number, city, province, zipcode, country (required)
            - floor, locality (optional)
        shipping_address: Shipping address (same structure as billing_address)
        currency: Currency code (ISO 4217, e.g., "USD", "BRL", "ARS")
        language: Language code (ISO 639-1, e.g., "en", "es", "pt")
        gateway: Payment gateway ("offline", "mercadopago", "pagseguro", "payu", "not-provided")
        payment_status: Payment status ("pending", "authorized", "paid", "voided", "refunded", "abandoned")
        status: Order status ("open", "closed", "cancelled")
        shipping_status: Shipping status ("unpacked", "unfulfilled", "fulfilled")
        shipping_pickup_type: Shipping type ("ship", "pickup")
        shipping_store_branch_name: Branch name for pickup orders
        shipping_min_delivery_date: Min delivery date (ISO 8601)
        shipping_max_delivery_date: Max delivery date (ISO 8601)
        shipping_tracking_number: Tracking number
        shipping_tracking_url: Tracking URL
        shipping_cost_owner: Merchant shipping cost
        shipping_cost_customer: Customer shipping cost
        note: Customer note
        owner_note: Merchant note (visible to merchant only)
        inventory_behaviour: "bypass" (don't claim stock) or "claim" (reserve stock)
        discount_coupon: Coupon code
        extra: Custom fields as JSON object
    
    Returns:
        Created order with full details
    
    Example:
        create_order(
            products=[{"variant_id": 123456, "quantity": 2, "price": "29.99"}],
            customer={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            payment_status="paid",
            owner_note="Gift wrap requested"
        )
    
    Note:
        - Orders created via API have storefront="api"
        - Use owner_note for payment processor details (external_id, external_url)
        - Transactions won't be automatically created for API orders
    """
    data = {
        "products": products,
        "customer": customer,
        "currency": currency,
        "language": language,
        "gateway": gateway,
        "payment_status": payment_status,
        "status": status,
        "shipping_status": shipping_status,
        "shipping_pickup_type": shipping_pickup_type,
        "inventory_behaviour": inventory_behaviour
    }
    
    if billing_address:
        data["billing_address"] = billing_address
    if shipping_address:
        data["shipping_address"] = shipping_address
    if shipping_store_branch_name:
        data["shipping_store_branch_name"] = shipping_store_branch_name
    if shipping_min_delivery_date:
        data["shipping_min_delivery_date"] = shipping_min_delivery_date
    if shipping_max_delivery_date:
        data["shipping_max_delivery_date"] = shipping_max_delivery_date
    if shipping_tracking_number:
        data["shipping_tracking_number"] = shipping_tracking_number
    if shipping_tracking_url:
        data["shipping_tracking_url"] = shipping_tracking_url
    if shipping_cost_owner:
        data["shipping_cost_owner"] = shipping_cost_owner
    if shipping_cost_customer:
        data["shipping_cost_customer"] = shipping_cost_customer
    if note:
        data["note"] = note
    if owner_note:
        data["owner_note"] = owner_note
    if discount_coupon:
        data["discount_coupon"] = discount_coupon
    if extra:
        data["extra"] = extra
    
    return make_request("POST", "/orders", json_data=data)


@mcp.tool()
def update_order(order_id: int, owner_note: Optional[str] = None, status: Optional[str] = None) -> dict:
    """
    Update order attributes (currently only owner_note and status).
    
    Args:
        order_id: The order ID
        owner_note: Merchant's internal note (visible to merchant only)
        status: Order status ("open", "closed", "cancelled")
    
    Returns:
        Updated order details
    
    Note:
        Use specific endpoints for other actions:
        - close_order() to close an order
        - open_order() to reopen a closed order
        - cancel_order() to cancel an order
    """
    data = {}
    
    if owner_note is not None:
        data["owner_note"] = owner_note
    if status is not None:
        data["status"] = status
    
    return make_request("PUT", f"/orders/{order_id}", json_data=data)


@mcp.tool()
def close_order(order_id: int) -> dict:
    """
    Close an order (mark as completed).
    
    Args:
        order_id: The order ID
    
    Returns:
        Updated order with status="closed" and closed_at timestamp
    """
    return make_request("POST", f"/orders/{order_id}/close")


@mcp.tool()
def open_order(order_id: int) -> dict:
    """
    Reopen a closed order.
    
    Args:
        order_id: The order ID
    
    Returns:
        Updated order with status="open" and closed_at=null
    """
    return make_request("POST", f"/orders/{order_id}/open")


@mcp.tool()
def cancel_order(
    order_id: int,
    reason: str = "other",
    send_email: bool = True,
    restock: bool = True
) -> dict:
    """
    Cancel an order.
    
    Args:
        order_id: The order ID
        reason: Cancellation reason ("customer", "inventory", "fraud", "other")
        send_email: Notify customer via email (default: True)
        restock: Return products to inventory (default: True)
    
    Returns:
        Updated order with status="cancelled" and cancellation details
    """
    data = {
        "reason": reason,
        "send_email": send_email,
        "restock": restock
    }
    
    return make_request("POST", f"/orders/{order_id}/cancel", json_data=data)


# ============================================================================
# CUSTOMERS
# ============================================================================

@mcp.tool()
def list_customers(
    page: int = 1,
    per_page: int = 30,
    since_id: Optional[int] = None,
    created_at_min: Optional[str] = None,
    created_at_max: Optional[str] = None,
    updated_at_min: Optional[str] = None,
    updated_at_max: Optional[str] = None,
    query: Optional[str] = None,
    ids: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    List all customers.
    
    Args:
        page: Page number
        per_page: Results per page (max: 200)
        since_id: Show customers after this ID
        created_at_min: Show customers created after date (ISO 8601)
        created_at_max: Show customers created before date (ISO 8601)
        updated_at_min: Show customers updated after date (ISO 8601)
        updated_at_max: Show customers updated before date (ISO 8601)
        query: Search customers by name or email
        ids: Comma-separated customer IDs to filter
    
    Returns:
        List of customers with addresses, billing info, and extra fields
    """
    params = {"page": page, "per_page": min(per_page, 200)}
    
    if since_id:
        params["since_id"] = since_id
    if created_at_min:
        params["created_at_min"] = created_at_min
    if created_at_max:
        params["created_at_max"] = created_at_max
    if updated_at_min:
        params["updated_at_min"] = updated_at_min
    if updated_at_max:
        params["updated_at_max"] = updated_at_max
    if query:
        params["q"] = query
    if ids:
        params["ids"] = ids
    
    return make_request("GET", "/customers", params=params)


@mcp.tool()
def get_customer(customer_id: int, fields: Optional[str] = None) -> dict:
    """
    Get a single customer by ID.
    
    Args:
        customer_id: The customer ID
        fields: Comma-separated list of fields to include (e.g., "id,name,email")
    
    Returns:
        Customer details including:
        - Personal info (name, email, phone, identification)
        - Addresses (default_address and addresses list)
        - Billing information (address, city, province, country, zipcode, etc.)
        - Extra custom fields
        - Total spent and currency
        - Last order ID
    """
    params = {}
    if fields:
        params["fields"] = fields
    
    return make_request("GET", f"/customers/{customer_id}", params=params)


@mcp.tool()
def create_customer(
    email: str,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    identification: Optional[str] = None,
    note: Optional[str] = None,
    addresses: Optional[list] = None,
    billing_address: Optional[str] = None,
    billing_number: Optional[str] = None,
    billing_floor: Optional[str] = None,
    billing_locality: Optional[str] = None,
    billing_zipcode: Optional[str] = None,
    billing_city: Optional[str] = None,
    billing_province: Optional[str] = None,
    billing_country: Optional[str] = None,
    billing_phone: Optional[str] = None,
    extra: Optional[dict] = None,
    send_email_invite: bool = False,
    password: Optional[str] = None
) -> dict:
    """
    Create a new customer.
    
    Args:
        email: Customer email (required)
        name: Customer name
        phone: Customer phone number
        identification: Customer identification/tax ID (CPF/CNPJ in Brazil)
        note: Store owner's notes about the customer
        addresses: List of shipping addresses. Each address should include:
            - address: Street address
            - number: Street number
            - floor: Floor/apartment (optional)
            - locality: Locality/neighborhood (optional)
            - city: City
            - province: State/province
            - country: Country code (e.g., "BR", "US")
            - zipcode: Postal code
            - phone: Phone number
        billing_address: Billing street address
        billing_number: Billing street number
        billing_floor: Billing floor/apartment
        billing_locality: Billing locality/neighborhood
        billing_zipcode: Billing postal code
        billing_city: Billing city
        billing_province: Billing state/province
        billing_country: Billing country code
        billing_phone: Billing phone number
        extra: JSON object with custom fields (e.g., {"gender": "male", "age": "30"})
        send_email_invite: Send email to notify customer of registration
        password: Customer password for account creation
    
    Returns:
        Created customer details with full address information
    
    Example:
        create_customer(
            email="customer@example.com",
            name="John Doe",
            phone="+55 11 9 1234-5678",
            addresses=[{
                "address": "Main Street",
                "number": "123",
                "city": "São Paulo",
                "province": "São Paulo",
                "country": "BR",
                "zipcode": "01234-567",
                "phone": "+55 11 9 1234-5678"
            }],
            extra={"customer_type": "vip"}
        )
    """
    data = {"email": email}
    
    if name:
        data["name"] = name
    if phone:
        data["phone"] = phone
    if identification:
        data["identification"] = identification
    if note:
        data["note"] = note
    if addresses:
        data["addresses"] = addresses
    
    # Billing information
    if billing_address:
        data["billing_address"] = billing_address
    if billing_number:
        data["billing_number"] = billing_number
    if billing_floor:
        data["billing_floor"] = billing_floor
    if billing_locality:
        data["billing_locality"] = billing_locality
    if billing_zipcode:
        data["billing_zipcode"] = billing_zipcode
    if billing_city:
        data["billing_city"] = billing_city
    if billing_province:
        data["billing_province"] = billing_province
    if billing_country:
        data["billing_country"] = billing_country
    if billing_phone:
        data["billing_phone"] = billing_phone
    
    if extra:
        data["extra"] = extra
    if send_email_invite:
        data["send_email_invite"] = send_email_invite
    if password:
        data["password"] = password
    
    return make_request("POST", "/customers", json_data=data)


@mcp.tool()
def update_customer(
    customer_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    identification: Optional[str] = None,
    note: Optional[str] = None,
    addresses: Optional[list] = None,
    billing_address: Optional[str] = None,
    billing_number: Optional[str] = None,
    billing_floor: Optional[str] = None,
    billing_locality: Optional[str] = None,
    billing_zipcode: Optional[str] = None,
    billing_city: Optional[str] = None,
    billing_province: Optional[str] = None,
    billing_country: Optional[str] = None,
    billing_phone: Optional[str] = None,
    extra: Optional[dict] = None
) -> dict:
    """
    Update an existing customer.
    
    Args:
        customer_id: The customer ID
        name: Customer name
        email: Customer email
        phone: Customer phone number
        identification: Customer identification/tax ID
        note: Store owner's notes
        addresses: List of shipping addresses (will replace existing addresses)
        billing_address: Billing street address
        billing_number: Billing street number
        billing_floor: Billing floor/apartment
        billing_locality: Billing locality/neighborhood
        billing_zipcode: Billing postal code
        billing_city: Billing city
        billing_province: Billing state/province
        billing_country: Billing country code
        billing_phone: Billing phone number
        extra: Custom fields as JSON object
    
    Returns:
        Updated customer details
    
    Note:
        Only provided fields will be updated. Omitted fields remain unchanged.
    """
    data = {}
    
    if name is not None:
        data["name"] = name
    if email is not None:
        data["email"] = email
    if phone is not None:
        data["phone"] = phone
    if identification is not None:
        data["identification"] = identification
    if note is not None:
        data["note"] = note
    if addresses is not None:
        data["addresses"] = addresses
    
    # Billing information
    if billing_address is not None:
        data["billing_address"] = billing_address
    if billing_number is not None:
        data["billing_number"] = billing_number
    if billing_floor is not None:
        data["billing_floor"] = billing_floor
    if billing_locality is not None:
        data["billing_locality"] = billing_locality
    if billing_zipcode is not None:
        data["billing_zipcode"] = billing_zipcode
    if billing_city is not None:
        data["billing_city"] = billing_city
    if billing_province is not None:
        data["billing_province"] = billing_province
    if billing_country is not None:
        data["billing_country"] = billing_country
    if billing_phone is not None:
        data["billing_phone"] = billing_phone
    
    if extra is not None:
        data["extra"] = extra
    
    return make_request("PUT", f"/customers/{customer_id}", json_data=data)


@mcp.tool()
def delete_customer(customer_id: int) -> dict:
    """
    Delete a customer.
    
    Args:
        customer_id: The customer ID
    
    Returns:
        Success confirmation
    
    Important:
        Cannot delete customers with associated orders.
        Will return 422 error if customer has orders.
    """
    return make_request("DELETE", f"/customers/{customer_id}")


# ============================================================================
# CATEGORIES
# ============================================================================

@mcp.tool()
def list_categories(page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
    """
    List all categories.
    
    Args:
        page: Page number
        per_page: Results per page (max: 200)
    
    Returns:
        List of categories
    """
    params = {"page": page, "per_page": min(per_page, 200)}
    return make_request("GET", "/categories", params=params)


@mcp.tool()
def get_category(category_id: int) -> dict:
    """
    Get a single category by ID.
    
    Args:
        category_id: The category ID
    
    Returns:
        Category details
    """
    return make_request("GET", f"/categories/{category_id}")


@mcp.tool()
def create_category(
    name: dict,
    description: Optional[dict] = None,
    parent_id: Optional[int] = None,
    handle: Optional[dict] = None
) -> dict:
    """
    Create a new category.
    
    Args:
        name: Category name in multiple languages, e.g., {"en": "Electronics", "es": "Electrónica"}
        description: Category description in multiple languages
        parent_id: Parent category ID (for subcategories)
        handle: URL-friendly identifier in multiple languages
    
    Returns:
        Created category details
    """
    data = {"name": name}
    
    if description:
        data["description"] = description
    if parent_id:
        data["parent"] = parent_id
    if handle:
        data["handle"] = handle
    
    return make_request("POST", "/categories", json_data=data)


@mcp.tool()
def update_category(
    category_id: int,
    name: Optional[dict] = None,
    description: Optional[dict] = None,
    parent_id: Optional[int] = None
) -> dict:
    """
    Update an existing category.
    
    Args:
        category_id: The category ID
        name: Category name in multiple languages
        description: Category description in multiple languages
        parent_id: Parent category ID
    
    Returns:
        Updated category details
    """
    data = {}
    
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if parent_id is not None:
        data["parent"] = parent_id
    
    return make_request("PUT", f"/categories/{category_id}", json_data=data)


@mcp.tool()
def delete_category(category_id: int) -> dict:
    """
    Delete a category.
    
    Args:
        category_id: The category ID
    
    Returns:
        Success confirmation
    """
    return make_request("DELETE", f"/categories/{category_id}")


# ============================================================================
# BILLING
# ============================================================================

@mcp.tool()
def create_billing_plan(
    code: str,
    external_reference: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Create a new billing plan for your service.
    
    IMPORTANT: This uses Partner-Action authentication method.
    Requires special partner credentials and permissions.
    
    Args:
        code: Currency code for the plan (e.g., "USD", "BRL", "ARS")
        external_reference: Optional ID for your own reference system
        description: Short description of the plan
    
    Returns:
        Created plan with:
        - id: Tiendanube's plan UUID
        - code: Currency code
        - external_reference: Your reference ID
        - description: Plan description
        - default: Whether this is the default plan
    
    Use Cases:
        - Create different pricing tiers (Basic, Pro, Enterprise)
        - Set up multi-currency pricing
        - Manage service levels
    
    Note:
        Plans are used to generate automatic periodic charges via subscriptions.
        Each merchant subscription will use a plan to determine pricing.
    
    Errors:
        - 404: Business Unit or Service not found
        - 400: Duplicated external_reference for this service
    """
    data = {"code": code}
    
    if external_reference:
        data["external_reference"] = external_reference
    if description:
        data["description"] = description
    
    return make_request("POST", "/plans", json_data=data)


@mcp.tool()
def update_billing_plan(
    plan_id: str,
    code: Optional[str] = None,
    external_reference: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update an existing billing plan.
    
    CRITICAL WARNING: Updating a plan will modify:
    - ALL subscriptions using this plan
    - ALL unpaid or pending charges for this plan
    
    Args:
        plan_id: Plan ID or your external_reference
        code: New currency code
        external_reference: New external reference ID
        description: New description
    
    Returns:
        Updated plan details
    
    Important:
        Use this carefully as it affects all active subscriptions.
        Consider creating a new plan instead of updating existing ones
        when making major pricing changes.
    
    Errors:
        - 404: Business Unit, Service, or Plan not found
    """
    data = {}
    
    if code:
        data["code"] = code
    if external_reference:
        data["external_reference"] = external_reference
    if description:
        data["description"] = description
    
    return make_request("PATCH", f"/plans/{plan_id}", json_data=data)


@mcp.tool()
def delete_billing_plan(plan_id: str) -> dict:
    """
    Delete a billing plan.
    
    CRITICAL WARNING: Deleting a plan will:
    - DELETE all subscriptions using this plan
    - DELETE all unpaid or pending charges for this plan
    
    Args:
        plan_id: Plan ID or your external_reference
    
    Returns:
        Success confirmation
    
    Important:
        This is a destructive operation. Ensure no active merchants
        are using this plan before deleting.
        Cannot delete the default plan.
    
    Errors:
        - 404: Business Unit, Service, or Plan not found
        - 400: Cannot delete default plan
    """
    return make_request("DELETE", f"/plans/{plan_id}")


@mcp.tool()
def get_subscription(concept_code: str, service_id: str) -> dict:
    """
    Get subscription details for a specific merchant/store.
    
    Args:
        concept_code: Concept code of the subscription
        service_id: Service ID (if app, use app_id)
    
    Returns:
        Subscription with:
        - external_reference: Your reference ID
        - description: Subscription description
        - recurring_frequency: Billing frequency (e.g., "monthly")
        - recurring_interval: Interval number
        - amount_currency: Currency code
        - amount_value: Subscription price
        - concept_code: Subscription concept
        - store_id: Merchant's store ID
        - next_execution: Date of next automatic charge
        - last_execution: Date of last charge
        - plan: Associated plan details (id, code)
    
    Important Fields:
        - next_execution: When the next charge will be created automatically.
                         This marks the start of the next billing period.
    
    Billing Cycle:
        Subscriptions align to the 16th of each month:
        - Install on 2nd: Next charge covers 2nd-16th (prorated)
        - Install on 20th: Next charge covers 20th-16th next month (prorated)
        - Install on 16th: Next charge covers full month (16th-16th)
    
    Errors:
        - 404: Store or Subscription not found
    """
    return make_request("GET", f"/concepts/{concept_code}/services/{service_id}/subscriptions")


@mcp.tool()
def update_subscription(
    concept_code: str,
    service_id: str,
    amount_currency: Optional[str] = None,
    amount_value: Optional[float] = None,
    plan_id: Optional[str] = None,
    plan_external_id: Optional[str] = None
) -> dict:
    """
    Update subscription details (change plan, pricing, etc.).
    
    IMPORTANT: Updating subscription price will update all unpaid
    or pending charges for this subscription.
    
    Args:
        concept_code: Concept code of the subscription
        service_id: Service ID (if app, use app_id)
        amount_currency: New currency code
        amount_value: New subscription price
        plan_id: New plan UUID to switch to
        plan_external_id: Partner's plan ID to switch to
    
    Returns:
        Updated subscription details
    
    Use Cases:
        - Switch merchant to different plan tier
        - Apply special pricing for specific merchant
        - Change currency
        - Upgrade/downgrade service level
    
    Example:
        # Upgrade merchant to Pro plan
        update_subscription(
            concept_code="service-fee",
            service_id="app_123",
            plan_id="pro-plan-uuid",
            amount_value=49.99
        )
    
    Errors:
        - 404: Store or Subscription not found
        - 400: Invalid currency for store
    """
    data = {}
    
    if amount_currency:
        data["amount_currency"] = amount_currency
    if amount_value is not None:
        data["amount_value"] = amount_value
    if plan_id:
        data["plan_id"] = plan_id
    if plan_external_id:
        data["plan_external_id"] = plan_external_id
    
    return make_request("PATCH", f"/concepts/{concept_code}/services/{service_id}/subscriptions", json_data=data)


@mcp.tool()
def create_extra_charge(
    service_id: str,
    description: str,
    from_date: str,
    to_date: str,
    amount_value: float,
    amount_currency: str,
    concept_code: str,
    external_reference: Optional[str] = None
) -> dict:
    """
    Create an additional/variable charge (usage beyond fixed fee).
    
    Use this for:
    - Variable charges (usage-based billing)
    - One-time fees
    - Extra features not included in subscription
    - Overage charges
    
    Args:
        service_id: Service ID (if app, use app_id)
        description: Short description of the charge
        from_date: Start date of billing period (ISO 8601)
        to_date: End date of billing period (ISO 8601)
        amount_value: Charge amount
        amount_currency: Currency code (e.g., "USD", "BRL")
        concept_code: Concept code for this charge
        external_reference: Optional ID for your reference
    
    Returns:
        Created charge with:
        - id: Charge UUID
        - description: Charge description
        - external_reference: Your reference ID
        - from_date: Period start
        - to_date: Period end
        - amount_value: Charge amount
        - amount_currency: Currency
        - concept_code: Concept code
    
    Best Practice (RECOMMENDED):
        Create extra charges ONE DAY BEFORE the subscription's next_execution date.
        This allows merchants to see all charges together for the same billing period,
        providing a smoother payment experience.
    
    Example:
        # Charge for extra API calls
        create_extra_charge(
            service_id="app_123",
            description="Extra API calls - 10,000 requests",
            from_date="2025-10-01T00:00:00Z",
            to_date="2025-10-16T00:00:00Z",
            amount_value=15.00,
            amount_currency="USD",
            concept_code="api-usage",
            external_reference="charge-oct-2025"
        )
    
    Pricing Models:
        1. Fixed + Variable: Subscription (fixed) + Extra charges (variable)
        2. Variable only: No subscription, only extra charges via this endpoint
    
    Errors:
        - 404: Store not found
    """
    data = {
        "description": description,
        "from_date": from_date,
        "to_date": to_date,
        "amount_value": amount_value,
        "amount_currency": amount_currency,
        "concept_code": concept_code
    }
    
    if external_reference:
        data["external_reference"] = external_reference
    
    return make_request("POST", f"/services/{service_id}/charges", json_data=data)

@mcp.tool()
def get_store() -> dict:
    """
    Get store information and settings.
    
    Returns:
        Store details including name, email, domain, languages, currencies, etc.
    """
    return make_request("GET", "/store")


# ============================================================================
# COUPONS
# ============================================================================

@mcp.tool()
def list_coupons(page: int = 1, per_page: int = 30) -> list[dict[str, Any]]:
    """
    List all coupons.
    
    Args:
        page: Page number
        per_page: Results per page (max: 200)
    
    Returns:
        List of coupons
    """
    params = {"page": page, "per_page": min(per_page, 200)}
    return make_request("GET", "/coupons", params=params)


@mcp.tool()
def get_coupon(coupon_id: int) -> dict:
    """
    Get a single coupon by ID.
    
    Args:
        coupon_id: The coupon ID
    
    Returns:
        Coupon details
    """
    return make_request("GET", f"/coupons/{coupon_id}")


@mcp.tool()
def create_coupon(
    code: str,
    type_discount: str,
    value: str,
    valid_from: Optional[str] = None,
    valid_until: Optional[str] = None,
    max_uses: Optional[int] = None,
    min_price: Optional[str] = None
) -> dict:
    """
    Create a new coupon.
    
    Args:
        code: Coupon code (unique)
        type_discount: Type of discount ("percentage", "absolute")
        value: Discount value as string (e.g., "10.00" for 10% or $10)
        valid_from: Start date (ISO 8601 format)
        valid_until: End date (ISO 8601 format)
        max_uses: Maximum number of uses
        min_price: Minimum order price required
    
    Returns:
        Created coupon details
    """
    data = {
        "code": code,
        "type": type_discount,
        "value": value
    }
    
    if valid_from:
        data["valid_from"] = valid_from
    if valid_until:
        data["valid_until"] = valid_until
    if max_uses is not None:
        data["max_uses"] = max_uses
    if min_price:
        data["min_price"] = min_price
    
    return make_request("POST", "/coupons", json_data=data)


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("tiendanube://store")
def get_store_resource() -> str:
    """Get current store information as a resource"""
    store_info = get_store()
    return f"""
# Store Information

**Name**: {store_info.get('name', {}).get('en', 'N/A')}
**Email**: {store_info.get('email', 'N/A')}
**Domain**: {store_info.get('domain', 'N/A')}
**Country**: {store_info.get('country', 'N/A')}
**Currency**: {store_info.get('currency', 'N/A')}
**Languages**: {', '.join(store_info.get('languages', []))}
**Main Language**: {store_info.get('main_language', 'N/A')}
"""


@mcp.resource("tiendanube://orders/summary")
def get_orders_summary_resource() -> str:
    """Get a summary of recent orders"""
    try:
        # Get recent orders
        recent_orders = list_orders(per_page=50, status="open")
        
        if not isinstance(recent_orders, list):
            return "No orders data available"
        
        total_orders = len(recent_orders)
        pending_payment = sum(1 for o in recent_orders if o.get('payment_status') == 'pending')
        paid_orders = sum(1 for o in recent_orders if o.get('payment_status') == 'paid')
        unpacked_orders = sum(1 for o in recent_orders if o.get('shipping_status') == 'unpacked')
        
        total_value = sum(float(o.get('total', 0)) for o in recent_orders)
        currency = recent_orders[0].get('currency', 'USD') if recent_orders else 'USD'
        
        return f"""
# Recent Orders Summary (Last 50 Open Orders)

## Overview
- **Total Open Orders**: {total_orders}
- **Total Value**: {currency} {total_value:.2f}
- **Average Order Value**: {currency} {(total_value / total_orders if total_orders > 0 else 0):.2f}

## Payment Status
- **Pending Payment**: {pending_payment}
- **Paid**: {paid_orders}

## Fulfillment Status
- **Ready to Pack**: {unpacked_orders}

## Actions Needed
{f'- {pending_payment} orders waiting for payment' if pending_payment > 0 else ''}
{f'- {unpacked_orders} orders ready to be packed and shipped' if unpacked_orders > 0 else ''}
"""
    except Exception as e:
        return f"Error fetching orders summary: {str(e)}"


@mcp.resource("tiendanube://products/low-stock")
def get_low_stock_products_resource() -> str:
    """Get products with low stock (≤10 units)"""
    try:
        # Get products with stock between 1 and 10
        low_stock = list_products(min_stock=1, max_stock=10, per_page=100, published=True)
        
        if not isinstance(low_stock, list) or len(low_stock) == 0:
            return "# Low Stock Alert\n\nNo products with low stock found. All inventory levels are healthy! ✅"
        
        result = "# Low Stock Alert 🔴\n\n"
        result += f"**Total Products**: {len(low_stock)} products need attention\n\n"
        
        # Group by stock level
        critical = []  # 1-3 units
        low = []       # 4-7 units
        moderate = []  # 8-10 units
        
        for product in low_stock:
            name = product.get('name', {}).get('en') or product.get('name', {}).get('pt') or product.get('name', {}).get('es', 'Unknown')
            
            # Get minimum stock from all variants
            variants = product.get('variants', [])
            if variants:
                min_stock = min(
                    (v.get('stock', 0) if isinstance(v.get('stock'), int) else 999 
                     for v in variants),
                    default=0
                )
                
                product_info = f"- **{name}** (ID: {product.get('id')})"
                
                # Add variant details if multiple variants
                if len(variants) > 1:
                    variant_details = []
                    for v in variants:
                        stock = v.get('stock', 'N/A')
                        sku = v.get('sku', '')
                        values = v.get('variant_values', [])
                        variant_name = ', '.join([str(val) for val in values]) if values else sku
                        if variant_name:
                            variant_details.append(f"{variant_name}: {stock}")
                        elif sku:
                            variant_details.append(f"SKU {sku}: {stock}")
                    if variant_details:
                        product_info += f"\n  {' | '.join(variant_details)}"
                else:
                    product_info += f" - Stock: {min_stock}"
                
                if min_stock <= 3:
                    critical.append(product_info)
                elif min_stock <= 7:
                    low.append(product_info)
                else:
                    moderate.append(product_info)
        
        if critical:
            result += f"\n## 🔴 Critical Stock (1-3 units)\n{len(critical)} products\n\n"
            result += "\n".join(critical[:20])  # Show first 20
            if len(critical) > 20:
                result += f"\n\n... and {len(critical) - 20} more"
        
        if low:
            result += f"\n\n## 🟡 Low Stock (4-7 units)\n{len(low)} products\n\n"
            result += "\n".join(low[:15])  # Show first 15
            if len(low) > 15:
                result += f"\n\n... and {len(low) - 15} more"
        
        if moderate:
            result += f"\n\n## 🟢 Moderate Stock (8-10 units)\n{len(moderate)} products\n\n"
            result += "\n".join(moderate[:10])  # Show first 10
            if len(moderate) > 10:
                result += f"\n\n... and {len(moderate) - 10} more"
        
        return result
    except Exception as e:
        return f"Error fetching low stock products: {str(e)}"


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def analyze_product_performance(timeframe: str = "last_month") -> str:
    """Generate a prompt to analyze product performance"""
    return f"""
Please analyze the product performance for {timeframe}:

1. List the top-selling products
2. Identify products with low stock
3. Find products with high views but low conversion
4. Suggest pricing optimizations based on sales data

Use the available Tiendanube API tools to gather this information.
"""


@mcp.prompt()
def customer_segmentation() -> str:
    """Generate a prompt for customer segmentation analysis"""
    return """
Analyze the customer base and create segments:

1. Identify high-value customers (by order count and total spent)
2. Find customers who haven't purchased in 90+ days
3. Segment customers by location
4. Identify customers who accept marketing emails

Use the customer and order data from Tiendanube API.
"""


@mcp.prompt()
def order_fulfillment_analysis() -> str:
    """Generate a prompt for order fulfillment analysis"""
    return """
Analyze order fulfillment performance:

1. List orders with shipping_status="unpacked" (ready to pack)
2. Identify orders with payment_status="paid" but not shipped
3. Find orders with delayed shipping (compare max_delivery_date with today)
4. Calculate average time from order creation to shipment
5. List orders by shipping method to optimize logistics

Use list_orders with appropriate filters and get detailed order info.
"""


@mcp.prompt()
def revenue_analysis(period: str = "last_30_days") -> str:
    """Generate a prompt for revenue analysis"""
    return f"""
Analyze store revenue for {period}:

1. Calculate total revenue (sum of all paid orders)
2. Identify best-selling products by revenue
3. Compare revenue by payment method (gateway field)
4. Calculate average order value
5. Identify revenue trends by day/week
6. Show revenue by sales channel (storefront field: store, api, meli, pos)

Use list_orders with created_at filters and aggregate the data.
"""


@mcp.prompt()
def abandoned_orders_recovery() -> str:
    """Generate a prompt for abandoned order recovery"""
    return """
Identify opportunities to recover abandoned orders:

1. List orders with payment_status="abandoned" or "pending"
2. Calculate value of abandoned orders
3. Identify customers with multiple abandoned orders
4. Suggest personalized recovery strategies based on:
   - Order value
   - Products in cart
   - Customer purchase history
5. Create targeted coupon codes for high-value abandoned orders

Use list_orders and customer data to build recovery campaigns.
"""


@mcp.prompt()
def inventory_management_analysis() -> str:
    """Generate a prompt for inventory management"""
    return """
Analyze inventory and provide management recommendations:

1. Identify variants with critical stock (≤5 units)
2. Find products with imbalanced variant stock
3. Calculate inventory turnover rate
4. Suggest reorder points for popular variants
5. Identify slow-moving variants for clearance
6. Check for variants missing dimensions/weight (shipping issues)

Use list_products with stock filters and list_product_variants for details.
"""


@mcp.prompt()
def variant_optimization() -> str:
    """Generate a prompt for variant optimization"""
    return """
Optimize product variants for better sales:

1. Find products with multiple variants and analyze:
   - Which variants sell most
   - Which have poor performance
   - Price differences between variants
2. Identify variants missing key information:
   - No SKU assigned
   - Missing dimensions (affects shipping)
   - No promotional prices
3. Suggest variant consolidation opportunities
4. Recommend creating new variants based on demand

Use list_product_variants and order data to analyze variant performance.
"""


@mcp.prompt()
def billing_analysis() -> str:
    """Generate a prompt for billing and revenue analysis"""
    return """
Analyze billing and subscription performance:

1. Review subscription details:
   - Current plan and pricing
   - Next execution date (upcoming charge)
   - Last execution date
   - Recurring frequency
2. Calculate projected revenue:
   - Monthly recurring revenue (MRR)
   - Annual recurring revenue (ARR)
3. Identify optimization opportunities:
   - Merchants on outdated plans
   - Pricing discrepancies
   - Upgrade/downgrade patterns
4. Track extra charges:
   - Variable usage patterns
   - Overage frequency
   - Average extra charge amount
5. Suggest plan improvements:
   - New pricing tiers
   - Feature bundling
   - Usage-based pricing models

Use get_subscription and analyze charge patterns.
"""


@mcp.prompt()
def subscription_management() -> str:
    """Generate a prompt for subscription lifecycle management"""
    return """
Manage subscription lifecycle and billing health:

1. Monitor subscription status:
   - Active subscriptions
   - Next charge dates
   - Billing cycle alignment
2. Identify at-risk subscriptions:
   - Frequent plan downgrades
   - High extra charges (potential churn signal)
   - Pricing complaints
3. Proactive management:
   - Send reminders before next_execution
   - Offer upgrades to merchants with high usage
   - Create custom pricing for high-value clients
4. Optimize billing timing:
   - Align extra charges with subscription period
   - Create charges 1 day before next_execution
5. Revenue forecasting:
   - Project next month's revenue
   - Identify growth opportunities
   - Calculate customer lifetime value (LTV)

Use get_subscription and update_subscription strategically.
"""


# ============================================================================
# EXTENSIONS (nuvemshop-dev): webhooks + theme CLI
# ============================================================================

from extensions import webhooks as _ext_webhooks, theme as _ext_theme  # noqa: E402
_ext_webhooks.register(mcp, make_request)
_ext_theme.register(mcp)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point for the MCP server"""
    import sys
    import os
    
    # Get configuration from environment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8080"))
    stateless = os.getenv("MCP_STATELESS", "false").lower() == "true"
    json_response = os.getenv("MCP_JSON_RESPONSE", "false").lower() == "true"
    
    # Support command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["sse", "streamable-http", "stdio"]:
            transport = sys.argv[1]
    
    print("=" * 60)
    print("🚀 Nuvemshop Dev MCP Server")
    print("=" * 60)
    print(f"📦 Transport: {transport.upper()}")
    
    if transport == "sse":
        print(f"📡 SSE Server listening on http://{host}:{port}/sse")
        print(f"🔗 Connect clients to: http://{host}:{port}/sse")
        print("⚠️  Note: SSE is deprecated, use streamable-http for production")
        print("=" * 60)
        mcp.run(transport="sse", host=host, port=port)
        
    elif transport == "streamable-http":
        print(f"📡 Streamable HTTP Server listening on http://{host}:{port}/mcp")
        print(f"🔗 Connect clients to: http://{host}:{port}/mcp")
        print(f"💾 Stateless mode: {stateless}")
        print(f"📄 JSON response: {json_response}")
        print("=" * 60)
        
        # Configure FastMCP for streamable HTTP
        if stateless:
            mcp.settings.stateless_http = True
        if json_response:
            mcp.settings.json_response = True
            
        mcp.run(transport="streamable-http", host=host, port=port)
        
    else:
        print("📝 Running with stdio transport (for CLI usage)")
        print("💡 For web access, set MCP_TRANSPORT=streamable-http")
        print("=" * 60)
        mcp.run()


if __name__ == "__main__":
    main()