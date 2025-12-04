import requests

API_URL = "https://imgur.plen.io/api/trpc/imgur.getLinks?batch=1"
ALBUM_URL = "https://imgur.com/a/hw-swap-11-25-25-gX3fKiT"

HEADERS = {
    "content-type": "application/json",
    "origin": "https://imgur.plen.io",
    "referer": "https://imgur.plen.io/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

PAYLOAD = {
    "0": {
        "json": {
            "url": ALBUM_URL,
        }
    }
}


def burst_test():
    for i in range(20):
        try:
            r = requests.post(API_URL, headers=HEADERS, json=PAYLOAD)
            print(f"[{i + 1}] status:", r.status_code)

            if r.status_code in (429, 403):
                print("\n--- Rate Limited ---")
                print("Response Text:", r.text)
                print("Response Headers:", r.headers)
                return True

        except Exception as e:
            print("Error:", e)

    print("First 20 requests succeeded without rate limiting. Trying again...")
    return False


if __name__ == "__main__":
    while True:
        if burst_test():
            break
