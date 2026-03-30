import requests

BASE_URL = "http://127.0.0.1:8000"


def search_items():
    q = input("Enter search term: ").strip()
    response = requests.get(f"{BASE_URL}/search", params={"q": q})
    print("\nSearch Results:")
    if response.status_code == 200:
        items = response.json()
        for item in items:
            print(
                f"ID: {item['id']} | "
                f"{item['title']} by {item['author']} | "
                f"Genre: {item['genre']} | "
                f"Type: {item['media_type']} | "
                f"Availability: {item['availability']}"
            )
    else:
        print("Error:", response.text)
    print()


def view_profile():
    user_id = input("Enter user ID: ").strip()
    response = requests.get(f"{BASE_URL}/profile/{user_id}")
    print("\nProfile:")
    if response.status_code == 200:
        profile = response.json()
        print(f"ID: {profile['id']}")
        print(f"Name: {profile['full_name']}")
        print(f"Email: {profile['email']}")
        print(f"Status: {profile['account_status']}")
        print(f"Max Loans: {profile['max_loans']}")
    else:
        print("Error:", response.text)
    print()


def borrow_item():
    user_id = int(input("Enter user ID: ").strip())
    item_id = int(input("Enter item ID to borrow: ").strip())
    response = requests.post(
        f"{BASE_URL}/borrow",
        json={"user_id": user_id, "item_id": item_id}
    )
    print("\nBorrow Result:")
    print(response.text)
    print()


def return_item():
    user_id = int(input("Enter user ID: ").strip())
    item_id = int(input("Enter item ID to return: ").strip())
    response = requests.post(
        f"{BASE_URL}/return",
        json={"user_id": user_id, "item_id": item_id}
    )
    print("\nReturn Result:")
    print(response.text)
    print()


def reserve_item():
    user_id = int(input("Enter user ID: ").strip())
    item_id = int(input("Enter item ID to reserve: ").strip())
    response = requests.post(
        f"{BASE_URL}/reserve",
        json={"user_id": user_id, "item_id": item_id}
    )
    print("\nReservation Result:")
    print(response.text)
    print()


def recommendations():
    user_id = input("Enter user ID: ").strip()
    response = requests.get(f"{BASE_URL}/recommend/{user_id}")
    print("\nRecommendations:")
    if response.status_code == 200:
        items = response.json()
        for item in items:
            print(
                f"ID: {item['id']} | "
                f"{item['title']} by {item['author']} | "
                f"Genre: {item['genre']}"
            )
    else:
        print("Error:", response.text)
    print()


def main():
    while True:
        print("=== Library Management System ===")
        print("1. Search Catalog")
        print("2. View User Profile")
        print("3. Borrow Item")
        print("4. Return Item")
        print("5. Reserve Item")
        print("6. View Recommendations")
        print("7. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            search_items()
        elif choice == "2":
            view_profile()
        elif choice == "3":
            borrow_item()
        elif choice == "4":
            return_item()
        elif choice == "5":
            reserve_item()
        elif choice == "6":
            recommendations()
        elif choice == "7":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()