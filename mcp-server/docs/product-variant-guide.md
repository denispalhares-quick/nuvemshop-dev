# 📦 Product Variants - Complete Guide

Comprehensive guide for managing product variants in Tiendanube/Nuvemshop.

## 🎯 What are Product Variants?

Product variants allow you to group products with different attributes (size, color, material, etc.) under a single product listing.

**Example**: A t-shirt with multiple sizes and colors
- Product: "Premium T-Shirt"
- Variants: 
  - Small / Black
  - Small / White
  - Medium / Black
  - Medium / White
  - Large / Black
  - Large / White

## 📊 Key Limits & Rules

- ✅ **Max 1,000 variants** per product
- ✅ **Max 3 attributes** per product (e.g., Size, Color, Material)
- ✅ **Unique combinations** - Each variant must have a unique combination of values
- ✅ **Automatic stock_management** - Cannot be set manually via API
- ✅ **Values must match attributes** - Number of values = number of attributes

---

## 🔧 Available Methods

### 1. **list_product_variants** - List All Variants
```python
# Get all variants for a product
variants = list_product_variants(product_id=1234)

# With filters
variants = list_product_variants(
    product_id=1234,
    since_id=100,
    created_at_min="2025-01-01T00:00:00Z",
    fields="id,price,stock,sku"
)
```

### 2. **get_product_variant** - Get Single Variant
```python
variant = get_product_variant(
    product_id=1234,
    variant_id=5678
)
```

### 3. **create_product_variant** - Create New Variant
```python
# Simple variant
variant = create_product_variant(
    product_id=1234,
    values=[{"en": "X-Large"}],
    price="29.99",
    stock=50,
    sku="TSH-XL-001"
)

# Complete variant with all fields
variant = create_product_variant(
    product_id=1234,
    values=[{"en": "Large"}, {"en": "Red"}],
    price="34.99",
    promotional_price="29.99",
    stock=100,
    sku="TSH-L-RED-001",
    barcode="1234567890123",
    mpn="MPN-001",
    weight="0.3",
    width="30",
    height="40",
    depth="2",
    cost="15.00",
    age_group="adult",
    gender="unisex",
    image_id=12345
)
```

### 4. **update_product_variant** - Update Existing Variant
```python
# Update price and stock
updated = update_product_variant(
    product_id=1234,
    variant_id=5678,
    price="24.99",
    stock=75
)

# Set unlimited stock
updated = update_product_variant(
    product_id=1234,
    variant_id=5678,
    stock=""  # Empty string = unlimited
)
```

### 5. **replace_all_product_variants** - Replace Entire Collection ⚠️
```python
# WARNING: This DELETES variants not included!
variants = replace_all_product_variants(
    product_id=1234,
    variants=[
        {
            "values": [{"en": "Small"}],
            "price": "19.99",
            "stock": 10
        },
        {
            "values": [{"en": "Medium"}],
            "price": "19.99",
            "stock": 20
        },
        {
            "values": [{"en": "Large"}],
            "price": "24.99",
            "stock": 15
        }
    ]
)
# Result: Only these 3 variants exist, all others are DELETED
```

### 6. **batch_update_product_variants** - Safe Batch Update ✅
```python
# Update multiple variants safely (no deletion)
updated = batch_update_product_variants(
    product_id=1234,
    variants=[
        {
            "id": 143,
            "price": "19.99",
            "stock": 25
        },
        {
            "id": 144,
            "price": "24.99",
            "stock": 30
        }
    ]
)
# Result: Only specified variants updated, others unchanged
```

### 7. **delete_product_variant** - Delete Variant
```python
result = delete_product_variant(
    product_id=1234,
    variant_id=5678
)
```

### 8. **update_variant_stock** - Bulk Stock Operations
```python
# Replace stock for ALL variants
updated = update_variant_stock(
    product_id=1234,
    action="replace",
    value=50
)

# Set specific variant to unlimited stock
updated = update_variant_stock(
    product_id=1234,
    action="replace",
    value=None,  # None = unlimited
    variant_id=5678
)

# Add 10 units to specific variant
updated = update_variant_stock(
    product_id=1234,
    action="variation",
    value=10,
    variant_id=5678
)

# Remove 5 units from all variants
updated = update_variant_stock(
    product_id=1234,
    action="variation",
    value=-5
)
```

### 9. **set_variant_extra_shipping_days** - Shipping Rules
```python
# Add 5 extra days for custom products
metafield = set_variant_extra_shipping_days(
    variant_id=5678,
    additional_days=5
)
```

---

## 📋 Common Use Cases

