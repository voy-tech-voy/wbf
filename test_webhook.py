import requests

url = "http://127.0.0.1:5005/api/v1/webhooks/gumroad"

data = {
    "email": "webhook_test@example.com",
    "full_name": "Webhook Tester",
    "product_name": "ImageWave Converter"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
