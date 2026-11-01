import requests

stream_url = "https://s1.worldcam.live:8082/aleksandrow-lodzki-dmowskiego-konstantynowska/index.m3u8?token=TWOJ_AKTUALNY_TOKEN"
response = requests.get(stream_url, headers={"User-Agent": "Mozilla/5.0"})

print(f"Status kod: {response.status_code}")
print(response.text[:200])  # Pokaże początek pliku manifestu, jeśli jest OK