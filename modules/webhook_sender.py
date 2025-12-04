import requests
import threading


def _send(webhook_url: str, content: str):
    try:
        requests.post(
            webhook_url,
            json={"content": content},
            timeout=10
        )
    except Exception:
        print("[ ERROR ] Failed to send log to Discord webhook!")  # im using print instead of logger for a reason, ok?


def send(webhook_url: str, content: str):
    threading.Thread(target=_send, args=(webhook_url, content), daemon=True).start()
