"""Quick test of dev account login"""
import requests
import json

# Test login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={
        'email': 'dev@example.com',
        'password': 'devpass123'
    }
)

print("="*80)
print("TESTING DEV ACCOUNT LOGIN")
print("="*80)
print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\nSUCCESS! Login works!")
    print(f"\nUser Info:")
    if 'user' in data:
        print(f"  ID: {data['user'].get('id')}")
        print(f"  Email: {data['user'].get('email')}")
        print(f"  Name: {data['user'].get('full_name')}")
    print(f"\nToken received: {data.get('access_token', 'N/A')[:50]}...")
else:
    print(f"\nFAILED: {response.text}")

print("\n" + "="*80)
