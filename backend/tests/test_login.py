#!/usr/bin/env python3
"""Test user login"""
import requests
import json

url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "mynewaccount@test.com",
    "password": "MyPassword123!"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("\n✅ Login successful!")
        print(f"Access Token: {response.json()['access_token'][:50]}...")
        print(f"User ID: {response.json()['user']['id']}")
        print(f"Email: {response.json()['user']['email']}")
        print(f"Role: {response.json()['user']['role']}")
except Exception as e:
    print(f"Error: {e}")
