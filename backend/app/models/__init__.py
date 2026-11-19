# Importing every model here guarantees db.create_all() sees all tables.
from app.models.user import User                                  # noqa: F401
from app.models.employee import Employee, LeaveRequest           # noqa: F401
from app.models.inventory import InventoryItem                   # noqa: F401
from app.models.chat_log import ChatLog                          # noqa: F401
from app.models.hr import Attendance, Payslip                    # noqa: F401
from app.models.sales import Customer, Order                     # noqa: F401
from app.models.finance import Invoice                           # noqa: F401
from app.models.procurement import Supplier, PurchaseOrder       # noqa: F401