### Use Case 1: Create Product with Multiple Variants

```python
# Step 1: Create product with attributes
product = create_product(
    name={"en": "Premium T-Shirt"},
    attributes=[{"en": "Size"}, {"en": "Color"}],
    variants=[
        {
            "values": [{"en": "Small"}, {"en": "Black"}],
            "price": "19.99",
            "stock": 50,
            "sku": "TSH-S-BLK"
        },
        {
            "values": [{"en": "Small"}, {"en": "White"}],
            "price": "19.99",
            "stock": 50,
            "sku": "TSH-S-WHT"
        },
        {
            "values": [{"en": "Medium"}, {"en": "Black"}],
            "price": "19.99",
            "stock": 75,
            "sku": "TSH-M-BLK"
        },
        {
            "values": [{"en": "Medium"}, {"en": "White"}],
            "price": "19.99",
            "stock": 75,
            "sku": "TSH-M-WHT"
        }
    ]
)

# Step 2: Add more variants later if needed
new_variant = create_product_variant(
    product_id=product["id"],
    values=[{"en": "Large"}, {"en": "Black"}],
    price="24.99",
    stock=100,
    sku="TSH-L-BLK"
)
```

### Use Case 2: Update Prices for Multiple Variants

```python
# Get all variants
variants = list_product_variants(product_id=1234)

# Prepare updates (increase all prices by 10%)
updates = []
for variant in variants:
    new_price = float(variant["price"]) * 1.10
    updates.append({
        "id": variant["id"],
        "price": f"{new_price:.2f}"
    })

# Apply updates
result = batch_update_product_variants(
    product_id=1234,
    variants=updates
)
```

### Use Case 3: Low Stock Alert & Restock

```python
# Find variants with low stock
variants = list_product_variants(product_id=1234)

low_stock = [
    v for v in variants 
    if v.get("stock") is not None and v["stock"] < 10
]

print(f"⚠️ {len(low_stock)} variants need restocking:")
for v in low_stock:
    values = ", ".join([val.get("en", "") for val in v["values"]])
    print(f"  - {values}: {v['stock']} units (SKU: {v['sku']})")

# Restock specific variant
if low_stock:
    update_variant_stock(
        product_id=1234,
        action="replace",
        value=100,
        variant_id=low_stock[0]["id"]
    )
```

### Use Case 4: Seasonal Sale (Promotional Prices)

```python
# Get all variants
variants = list_product_variants(product_id=1234)

# Apply 20% discount to all
updates = []
for variant in variants:
    original_price = float(variant["price"])
    promo_price = original_price * 0.80
    
    updates.append({
        "id": variant["id"],
        "promotional_price": f"{promo_price:.2f}"
    })

# Apply promotional prices
result = batch_update_product_variants(
    product_id=1234,
    variants=updates
)
```

### Use Case 5: Inventory Sync

```python
# External inventory system data
external_inventory = {
    "TSH-S-BLK": 45,
    "TSH-M-BLK": 60,
    "TSH-L-BLK": 30
}

# Get current variants
variants = list_product_variants(product_id=1234)

# Prepare updates
updates = []
for variant in variants:
    sku = variant.get("sku")
    if sku in external_inventory:
        updates.append({
            "id": variant["id"],
            "stock": external_inventory[sku]
        })

# Sync stock
if updates:
    result = batch_update_product_variants(
        product_id=1234,
        variants=updates
    )
    print(f"✅ Synced {len(updates)} variants")
```

---

## 🎨 Important Properties

### Stock Management

| stock value | stock_management | Result |
|-------------|------------------|--------|
| `50` | `true` (auto) | 50 units tracked |
| `0` | `true` (auto) | Out of stock |
| `""` or `null` | `false` (auto) | Unlimited/Infinite |

### Age Group (Optional)
Valid values: `"newborn"`, `"infant"`, `"toddler"`, `"kids"`, `"adult"`

### Gender (Optional)
Valid values: `"female"`, `"male"`, `"unisex"`

### Dimensions
- **weight**: in kg (string)
- **width**: in cm (string)
- **height**: in cm (string)
- **depth**: in cm (string)

---

## ⚠️ Common Errors & Solutions

### Error: "Variants cannot be repeated"
```
Problem: Trying to create variant with existing value combination
Solution: Check existing variants, update instead of create
```

### Error: "Product is not allowed to have more than 1000 variants"
```
Problem: Exceeding variant limit
Solution: Remove unused variants or split into multiple products
```

### Error: "The selected age_group is invalid"
```
Problem: Using invalid age_group value
Solution: Use only: newborn, infant, toddler, kids, adult
```

