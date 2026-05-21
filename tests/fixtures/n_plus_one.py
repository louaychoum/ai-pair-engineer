"""Classic N+1 ORM query problem.

Loads N orders, then issues N more queries to load each order's customer.
On a customer page with 100 orders that's 101 round trips to the database.

Paste this into the AI Pair Engineer to see it caught.
"""

from sqlalchemy.orm import Session
from models import Order


def render_orders_page(session: Session, customer_id: int) -> str:
    orders = session.query(Order).filter(Order.customer_id == customer_id).all()

    rows = []
    for order in orders:
        # Each access to order.customer triggers a fresh SELECT.
        customer_name = order.customer.name
        rows.append(f"<tr><td>{order.id}</td><td>{customer_name}</td></tr>")

    return "<table>" + "".join(rows) + "</table>"
