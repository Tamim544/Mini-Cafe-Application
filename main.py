import json
import os
import random
import string

DATA_FILE = "data.json"
ADMIN_PASSWORD = "admin"  

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"menu": {}, "orders": {}}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# --- Admin Functions ---

def admin_menu(data):
    while True:
        print("\n=== ADMIN DASHBOARD ===")
        print("1. Manage Menu (Add/Update Item)")
        print("2. Remove Item from Menu")
        print("3. Manage Orders (Accept/Cancel)")
        print("4. View All Orders")
        print("5. Logout")
        
        choice = input("Enter choice: ")
        
        if choice == '1':
            name = input("Enter item name: ").strip()
            if not name: continue
            try:
                price = float(input(f"Enter price for '{name}': "))
                data['menu'][name] = price
                save_data(data)
                print(f"✅ Menu updated: {name} - ${price:.2f}")
            except ValueError:
                print("❌ Invalid price.")

        elif choice == '2':
            name = input("Enter item name to remove: ").strip()
            if name in data['menu']:
                del data['menu'][name]
                save_data(data)
                print(f"✅ Removed {name} from menu.")
            else:
                print("❌ Item not found.")

        elif choice == '3':
            # Manage Pending Orders
            pending_orders = {oid: details for oid, details in data['orders'].items() if details['status'] == 'Pending'}
            
            if not pending_orders:
                print("\nNo pending orders.")
                continue
                
            print("\n--- Pending Orders ---")
            for oid, details in pending_orders.items():
                items_str = ", ".join([f"{item} (x{qty})" for item, qty in details['items'].items()])
                print(f"ID: {oid} | Total: ${details['total']:.2f} | Items: {items_str}")
            
            oid = input("\nEnter Order ID to manage (or 'b' to back): ").strip().upper()
            if oid == 'B': continue
            
            if oid in pending_orders:
                action = input("Accept (a) or Cancel (c)? ").lower()
                if action == 'a':
                    data['orders'][oid]['status'] = 'Accepted'
                    print(f"✅ Order {oid} ACCEPTED.")
                elif action == 'c':
                    data['orders'][oid]['status'] = 'Cancelled'
                    print(f"❌ Order {oid} CANCELLED.")
                else:
                    print("Invalid action.")
                save_data(data)
            else:
                print("Invalid Order ID.")

        elif choice == '4':
            print("\n--- All Orders ---")
            if not data['orders']:
                print("No orders history.")
            for oid, details in data['orders'].items():
                print(f"ID: {oid} | Status: {details['status']} | Total: ${details['total']:.2f}")

        elif choice == '5':
            break
        else:
            print("Invalid choice.")

# --- Customer Functions ---

def customer_menu(data):
    while True:
        print("\n=== CUSTOMER MENU ===")
        print("1. View Menu")
        print("2. Place Order")
        print("3. Check Order Status")
        print("4. Back to Main")
        
        choice = input("Enter choice: ")
        
        if choice == '1':
            print("\n--- MENU ---")
            for item, price in data['menu'].items():
                print(f"{item}: ${price:.2f}")
        
        elif choice == '2':
            if not data['menu']:
                print("\nMenu is empty! Please ask admin to add items.")
                continue
                
            cart = {}
            while True:
                print("\n--- MENU ---")
                menu_list = list(data['menu'].items())
                for idx, (item, price) in enumerate(menu_list, 1):
                    print(f"{idx}. {item} (${price:.2f})")
                print("D. Done Ordering")
                
                sel = input("Select item number (or D): ").strip().upper()
                if sel == 'D':
                    break
                
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(menu_list):
                        item_name = menu_list[idx][0]
                        qty = int(input(f"How many '{item_name}'? "))
                        if qty > 0:
                            cart[item_name] = cart.get(item_name, 0) + qty
                            print(f"Added {qty} {item_name}(s) to cart.")
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Invalid input.")
            
            if cart:
                total = sum(data['menu'][item] * qty for item, qty in cart.items())
                print(f"\nYour Total: ${total:.2f}")
                confirm = input("Place order? (y/n): ").lower()
                if confirm == 'y':
                    order_id = generate_order_id()
                    data['orders'][order_id] = {
                        "items": cart,
                        "total": total,
                        "status": "Pending"
                    }
                    save_data(data)
                    print(f"✅ Order Placed! Your Order ID is: {order_id}")
                    print("Please keep this ID to check your status.")
            else:
                print("Cart is empty.")

        elif choice == '3':
            oid = input("Enter your Order ID: ").strip().upper()
            if oid in data['orders']:
                status = data['orders'][oid]['status']
                print(f"\nOrder Status for {oid}: [{status}]")
                if status == 'Pending':
                    print("Your order is waiting for admin approval.")
                elif status == 'Accepted':
                    print("Your order is being prepared!")
                elif status == 'Cancelled':
                    print("Sorry, your order was cancelled by the cafe.")
            else:
                print("❌ Order ID not found.")

        elif choice == '4':
            break
        else:
            print("Invalid choice.")

def main():
    print("Welcome to Python Cafe System")
    while True:
        data = load_data() # Reload data every time to keep sync simple
        print("\n=== MAIN SCREEN ===")
        print("1. Customer Login")
        print("2. Admin Login")
        print("3. Exit")
        
        choice = input("Select Role: ")
        
        if choice == '1':
            customer_menu(data)
        elif choice == '2':
            pwd = input("Enter Admin Password: ")
            if pwd == ADMIN_PASSWORD:
                admin_menu(data)
            else:
                print("❌ Wrong Password!")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
