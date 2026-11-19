"""Procurement module: purchase orders and supplier deliveries."""

import re

from app.models.procurement import PurchaseOrder
from app.handlers.common import make_reply, find_supplier_in_query, inr

PO_COLUMNS = ["PO", "Supplier", "Item", "Qty", "Cost", "Expected", "Status"]
STOPWORDS = {"the", "and", "for", "inch"}


def _row(po):
    return [f"PO-{po.id:04d}", po.supplier.name, po.item_name, str(po.quantity),
            inr(po.total_cost), str(po.expected_date), po.status.title()]


def _find_by_item(query):
    q = query.lower()
    matches = []
    for po in PurchaseOrder.query.all():
        name = po.item_name.lower()
        words = [w for w in re.findall(r"[a-z]+", name) if len(w) >= 3 and w not in STOPWORDS]
        if name in q or any(re.search(rf"\b{re.escape(w)}", q) for w in words):
            matches.append(po)
    return matches


def purchase_orders(entities, user_id, query):
    po_id = entities.get("po_id")
    if po_id:
        po = PurchaseOrder.query.get(int(po_id))
        if not po:
            return make_reply(f"No purchase order found with number {po_id}.")
        return make_reply(f"Purchase order PO-{po.id:04d} is {po.status}; expected {po.expected_date}.",
                          PO_COLUMNS, [_row(po)])

    supplier = find_supplier_in_query(query)
    if supplier:
        items = (PurchaseOrder.query.filter_by(supplier_id=supplier.id)
                 .order_by(PurchaseOrder.order_date.desc()).all())
        if items:
            return make_reply(f"{len(items)} purchase order(s) with {supplier.name}.",
                              PO_COLUMNS, [_row(p) for p in items])

    by_item = _find_by_item(query)
    if by_item:
        first = by_item[0]
        return make_reply(f"{first.item_name} is {first.status}; expected {first.expected_date}.",
                          PO_COLUMNS, [_row(p) for p in by_item])

    pending = (PurchaseOrder.query.filter(PurchaseOrder.status != "received")
               .order_by(PurchaseOrder.expected_date).all())
    if not pending:
        return make_reply("There are no pending purchase orders.")
    total = sum(float(p.total_cost) for p in pending)
    return make_reply(f"{len(pending)} purchase order(s) are still pending, worth {inr(total)}.",
                      PO_COLUMNS, [_row(p) for p in pending])