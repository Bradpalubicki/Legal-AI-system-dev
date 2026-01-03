#!/usr/bin/env python3
"""Test registration with frontend format"""
import requests
import json

url = "http://localhost:8000/api/v1/auth/register"
data = {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "role": "ATTORNEY",
    "termsAccepted": True,
    "acceptedDocuments": []
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        print("\n[OK] Registration successful!")
        print(f"User: {response.json()['user']['full_name']}")
        print(f"Role: {response.json()['user']['role']}")
        print(f"Email: {response.json()['user']['email']}")
except Exception as e:
    print(f"Error: {e}")
