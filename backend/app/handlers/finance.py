"""Finance module: invoices, overdue payments, receivables."""

from datetime import date

from app.models.finance import Invoice
from app.handlers.common import make_reply, find_customer_in_query, inr

INV_COLUMNS = ["Invoice", "Customer", "Amount", "Due date", "Status"]


def _status(inv, today):
    if inv.status == "paid":
        return "Paid"
    if inv.due_date < today:
        return f"Overdue ({(today - inv.due_date).days} days)"
    return "Unpaid"


def _row(inv, today):
    return [f"INV-{inv.id:04d}", inv.customer.name, inr(inv.amount), str(inv.due_date), _status(inv, today)]


def overdue_invoices(entities, user_id, query):
    today = date.today()
    items = (Invoice.query.filter(Invoice.status == "unpaid", Invoice.due_date < today)
             .order_by(Invoice.due_date).all())
    if not items:
        return make_reply("No invoices are overdue. Nice.")
    total = sum(float(i.amount) for i in items)
    return make_reply(f"{len(items)} invoice(s) are overdue, totalling {inr(total)}.",
                      INV_COLUMNS, [_row(i, today) for i in items])


def unpaid_invoices(entities, user_id, query):
    today = date.today()
    items = Invoice.query.filter_by(status="unpaid").order_by(Invoice.due_date).all()
    if not items:
        return make_reply("There are no unpaid invoices.")
    total = sum(float(i.amount) for i in items)
    overdue = sum(1 for i in items if i.due_date < today)
    return make_reply(f"{inr(total)} is outstanding across {len(items)} unpaid invoice(s); {overdue} overdue.",
                      INV_COLUMNS, [_row(i, today) for i in items])


def invoice_lookup(entities, user_id, query):
    today = date.today()

    invoice_id = entities.get("invoice_id")
    if invoice_id:
        inv = Invoice.query.get(int(invoice_id))
        if not inv:
            return make_reply(f"No invoice found with number {invoice_id}.")
        return make_reply(f"Invoice INV-{inv.id:04d} is {_status(inv, today).lower()}.",
                          INV_COLUMNS, [_row(inv, today)])

    customer = find_customer_in_query(query)
    if customer:
        items = (Invoice.query.filter_by(customer_id=customer.id)
                 .order_by(Invoice.issue_date.desc()).limit(8).all())
        if not items:
            return make_reply(f"{customer.name} has no invoices.")
        return make_reply(f"{len(items)} invoice(s) for {customer.name}.",
                          INV_COLUMNS, [_row(i, today) for i in items])

    items = Invoice.query.order_by(Invoice.issue_date.desc()).limit(5).all()
    if not items:
        return make_reply("There are no invoices yet.")
    return make_reply("Your latest invoices:", INV_COLUMNS, [_row(i, today) for i in items])