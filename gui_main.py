import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import random
import string

DATA_FILE = "data.json"
ADMIN_PASSWORD = "admin"

class CafeSystemGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cafe Management System")
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")
        
        # Initialize Data
        self.data = self.load_data()
        
        # Container for screens
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (MainScreen, CustomerScreen, AdminScreen):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("MainScreen")

    def show_frame(self, page_name):
        # Refresh data when switching frames to ensure updates (like new menu items) are seen
        self.data = self.load_data()
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "refresh"):
            frame.refresh()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"menu": {}, "orders": {}}
        with open(DATA_FILE, 'r') as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    def generate_order_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


class MainScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#333333")
        self.controller = controller
        
        lbl_title = tk.Label(self, text="Welcome to The Mini Cafe", font=("Helvetica", 26, "bold"), fg="Green", bg="#333333")
        lbl_title.pack(pady=80)
        
        btn_frame = tk.Frame(self, bg="#333333")
        btn_frame.pack(pady=20)
        
        btn_cust = tk.Button(btn_frame, text="Customer Area", font=("Arial", 16), width=20, 
                             command=lambda: controller.show_frame("CustomerScreen"), bg="#4CAF50", fg="blue")
        btn_cust.pack(pady=10)
        
        btn_admin = tk.Button(btn_frame, text="Admin Dashboard", font=("Arial", 16), width=20, 
                              command=self.check_admin_login, bg="#2196F3", fg="blue")
        btn_admin.pack(pady=10)
        
        btn_exit = tk.Button(btn_frame, text="Exit", font=("Arial", 14), width=15, 
                             command=controller.quit, bg="#f44336", fg="blue")
        btn_exit.pack(pady=30)

    def check_admin_login(self):
        pwd = simpledialog.askstring("Admin Login", "Enter Password:", show='*')
        if pwd == ADMIN_PASSWORD:
            self.controller.show_frame("AdminScreen")
        elif pwd is not None:
            messagebox.showerror("Error", "Incorrect Password")


class CustomerScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.cart = {}
        
        # Header
        header = tk.Frame(self, bg="#4CAF50", height=60)
        header.pack(fill="x")
        tk.Button(header, text="< Back", command=lambda: controller.show_frame("MainScreen"), bg="white").pack(side="left", padx=10, pady=10)
        tk.Label(header, text="Customer Menu", font=("Arial", 18, "bold"), bg="#4CAF50", fg="white").pack(side="left", padx=20)
        
        # Content Layout: Left (Menu), Right (Cart/Status)
        content = tk.Frame(self)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- LEFT: Menu ---
        left_frame = tk.LabelFrame(content, text="Menu", font=("Arial", 12, "bold"))
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Treeview for Menu
        cols = ('Item', 'Price')
        self.tree_menu = ttk.Treeview(left_frame, columns=cols, show='headings')
        self.tree_menu.heading('Item', text='Item Name')
        self.tree_menu.heading('Price', text='Price ($)')
        self.tree_menu.column('Item', width=150)
        self.tree_menu.column('Price', width=80)
        self.tree_menu.pack(fill="both", expand=True, pady=5)
        
        # Add to Cart Controls
        add_frame = tk.Frame(left_frame)
        add_frame.pack(fill="x", pady=5)
        tk.Label(add_frame, text="Qty:").pack(side="left", padx=5)
        self.spin_qty = tk.Spinbox(add_frame, from_=1, to=10, width=5)
        self.spin_qty.pack(side="left", padx=5)
        tk.Button(add_frame, text="Add to Cart", command=self.add_to_cart, bg="#FFC107").pack(side="left", padx=5)

        # --- RIGHT: Cart & Status ---
        right_frame = tk.Frame(content)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Cart Section
        cart_frame = tk.LabelFrame(right_frame, text="Your Cart", font=("Arial", 12, "bold"))
        cart_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.list_cart = tk.Listbox(cart_frame, height=10)
        self.list_cart.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.lbl_total = tk.Label(cart_frame, text="Total: $0.00", font=("Arial", 12, "bold"), fg="red")
        self.lbl_total.pack(anchor="e", padx=10)
        
        tk.Button(cart_frame, text="Place Order", command=self.place_order, bg="#4CAF50", fg="white", font=("Arial", 12, "bold")).pack(fill="x", padx=5, pady=5)
        
        # Order Status Section
        status_frame = tk.LabelFrame(right_frame, text="Check Order Status", font=("Arial", 12, "bold"))
        status_frame.pack(fill="x")
        
        tk.Label(status_frame, text="Order ID:").pack(anchor="w", padx=5)
        self.entry_oid = tk.Entry(status_frame)
        self.entry_oid.pack(fill="x", padx=5, pady=5)
        tk.Button(status_frame, text="Check Status", command=self.check_status).pack(fill="x", padx=5, pady=5)

    def refresh(self):
        # Reload Menu
        self.cart = {}
        self.update_cart_display()
        for item in self.tree_menu.get_children():
            self.tree_menu.delete(item)
        
        menu = self.controller.data['menu']
        for item, price in menu.items():
            self.tree_menu.insert("", "end", values=(item, f"{price:.2f}"))

    def add_to_cart(self):
        selected = self.tree_menu.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item from the menu.")
            return
        
        item_values = self.tree_menu.item(selected[0], 'values')
        item_name = item_values[0]
        qty = int(self.spin_qty.get())
        
        self.cart[item_name] = self.cart.get(item_name, 0) + qty
        self.update_cart_display()

    def update_cart_display(self):
        self.list_cart.delete(0, tk.END)
        total = 0
        menu = self.controller.data['menu']
        
        for item, qty in self.cart.items():
            price = menu.get(item, 0)
            cost = price * qty
            total += cost
            self.list_cart.insert(tk.END, f"{item} x{qty} - ${cost:.2f}")
            
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    def place_order(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add items before placing order.")
            return
            
        menu = self.controller.data['menu']
        total = sum(menu[item] * qty for item, qty in self.cart.items())
        
        oid = self.controller.generate_order_id()
        
        new_order = {
            "items": self.cart,
            "total": total,
            "status": "Pending"
        }
        
        self.controller.data['orders'][oid] = new_order
        self.controller.save_data()
        
        messagebox.showinfo("Success", f"Order Placed!\nYour Order ID is: {oid}\nPlease save this ID.")
        self.cart = {}
        self.update_cart_display()

    def check_status(self):
        oid = self.entry_oid.get().strip().upper()
        orders = self.controller.data['orders']
        
        if oid in orders:
            status = orders[oid]['status']
            msg = f"Status: {status}\n"
            if status == "Pending": msg += "Waiting for admin approval."
            elif status == "Accepted": msg += "Being prepared!"
            elif status == "Cancelled": msg += "Order was cancelled."
            messagebox.showinfo(f"Order {oid}", msg)
        else:
            messagebox.showerror("Error", "Order ID not found.")


class AdminScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = tk.Frame(self, bg="#2196F3", height=60)
        header.pack(fill="x")
        tk.Button(header, text="Logout", command=lambda: controller.show_frame("MainScreen"), bg="white").pack(side="right", padx=10, pady=10)
        tk.Label(header, text="Admin Dashboard", font=("Arial", 18, "bold"), bg="#2196F3", fg="white").pack(side="left", padx=20)
        
        # Tabs
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Manage Orders
        self.tab_orders = tk.Frame(tabs)
        tabs.add(self.tab_orders, text="Manage Orders")
        self.setup_orders_tab()
        
        # Tab 2: Manage Menu
        self.tab_menu = tk.Frame(tabs)
        tabs.add(self.tab_menu, text="Manage Menu")
        self.setup_menu_tab()

    def setup_orders_tab(self):
        # Order List
        cols = ('ID', 'Status', 'Total', 'Items')
        self.tree_orders = ttk.Treeview(self.tab_orders, columns=cols, show='headings')
        self.tree_orders.heading('ID', text='Order ID')
        self.tree_orders.heading('Status', text='Status')
        self.tree_orders.heading('Total', text='Total ($)')
        self.tree_orders.heading('Items', text='Items')
        self.tree_orders.column('ID', width=60)
        self.tree_orders.column('Status', width=80)
        self.tree_orders.column('Total', width=80)
        self.tree_orders.column('Items', width=300)
        self.tree_orders.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(self.tab_orders)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="Accept Order", bg="#4CAF50", fg="white", command=self.accept_order).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel Order", bg="#f44336", fg="white", command=self.cancel_order).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh List", command=self.refresh_orders).pack(side="right", padx=5)

    def setup_menu_tab(self):
        # Split: List on left, Inputs on right
        content = tk.Frame(self.tab_menu)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # List
        cols = ('Item', 'Price')
        self.tree_admin_menu = ttk.Treeview(content, columns=cols, show='headings')
        self.tree_admin_menu.heading('Item', text='Item Name')
        self.tree_admin_menu.heading('Price', text='Price ($)')
        self.tree_admin_menu.pack(side="left", fill="both", expand=True)
        
        # Controls
        ctrl_frame = tk.Frame(content)
        ctrl_frame.pack(side="right", fill="y", padx=10)
        
        tk.Label(ctrl_frame, text="Item Name:").pack(anchor="w")
        self.entry_item_name = tk.Entry(ctrl_frame)
        self.entry_item_name.pack(fill="x", pady=5)
        
        tk.Label(ctrl_frame, text="Price:").pack(anchor="w")
        self.entry_item_price = tk.Entry(ctrl_frame)
        self.entry_item_price.pack(fill="x", pady=5)
        
        tk.Button(ctrl_frame, text="Add / Update", bg="#2196F3", fg="white", command=self.upsert_item).pack(fill="x", pady=10)
        tk.Button(ctrl_frame, text="Delete Selected", bg="#f44336", fg="white", command=self.delete_item).pack(fill="x", pady=10)

    def refresh(self):
        self.refresh_orders()
        self.refresh_menu()

    def refresh_orders(self):
        for item in self.tree_orders.get_children():
            self.tree_orders.delete(item)
        
        orders = self.controller.data['orders']
        # Show pending first
        for oid, details in orders.items():
            items_str = ", ".join([f"{k} x{v}" for k, v in details['items'].items()])
            self.tree_orders.insert("", "end", values=(oid, details['status'], f"{details['total']:.2f}", items_str))

    def refresh_menu(self):
        for item in self.tree_admin_menu.get_children():
            self.tree_admin_menu.delete(item)
        
        menu = self.controller.data['menu']
        for item, price in menu.items():
            self.tree_admin_menu.insert("", "end", values=(item, f"{price:.2f}"))

    def accept_order(self):
        selected = self.tree_orders.selection()
        if not selected: return
        
        item = self.tree_orders.item(selected[0])
        oid = item['values'][0]
        
        self.controller.data['orders'][oid]['status'] = "Accepted"
        self.controller.save_data()
        self.refresh_orders()
        messagebox.showinfo("Done", f"Order {oid} Accepted.")

    def cancel_order(self):
        selected = self.tree_orders.selection()
        if not selected: return
        
        item = self.tree_orders.item(selected[0])
        oid = item['values'][0]
        
        self.controller.data['orders'][oid]['status'] = "Cancelled"
        self.controller.save_data()
        self.refresh_orders()
        messagebox.showinfo("Done", f"Order {oid} Cancelled.")

    def upsert_item(self):
        name = self.entry_item_name.get().strip()
        price_str = self.entry_item_price.get().strip()
        
        if not name or not price_str:
            messagebox.showerror("Error", "Fill both fields.")
            return
            
        try:
            price = float(price_str)
            self.controller.data['menu'][name] = price
            self.controller.save_data()
            self.refresh_menu()
            self.entry_item_name.delete(0, tk.END)
            self.entry_item_price.delete(0, tk.END)
            messagebox.showinfo("Success", f"Updated {name}")
        except ValueError:
            messagebox.showerror("Error", "Price must be a number.")

    def delete_item(self):
        selected = self.tree_admin_menu.selection()
        if not selected: return
        
        item_values = self.tree_admin_menu.item(selected[0], 'values')
        name = item_values[0]
        
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            del self.controller.data['menu'][name]
            self.controller.save_data()
            self.refresh_menu()

if __name__ == "__main__":
    app = CafeSystemGUI()
    app.mainloop()
