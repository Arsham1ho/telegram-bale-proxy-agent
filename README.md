# Telegram-to-Bale V2Ray Proxy Config Forwarder

An open-source Python agent that automatically monitors Telegram channels for V2Ray & proxy configs and forwards them to Bale messenger in real-time.

It detects vmess, vless, ss, trojan, reality, hysteria, wireguard & Telegram proxy links — deduplicates them so you never get repeats.

## How It Works

- **Telethon** listens to 13+ Telegram proxy channels
- **Regex engine** extracts proxy configs from every new message
- **SHA-256 hashing** prevents duplicate sends
- **Playwright** automates Bale web to deliver configs instantly

## Supported Protocols

| Protocol | Example |
|---|---|
| VMess | `vmess://...` |
| VLESS | `vless://...` |
| Shadowsocks | `ss://...` |
| Trojan | `trojan://...` |
| Reality | `reality://...` |
| Hysteria2 | `hy2://...` / `hysteria2://...` |
| Hysteria | `hysteria://...` |
| WireGuard | `wireguard://...` |
| Telegram Proxy | `tg://proxy?...` / `https://t.me/proxy?...` |
| Raw JSON V2Ray | JSON objects with v/ps/add/port keys |

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/Arsham1ho/telegram-bale-proxy-agent.git
cd telegram-bale-proxy-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your credentials:

- **Telegram API credentials**: Get `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org)
- **Channels**: Add Telegram channel usernames to monitor (e.g., `@v2rayng_org`)
- **Bale target**: Set the Bale chat URL (e.g., `https://web.bale.ai/chat?uid=XXXXXXXXXX`)

### 3. Authenticate Telegram (one-time)

```bash
python auth_telegram.py
```

Enter your phone number and the verification code. The session is saved so you won't need to do this again.

### 4. Run

```bash
python main.py
```

On first run, a browser window opens for Bale — log in manually once. After that, the session is saved and the agent runs fully automatically.

## Architecture

```
Telegram Channels
        |
        v
  Telethon Listener (events.NewMessage)
        |
        v
  Config Detector (regex extraction)
        |
        v
  Dedup Store (SQLite + SHA-256)
        |
        v
  Bale Sender (Playwright browser automation)
        |
        v
  Bale Chat
```

## File Structure

```
├── main.py                # Entry point, wires everything together
├── config.py              # Loads settings from config.yaml
├── config.yaml.example    # Template config (committed to git)
├── config.yaml            # Your config with secrets (gitignored)
├── telegram_listener.py   # Telethon channel monitor
├── config_detector.py     # Regex parser for proxy configs
├── bale_sender.py         # Playwright browser automation
├── dedup.py               # SQLite dedup store
├── auth_telegram.py       # One-time Telegram authentication
├── requirements.txt       # Python dependencies
└── data/                  # Runtime data (auto-created, gitignored)
    ├── session.session    # Telethon session
    ├── bale_browser/      # Playwright browser profile
    └── seen_configs.db    # Dedup database
```

## Requirements

- Python 3.9+
- A Telegram account (not a bot — uses user API)
- A Bale account
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)

## License

MIT
