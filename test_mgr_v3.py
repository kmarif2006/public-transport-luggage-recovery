import requests

BASE_URL = "http://localhost:5000/api"

def test_manager_login():
    print("--- Testing Manager Login (v3) ---")
    # Combination: lower case email, uppercase D in password (as per script)
    login_data = {
        "email": "manager.d001@tnstc.gov.in",
        "password": "D001_pass123"
    }
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        
        if r.status_code == 200:
            print("SUCCESS: Manager logged in!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manager_login()
