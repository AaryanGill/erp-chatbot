"""Sales module: orders, sales summary, top customer."""

from datetime import date, timedelta

from app import db
from app.models.sales import Customer, Order
from app.handlers.common import make_reply, find_customer_in_query, inr


def _order_row(o):
    return [f"ORD-{o.id:04d}", o.customer.name, str(o.order_date), inr(o.total_amount), o.status.title()]


ORDER_COLUMNS = ["Order", "Customer", "Date", "Amount", "Status"]


def sales_orders(entities, user_id, query):
    order_id = entities.get("order_id")
    if order_id:
        o = Order.query.get(int(order_id))
        if not o:
            return make_reply(f"No order found with number {order_id}.")
        return make_reply(f"Order ORD-{o.id:04d} is {o.status}.", ORDER_COLUMNS, [_order_row(o)])

    customer = find_customer_in_query(query)
    if customer:
        orders = (Order.query.filter_by(customer_id=customer.id)
                  .order_by(Order.order_date.desc()).limit(8).all())
        if not orders:
            return make_reply(f"{customer.name} has no orders.")
        return make_reply(f"{len(orders)} order(s) for {customer.name}.",
                          ORDER_COLUMNS, [_order_row(o) for o in orders])

    open_orders = (Order.query.filter(Order.status.in_(["pending", "shipped"]))
                   .order_by(Order.order_date.desc()).all())
    if not open_orders:
        return make_reply("There are no open orders right now.")
    total = sum(float(o.total_amount) for o in open_orders)
    return make_reply(f"{len(open_orders)} open order(s) worth {inr(total)}.",
                      ORDER_COLUMNS, [_order_row(o) for o in open_orders])


def sales_summary(entities, user_id, query):
    since = date.today() - timedelta(days=30)
    orders = Order.query.filter(Order.order_date >= since).all()
    if not orders:
        return make_reply("There are no orders in the last 30 days.")

    live = [o for o in orders if o.status != "cancelled"]
    total = sum(float(o.total_amount) for o in live)

    by_status = {}
    for o in orders:
        entry = by_status.setdefault(o.status, [0, 0.0])
        entry[0] += 1
        entry[1] += float(o.total_amount)
    rows = [[status.title(), str(n), inr(amt)] for status, (n, amt) in sorted(by_status.items())]

    return make_reply(f"Sales in the last 30 days: {inr(total)} from {len(live)} order(s), "
                      f"excluding cancelled orders.", ["Status", "Orders", "Amount"], rows)


def top_customer(entities, user_id, query):
    totals = {}
    for o in Order.query.filter(Order.status != "cancelled").all():
        totals[o.customer_id] = totals.get(o.customer_id, 0.0) + float(o.total_amount)
    if not totals:
        return make_reply("There are no orders yet.")

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:3]
    names = {c.id: c.name for c in Customer.query.filter(Customer.id.in_([cid for cid, _ in ranked])).all()}
    rows = [[str(i + 1), names[cid], inr(amt)] for i, (cid, amt) in enumerate(ranked)]
    return make_reply(f"Your top customer is {names[ranked[0][0]]} with {inr(ranked[0][1])} in orders.",
                      ["Rank", "Customer", "Total orders"], rows)