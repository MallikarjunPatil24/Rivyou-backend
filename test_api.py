import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:8000"

def get_random_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

def run_tests():
    # Keep track of results for the summary
    test_results = {}
    
    # Step 1 - Register a user
    register_url = f"{BASE_URL}/api/auth/register/"
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test1234!"
    }
    
    print("\n--- Step 1: Register User ---")
    try:
        print(f"Requesting URL: {register_url}")
        response = requests.post(register_url, json=register_data)
        print(f"Register status: {response.status_code}")
        print("Response Headers:", dict(response.headers))
        print("Response JSON:", response.json())
        
        # If the user already exists, Django returns a 400 Bad Request
        if response.status_code == 201:
            test_results["Step 1 - Register user"] = "PASS"
        elif response.status_code == 400 and "already exists" in str(response.content):
            print("[INFO] User 'testuser' already registered. Proceeding.")
            test_results["Step 1 - Register user"] = "PASS (User already exists)"
        else:
            test_results["Step 1 - Register user"] = "FAIL"
    except Exception as e:
        print(f"Error during registration: {e}")
        test_results["Step 1 - Register user"] = "FAIL"

    # Step 2 - Login and get token
    login_url = f"{BASE_URL}/api/auth/login/"
    login_data = {
        "username": "testuser",
        "password": "Test1234!"
    }
    access_token = None
    
    print("\n--- Step 2: Login ---")
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login status: {response.status_code}")
        
        token_received = "No"
        if response.status_code == 200:
            res_json = response.json()
            access_token = res_json.get("token")
            if access_token:
                token_received = "Yes"
                test_results["Step 2 - Login and get token"] = "PASS"
            else:
                test_results["Step 2 - Login and get token"] = "FAIL (No token in response)"
        else:
            test_results["Step 2 - Login and get token"] = "FAIL"
            
        print(f"Token received: {token_received}")
    except Exception as e:
        print(f"Error during login: {e}")
        test_results["Step 2 - Login and get token"] = "FAIL"

    # Prepare authorization header
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    # Step 3 - Search for "smartphone"
    search_url = f"{BASE_URL}/api/products/search/"
    params = {"q": "smartphone", "limit": 5}
    
    print("\n--- Step 3: Search for 'smartphone' ---")
    try:
        response = requests.get(search_url, headers=headers, params=params)
        print(f"Search status: {response.status_code}")
        
        if response.status_code == 200:
            res_json = response.json()
            total_results = res_json.get("total_results", 0)
            print(f"Total results: {total_results}")
            
            results = res_json.get("results", [])
            for idx, item in enumerate(results, 1):
                name = item.get("product_name")
                cat = item.get("category")
                score = item.get("relevance_score")
                reason = item.get("rank_reason")
                print(f"{idx}. {name} | {cat} | Score: {score} | {reason}")
                
            test_results["Step 3 - Search for 'smartphone'"] = "PASS"
        else:
            test_results["Step 3 - Search for 'smartphone'"] = f"FAIL (Status: {response.status_code})"
    except Exception as e:
        print(f"Error during search: {e}")
        test_results["Step 3 - Search for 'smartphone'"] = "FAIL"

    # Step 4 - Get product by ID (use id=1)
    detail_url = f"{BASE_URL}/api/products/1/"
    
    print("\n--- Step 4: Get product by ID (1) ---")
    try:
        response = requests.get(detail_url, headers=headers)
        print(f"Product detail status: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            print(f"Product Name: {res_json.get('product_name')}")
            print(f"Category: {res_json.get('category')}")
            test_results["Step 4 - Get product by ID"] = "PASS"
        else:
            print(response.json())
            test_results["Step 4 - Get product by ID"] = f"FAIL (Status: {response.status_code})"
    except Exception as e:
        print(f"Error during product detail fetch: {e}")
        test_results["Step 4 - Get product by ID"] = "FAIL"

    # Step 5 - Get products by category
    category_url = f"{BASE_URL}/api/products/category/Smartphones/"
    
    print("\n--- Step 5: Get products by category 'Smartphones' ---")
    try:
        response = requests.get(category_url, headers=headers)
        print(f"Category search status: {response.status_code}")
        if response.status_code == 200:
            products_list = response.json()
            print(f"Products in Smartphones: {len(products_list)}")
            test_results["Step 5 - Get products by category"] = "PASS"
        else:
            test_results["Step 5 - Get products by category"] = f"FAIL (Status: {response.status_code})"
    except Exception as e:
        print(f"Error during category search: {e}")
        test_results["Step 5 - Get products by category"] = "FAIL"

    # Step 6 - Test unauthorized access (no token)
    print("\n--- Step 6: Test unauthorized access (no token) ---")
    try:
        # Request without header
        response = requests.get(search_url, params={"q": "smartphone"})
        print(f"Unauthorized status: {response.status_code}")
        if response.status_code == 401:
            test_results["Step 6 - Test unauthorized access"] = "PASS"
        else:
            test_results["Step 6 - Test unauthorized access"] = f"FAIL (Expected 401, got {response.status_code})"
    except Exception as e:
        print(f"Error during unauthorized check: {e}")
        test_results["Step 6 - Test unauthorized access"] = "FAIL"

    # Step 7 - Get Search History / Analytics
    analytics_url = f"{BASE_URL}/api/analytics/history/"
    print("\n--- Step 7: Get Search History/Analytics ---")
    try:
        response = requests.get(analytics_url, headers=headers)
        print(f"Analytics status: {response.status_code}")
        if response.status_code == 200:
            history = response.json()
            print(f"Total search history records: {len(history)}")
            for idx, log in enumerate(history, 1):
                print(f"  {idx}. Query: '{log.get('query')}' | Results: {log.get('results_count')} | Created At: {log.get('created_at')}")
            test_results["Step 7 - Get Search History/Analytics"] = "PASS"
        else:
            test_results["Step 7 - Get Search History/Analytics"] = f"FAIL (Status: {response.status_code})"
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        test_results["Step 7 - Get Search History/Analytics"] = "FAIL"

    # Print Summary
    print("\n" + "=" * 19 + " TEST SUMMARY " + "=" * 19)
    for test, status_res in test_results.items():
        print(f"{test:<35}: {status_res}")
    print("=" * 52)

if __name__ == "__main__":
    run_tests()
