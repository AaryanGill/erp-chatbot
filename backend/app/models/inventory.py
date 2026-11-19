from app import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(50), unique=True)
    quantity = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    unit_price = db.Column(db.Numeric(10, 2))

    def to_dict(self):
        return {
            "id": self.id,
            "item_name": self.item_name,
            "sku": self.sku,
            "quantity": self.quantity,
            "reorder_level": self.reorder_level,
        }