### Error: "The selected gender is invalid"
```
Problem: Using invalid gender value
Solution: Use only: female, male, unisex
```

### Error: "Variant values should not be empty"
```
Problem: Sending empty values array
Solution: Always include values matching product attributes
```

---

## 🚀 Best Practices

### ✅ DO:
- Use `batch_update_product_variants()` for multiple updates (safer)
- Always set SKU for inventory tracking
- Include dimensions for accurate shipping calculations
- Use promotional_price for sales instead of changing price
- Set age_group and gender for Google Shopping
- Use meaningful SKU patterns (e.g., `PRODUCT-SIZE-COLOR`)

### ❌ DON'T:
- Use `replace_all_product_variants()` unless you really mean to delete variants
- Try to manually set `stock_management` (it's automatic)
- Create variants with duplicate value combinations
- Forget to include all attribute values
- Remove stock from variants still being sold

---

## 📊 Performance Tips

### Bulk Operations
```python
# ❌ Slow: Individual updates
for variant_id in variant_ids:
    update_product_variant(product_id, variant_id, price="19.99")

# ✅ Fast: Batch update
updates = [{"id": vid, "price": "19.99"} for vid in variant_ids]
batch_update_product_variants(product_id, updates)
```

### Stock Updates
```python
# ❌ Slow: Update each variant individually
for variant in variants:
    update_product_variant(product_id, variant["id"], stock=50)

# ✅ Fast: Use bulk stock update
update_variant_stock(product_id, action="replace", value=50)
```

### Filtering
```python
# ✅ Use fields parameter to reduce payload
variants = list_product_variants(
    product_id=1234,
    fields="id,sku,stock,price"
)

# ✅ Use date filters for incremental updates
variants = list_product_variants(
    product_id=1234,
    updated_at_min="2025-10-01T00:00:00Z"
)
```

---

## 🔄 Migration Strategies

### Migrating from External System

```python
def migrate_variants(product_id, external_variants):
    """
    Safely migrate variants from external system
    """
    # Get current variants
    current = list_product_variants(product_id)
    current_map = {
        tuple(v.get("sku")): v for v in current 
        if v.get("sku")
    }
    
    updates = []
    creates = []
    
    for ext_variant in external_variants:
        sku = ext_variant["sku"]
        
        if sku in current_map:
            # Update existing
            updates.append({
                "id": current_map[sku]["id"],
                "price": ext_variant["price"],
                "stock": ext_variant["stock"],
                "sku": sku
            })
        else:
            # Create new
            creates.append({
                "values": ext_variant["values"],
                "price": ext_variant["price"],
                "stock": ext_variant["stock"],
                "sku": sku
            })
    
    # Apply updates
    if updates:
        batch_update_product_variants(product_id, updates)
        print(f"✅ Updated {len(updates)} variants")
    
    # Create new variants
    for variant_data in creates:
        create_product_variant(product_id, **variant_data)
    print(f"✅ Created {len(creates)} new variants")
```

---

## 📈 Analytics & Reporting

### Variant Performance Report

```python
def analyze_variant_performance(product_id):
    """
    Generate performance report for product variants
    """
    # Get variants
    variants = list_product_variants(product_id)
    
    # Get recent orders with this product
    orders = list_orders(
        created_at_min="2025-09-01T00:00:00Z",
        per_page=200
    )
    
    # Count sales per variant
    variant_sales = {}
    for order in orders:
        for item in order.get("products", []):
            if item["product_id"] == product_id:
                vid = item["variant_id"]
                variant_sales[vid] = variant_sales.get(vid, 0) + item["quantity"]
    
    # Generate report
    print("\n" + "="*60)
    print("VARIANT PERFORMANCE REPORT")
    print("="*60)
    
    for variant in sorted(variants, key=lambda v: variant_sales.get(v["id"], 0), reverse=True):
        values = ", ".join([v.get("en", "") for v in variant["values"]])
        sales = variant_sales.get(variant["id"], 0)
        stock = variant.get("stock", "∞")
        price = variant.get("price", "N/A")
        
        print(f"\n{values}")
        print(f"  SKU: {variant.get('sku', 'N/A')}")
        print(f"  Sales: {sales} units")
        print(f"  Stock: {stock}")
        print(f"  Price: ${price}")
        print(f"  Revenue: ${float(price) * sales if price != 'N/A' else 0:.2f}")
```

### Low Stock Alert System

```python
def check_low_stock_variants(threshold=10):
    """
    Check all products for low stock variants
    """
    products = list_products(published=True, per_page=200)
    
    alerts = []
    
    for product in products:
        product_id = product["id"]
        product_name = product["name"].get("en", "Unknown")
        
        variants = list_product_variants(product_id)
        
        for variant in variants:
            stock = variant.get("stock")
            
            if stock is not None and stock <= threshold:
                values = ", ".join([v.get("en", "") for v in variant["values"]])
                
                alerts.append({
                    "product": product_name,
                    "variant": values,
                    "sku": variant.get("sku"),
                    "stock": stock,
                    "price": variant.get("price")
                })
    
    # Print report
    if alerts:
        print(f"\n⚠️  LOW STOCK ALERT: {len(alerts)} variants")
        print("="*60)
        
        for alert in sorted(alerts, key=lambda x: x["stock"]):
            print(f"\n🔴 {alert['product']} - {alert['variant']}")
            print(f"   SKU: {alert['sku']}")
            print(f"   Stock: {alert['stock']} units")
            print(f"   Price: ${alert['price']}")
    else:
        print("✅ All variants have sufficient stock")
```

---

## 🔧 Automation Examples

### Auto-Restock Based on Sales Velocity

```python
def auto_restock_variants(days_to_analyze=30, target_days=60):
    """
    Automatically restock based on sales velocity
    """
    import datetime
    
    # Get orders from last X days
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_to_analyze)
    orders = list_orders(
        created_at_min=cutoff.isoformat() + "Z",
        payment_status="paid",
        per_page=200
    )
    
    # Calculate sales velocity per variant
    variant_velocity = {}  # variant_id: units per day
    
    for order in orders:
        for item in order.get("products", []):
            vid = item["variant_id"]
            qty = int(item["quantity"])
            
            if vid not in variant_velocity:
                variant_velocity[vid] = 0
            variant_velocity[vid] += qty
    
    # Convert to daily rate
    for vid in variant_velocity:
        variant_velocity[vid] = variant_velocity[vid] / days_to_analyze
    
    # Check each product's variants
    products = list_products(published=True, per_page=200)
    
    restock_recommendations = []
    
    for product in products:
        variants = list_product_variants(product["id"])
        
        for variant in variants:
            vid = variant["id"]
            current_stock = variant.get("stock")
            
            if current_stock is None:  # Unlimited stock
                continue
            
            if vid in variant_velocity:
                velocity = variant_velocity[vid]
                days_remaining = current_stock / velocity if velocity > 0 else float('inf')
                
                if days_remaining < target_days:
                    # Calculate restock amount
                    needed = int(velocity * target_days - current_stock)
                    
                    restock_recommendations.append({
                        "product_id": product["id"],
                        "variant_id": vid,
                        "current_stock": current_stock,
                        "velocity": velocity,
                        "days_remaining": days_remaining,
                        "restock_amount": needed
                    })
    
    # Apply restocking
    for rec in restock_recommendations:
        new_stock = rec["current_stock"] + rec["restock_amount"]
        
        update_variant_stock(
            product_id=rec["product_id"],
            action="replace",
            value=new_stock,
            variant_id=rec["variant_id"]
        )
        
        print(f"✅ Restocked variant {rec['variant_id']}: "
              f"{rec['current_stock']} → {new_stock} units "
              f"(velocity: {rec['velocity']:.2f}/day)")
```

### Dynamic Pricing Based on Stock Level

```python
def adjust_prices_by_stock(product_id):
    """
    Increase prices for low stock, decrease for overstock
    """
    variants = list_product_variants(product_id)
    
    updates = []
    
    for variant in variants:
        stock = variant.get("stock")
        base_price = float(variant.get("price", 0))
        
        if stock is None:  # Unlimited
            continue
        
        # Pricing logic
        if stock < 5:
            # Low stock: increase 20%
            new_price = base_price * 1.20
            reason = "Low stock premium"
        elif stock > 100:
            # Overstock: decrease 15%
            new_price = base_price * 0.85
            reason = "Overstock discount"
        else:
            continue
        
        updates.append({
            "id": variant["id"],
            "price": f"{new_price:.2f}"
        })
        
        values = ", ".join([v.get("en", "") for v in variant["values"]])
        print(f"💰 {values}: ${base_price:.2f} → ${new_price:.2f} ({reason})")
    
    if updates:
        batch_update_product_variants(product_id, updates)
        print(f"\n✅ Updated {len(updates)} variant prices")
```

---

## 🧪 Testing Utilities

```python
def test_variant_operations(product_id):
    """
    Comprehensive test suite for variant operations
    """
    print("\n🧪 Testing Variant Operations...")
    
    # Test 1: List variants
    print("\n1. Listing variants...")
    variants = list_product_variants(product_id)
    print(f"   ✅ Found {len(variants)} variants")
    
    if not variants:
        print("   ⚠️  No variants to test with")
        return
    
    # Test 2: Get single variant
    print("\n2. Getting single variant...")
    variant = get_product_variant(product_id, variants[0]["id"])
    print(f"   ✅ Retrieved variant {variant['id']}")
    
    # Test 3: Update variant
    print("\n3. Updating variant...")
    original_price = variant.get("price")
    test_price = "999.99"
    
    updated = update_product_variant(
        product_id=product_id,
        variant_id=variant["id"],
        price=test_price
    )
    print(f"   ✅ Updated price: {original_price} → {test_price}")
    
    # Test 4: Restore original price
    print("\n4. Restoring original price...")
    update_product_variant(
        product_id=product_id,
        variant_id=variant["id"],
        price=original_price
    )
    print(f"   ✅ Restored price: {test_price} → {original_price}")
    
    # Test 5: Stock operations
    print("\n5. Testing stock operations...")
    original_stock = variant.get("stock")
    
    # Add stock
    update_variant_stock(
        product_id=product_id,
        action="variation",
        value=10,
        variant_id=variant["id"]
    )
    print(f"   ✅ Added 10 units")
    
    # Remove stock
    update_variant_stock(
        product_id=product_id,
        action="variation",
        value=-10,
        variant_id=variant["id"]
    )
    print(f"   ✅ Removed 10 units")
    
    print("\n✅ All tests passed!")
```

---

## 📚 Quick Reference

### Method Summary

| Method | Type | Destructive? | Best For |
|--------|------|--------------|----------|
| `list_product_variants` | Read | No | Getting all variants |
| `get_product_variant` | Read | No | Single variant details |
| `create_product_variant` | Create | No | Adding new variants |
| `update_product_variant` | Update | No | Single variant update |
| `batch_update_product_variants` | Update | No | ✅ Multiple updates (safe) |
| `replace_all_product_variants` | Replace | ⚠️ YES | Complete rebuild |
| `delete_product_variant` | Delete | ⚠️ YES | Removing variants |
| `update_variant_stock` | Update | No | ✅ Bulk stock operations |
| `set_variant_extra_shipping_days` | Create | No | Shipping rules |

### Stock Actions

| Action | Value | Result |
|--------|-------|--------|
| `replace` | `50` | Set to 50 units |
| `replace` | `0` | Out of stock |
| `replace` | `null` | Unlimited stock |
| `variation` | `10` | Add 10 units |
| `variation` | `-5` | Remove 5 units |

---

## 🎓 Learning Path

1. **Beginner**: Start with single variant operations
   - Create simple products with 1-2 variants
   - Update individual variants
   - Basic stock management

2. **Intermediate**: Use batch operations
   - Update multiple variants at once
   - Implement stock alerts
   - Set up promotional pricing

3. **Advanced**: Automation & analytics
   - Auto-restock based on velocity
   - Dynamic pricing algorithms
   - Performance analytics
   - Integration with external systems

---

## 🆘 Troubleshooting Guide

### Problem: Variant not updating
```python
# Check if variant belongs to product
variant = get_product_variant(product_id, variant_id)
if variant["product_id"] != product_id:
    print("❌ Variant doesn't belong to this product")
```

### Problem: Stock not changing
```python
# Verify stock_management status
variant = get_product_variant(product_id, variant_id)
print(f"Stock management: {variant['stock_management']}")
print(f"Current stock: {variant['stock']}")

# If stock is None, it's unlimited
if variant["stock"] is None:
    print("ℹ️  Variant has unlimited stock")
```

### Problem: Batch update fails
```python
# Ensure all variants have 'id' field
updates = [
    {"id": 123, "price": "19.99"},  # ✅ Correct
    {"price": "19.99"}  # ❌ Missing id
]

# Check for duplicate value combinations
# Each variant must have unique values
```

---

## 💡 Pro Tips

1. **Use SKU for everything** - Makes inventory management much easier
2. **Set dimensions early** - Required for accurate shipping calculations
3. **Use promotional_price** - Instead of changing price for sales
4. **Batch operations** - Always prefer batch methods for multiple updates
5. **Monitor stock levels** - Set up automated alerts
6. **Test in development** - Use test products before production changes
7. **Keep audit logs** - Track price and stock changes
8. **Use meaningful SKUs** - Follow a pattern: `{PRODUCT}-{ATTR1}-{ATTR2}`

---

**Need help?** Check the [main server documentation](README.md) or the [Tiendanube API docs](https://tiendanube.github.io/api-documentation/).
