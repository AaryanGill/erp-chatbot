"""Inventory module: stock lookup, low-stock alerts, stock value."""

from app.models.inventory import InventoryItem
from app.handlers.common import make_reply, find_item_in_query, inr


def _stock_message(item):
    flag = " (below reorder level!)" if item.quantity <= item.reorder_level else ""
    return f"{item.item_name} (SKU {item.sku}): {item.quantity} units in stock{flag}."


def check_inventory(entities, user_id, query):
    sku = entities.get("item_sku")
    if sku:
        item = InventoryItem.query.filter(InventoryItem.sku.ilike(sku)).first()
        return make_reply(_stock_message(item) if item else f"No item found with SKU {sku}.")

    item = find_item_in_query(query)
    if item:
        return make_reply(_stock_message(item))
    return make_reply("Please give an item name or SKU, e.g. 'check stock for SKU ABC123'.")


def low_stock_alert(entities, user_id, query):
    low = (InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level)
           .order_by(InventoryItem.quantity).all())
    if not low:
        return make_reply("No items are currently below their reorder level.")
    rows = [[i.item_name, i.sku, str(i.quantity), str(i.reorder_level)] for i in low]
    return make_reply(f"{len(low)} item(s) are at or below their reorder level.",
                      ["Item", "SKU", "In stock", "Reorder at"], rows)


def inventory_value(entities, user_id, query):
    items = InventoryItem.query.all()
    if not items:
        return make_reply("There are no inventory items yet.")
    priced = sorted(((float(i.unit_price or 0) * i.quantity, i) for i in items),
                    key=lambda p: p[0], reverse=True)
    total = sum(v for v, _ in priced)
    rows = [[i.item_name, str(i.quantity), inr(i.unit_price, 2), inr(v)] for v, i in priced[:8]]
    return make_reply(f"Total stock value is {inr(total)} across {len(items)} item(s).",
                      ["Item", "Qty", "Unit price", "Value"], rows)