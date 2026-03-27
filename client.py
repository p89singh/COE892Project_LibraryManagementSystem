import requests
import sys

# Point this to your FastAPI Gateway address
GATEWAY_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'-'*40}")
    print(f"{title.center(40)}")
    print(f"{'-'*40}")

def search_catalog():
    print_header("Search Catalog & View Availability")
    query = input("Enter book title, author, or keyword: ")
    
    try:
        # Route through the API Gateway
        response = requests.get(f"{GATEWAY_URL}/search", params={"q": query})
        
        if response.status_code == 200:
            results = response.json()
            if not results:
                print("No items found matching your query.")
                return
            
            print("\n--- Search Results ---")
            for item in results:
                status = "Available" if item.get('available') else "Checked Out"
                print(f"ID: {item.get('id')} | Title: {item.get('title')} | Status: {status}")
        else:
            print(f"System Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException:
        print("[!] Error: Could not connect to the API Gateway. Is it running?")

def borrow_item():
    print_header("Borrow / Reserve Item")
    user_id = input("Enter your User ID: ")
    item_id = input("Enter the Item ID you wish to borrow: ")
    
    if not user_id.isdigit() or not item_id.isdigit():
        print("[!] Invalid input. IDs must be numeric.")
        return

    try:
        # Route through the API Gateway to the Circulation Engine
        response = requests.post(
            f"{GATEWAY_URL}/borrow", 
            params={"user_id": int(user_id), "item_id": int(item_id)}
        )
        
        # Clear system feedback based on response
        if response.status_code == 200:
            print(f"[SUCCESS] Item {item_id} successfully borrowed by User {user_id}!")
            print("A notification has been triggered in the background.")
        elif response.status_code == 409:
            print(f"[!] Conflict: Item {item_id} is already checked out or unavailable.")
        else:
            print(f"[!] Failed to borrow item. Error: {response.json().get('detail')}")
            
    except requests.exceptions.RequestException:
        print("[!] Error: Could not connect to the API Gateway.")

def view_profile():
    print_header("View User Profile")
    user_id = input("Enter your User ID: ")
    
    try:
        response = requests.get(f"{GATEWAY_URL}/profile/{user_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"Name: {data.get('name')}")
            print(f"Active Borrows: {len(data.get('borrowed_items', []))}")
        else:
            print(f"[!] Error: {response.json().get('detail')}")
    except requests.exceptions.RequestException:
        print("[!] Error: Could not connect to the API Gateway.")

def main_menu():
    while True:
        print_header("Automated Public Library System")
        print("1. Search Catalog & View Availability")
        print("2. Borrow an Item")
        print("3. View User Profile")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ")
        
        if choice == '1':
            search_catalog()
        elif choice == '2':
            borrow_item()
        elif choice == '3':
            view_profile()
        elif choice == '4':
            print("Exiting system. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid selection. Please choose 1-4.")

if __name__ == "__main__":
    # Ensure dependencies are noted for the README
    # pip install requests
    main_menu()