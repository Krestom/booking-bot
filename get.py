import requests

url = "https://n1340880.yclients.com/company/1219726/create-record/record?o=s18505562d2503041700"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    html_content = response.text
    print(html_content)  # Печатаем первые 1000 символов
else:
    print(f"Ошибка: {response.status_code}")