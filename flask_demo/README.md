# Flask Demo — "hands-on 1"

A minimal Flask web app served on port 8000, accessible from your local network.

## Setup

```bash
cd flask_demo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

The app listens on `0.0.0.0:8000`, so it is reachable from other devices on the same network.

- On this machine: http://localhost:8000
- From other devices: http://<your-ip-address>:8000

Find your local IP address (macOS):

```bash
ipconfig getifaddr en0
```

## Notes

- If the page is not reachable from other devices, allow inbound connections on port 8000 (macOS: System Settings → Network → Firewall) or try `python app.py` once and approve the firewall prompt.
- `debug=True` is for development only; disable it for any real deployment.
