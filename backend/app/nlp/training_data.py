"""
Training examples for the ML intent classifier (19 intents + an out-of-scope class).
To improve accuracy, add more example sentences to any intent and re-run evaluate_nlp.py.
"""

TRAINING_DATA = {
    # ------------------------------------------------------------ general
    "greeting": [
        "hello", "hi", "hey", "hi there", "hello there", "good morning",
        "good afternoon", "good evening", "hey bot", "hello assistant",
        "hi assistant", "greetings",
    ],
    "help": [
        "help", "help me", "what can you do", "what are the commands",
        "show me the options", "how do i use this", "what can i ask",
        "list the commands", "what are your features", "i need help",
        "how does this work", "show help",
    ],

    # ------------------------------------------------------------ HR
    "check_leave_balance": [
        "check leave balance", "what is my leave balance", "how many leaves do i have",
        "how many leave days remaining", "remaining leave days", "leave balance for employee 2",
        "show my leave balance", "how many days off do i have left", "my pto balance",
        "how much leave is left", "leaves left", "tell me my remaining leaves",
        "balance of leave days", "how many vacation days do i have left",
        "how many days off are remaining", "days of leave left for me",
        "how many casual leaves can i still use",
    ],
    "apply_leave": [
        "apply leave", "apply for leave", "i want to apply for leave", "apply leave from 5 nov to 8 nov",
        "request leave for tomorrow", "book vacation", "i need a leave on 12 december",
        "submit a leave request", "take leave tomorrow", "apply leave for employee 1",
        "i want to take a day off", "please apply leave on 20 dec", "request time off",
        "book leave from 1 jan to 3 jan", "apply for vacation next week",
        "can i take friday off", "i need next monday off", "can i get a day off tomorrow",
    ],
    "my_leave_requests": [
        "show my leave requests", "my leave requests", "leave request status",
        "what is the status of my leave", "list my leave history", "pending leaves",
        "show leave history", "did my leave get approved", "view my requests",
        "show all my leave applications", "leave status", "my requests",
    ],
    "employee_info": [
        "show employee profile", "employee info", "tell me about employee 12",
        "what is the department of employee 2", "designation of employee 1",
        "show my profile", "who is employee 12", "employee details",
        "which department do i work in", "what is my designation", "my employee profile",
        "show profile for employee 2", "details of employee 1", "what is my job title",
    ],
    "employee_list": [
        "list all employees", "show all employees", "employees in sales", "who works in engineering",
        "how many employees do we have", "employee list", "show employees in finance department",
        "list the staff", "headcount by department", "give me the staff list",
        "all employees in hr", "show everyone in operations", "who are the employees",
        "how many people work in the company", "how many staff members are there",
        "who all work here", "number of employees in each department",
    ],
    "my_attendance": [
        "did i come in today", "my attendance", "show my attendance this week", "was i present yesterday",
        "attendance for employee 2", "how many days was i absent", "my check in time",
        "show attendance record", "attendance this month", "did i mark attendance today",
        "how many days present this month", "am i marked present today", "when did i check in",
        "was i late today", "what time did i arrive",
    ],
    "payslip": [
        "show my payslip", "what is my salary", "net pay for last month", "salary slip for october",
        "how much was i paid", "download my payslip", "payslip for employee 2",
        "what is my take home pay", "show salary details", "my salary breakdown",
        "show deductions on my payslip", "what is my basic pay", "how much salary did i get",
        "did i get paid this month", "when was my salary credited",
        "how much money did i earn last month", "show my pay for this month",
    ],

    # ------------------------------------------------------------ Inventory
    "check_inventory": [
        "check stock for sku abc123", "inventory for sku chr456", "how many office chairs in stock",
        "how many chairs do we have", "stock of wireless mouse", "is the laptop stand available",
        "quantity of wireless mouse", "do we have any mouse in stock", "how many laptop stands are there",
        "check inventory", "available quantity for sku lps789", "how many units of office chair",
        "stock level of laptop stand", "is sku abc123 available", "inventory of mouse",
        "how many mice are left", "how many chairs are left", "units left of laptop stand",
        "how many are left in stock", "how many monitors are in stock", "stock of usb hub",
        "what is in the warehouse", "what do we have in stock", "show current inventory levels",
    ],
    "low_stock_alert": [
        "what items are low on stock", "show low stock items", "which items need reorder",
        "any shortage", "restock needed", "items below reorder level", "what should we reorder",
        "low inventory items", "which products are running out", "items running low",
        "stock alerts", "what is out of stock soon", "show items that need restocking",
        "are we running out of anything", "which products are almost finished",
    ],
    "inventory_value": [
        "total stock value", "what is the inventory worth", "value of our inventory",
        "how much is our stock worth", "inventory valuation", "total value of all items in stock",
        "worth of warehouse stock", "show stock value", "what is the total inventory value",
        "how much money is in inventory", "value of goods in stock",
    ],

    # ------------------------------------------------------------ Sales
    "sales_orders": [
        "show open orders", "pending orders", "list customer orders", "status of order 3",
        "orders from acme", "show orders for globex", "which orders are not delivered",
        "show recent sales orders", "what orders are shipped", "track order 4",
        "open sales orders", "order status", "show orders placed by initech",
        "which orders are pending delivery", "list all orders",
        "is anything stuck in shipping", "which orders are still in transit",
        "what orders have not arrived yet", "show shipped orders",
    ],
    "sales_summary": [
        "total sales this month", "how much revenue did we make", "sales summary", "sales report",
        "what are our sales numbers", "revenue for the last 30 days", "show me sales performance",
        "how are sales doing", "total sales", "sales overview", "how much did we sell",
        "give me the revenue figures", "how are we doing this month", "show me the sales figures",
    ],
    "top_customer": [
        "who is our top customer", "best customer", "which customer buys the most",
        "top customers by revenue", "biggest client", "who are our best clients",
        "highest spending customer", "top buyer", "which client orders the most",
        "show our best customers", "which customer brings in the most money",
    ],

    # ------------------------------------------------------------ Finance
    "overdue_invoices": [
        "overdue invoices", "which invoices are overdue", "late payments", "invoices past due date",
        "who has not paid on time", "show overdue payments", "list overdue bills",
        "payments past due", "any invoice overdue", "which customers are late on payment",
        "show invoices that are late",
    ],
    "unpaid_invoices": [
        "unpaid invoices", "outstanding amount", "pending payments", "how much do customers owe us",
        "total receivable", "show unpaid bills", "money yet to be collected",
        "outstanding invoices total", "what is pending to collect", "accounts receivable",
        "how much is yet to be paid", "show invoices not paid yet",
        "who has not paid us yet", "who still owes us money",
    ],
    "invoice_lookup": [
        "status of invoice 3", "show invoice for globex", "invoices for acme", "details of invoice 2",
        "show latest invoices", "is invoice 5 paid", "find invoice", "invoice details",
        "show invoices for initech", "list invoices", "show me inv 4", "recent invoices",
    ],

    # ------------------------------------------------------------ Procurement
    "purchase_orders": [
        "show pending purchase orders", "purchase orders from techparts", "when will the usb c hub arrive",
        "status of purchase order 2", "list purchase orders", "open purchase orders",
        "what have we ordered from suppliers", "when will the monitors be delivered",
        "which deliveries are pending", "supplier orders", "purchase order for office chairs",
        "show incoming stock", "when is the supplier delivery expected", "po status",
        "any deliveries coming this week", "what do we owe our suppliers",
    ],

    # ------------------------------------------------------------ Approvals
    "pending_approvals": [
        "show pending approvals", "what is waiting for my approval", "which leave requests need approval",
        "who has applied for leave", "show requests awaiting approval", "any leave requests to approve",
        "list leave requests from the team", "pending leave requests for approval",
        "are there requests waiting for approval", "show approvals",
        "who has requested leave", "show leave applications from employees",
    ],
    "decide_leave": [
        "approve request 3", "approve leave request 2", "reject request 4", "please approve leave 5",
        "decline leave request 1", "reject leave request 3", "approve request number 2",
        "deny request 6", "approve the leave", "reject the leave request",
    ],

    # ------------------------------------------------------------ Out of scope
    # Teaches the model what NOT to answer, so off-topic questions are rejected.
    "unknown": [
        "what is the weather today", "tell me a joke", "play some music", "book a table for dinner",
        "who won the cricket match", "what is the capital of france", "thank you", "thanks a lot",
        "ok", "who are you", "what is your name", "how old are you", "sing a song",
        "translate this to hindi", "what time is it", "order me a pizza", "how do i cook pasta",
        "tell me a story", "what is two plus two", "bye", "goodbye", "are you a robot",
        "yes", "no", "maybe", "recommend a movie", "what is the news today", "write a poem", "how tall is mount everest",
    ],
}