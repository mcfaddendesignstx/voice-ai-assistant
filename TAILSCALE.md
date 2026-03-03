# Tailscale Setup — Remote Access to Your Voice Assistant

Tailscale creates a private VPN mesh between your devices. Your iPhone can
reach your Windows Docker host from anywhere (coffee shop, cellular, etc.)
without exposing ports to the public internet.

---

## How It Works

```
iPhone (Tailscale IP: 100.x.x.1)
    │
    │  Encrypted WireGuard tunnel (automatic)
    │
Windows PC (Tailscale IP: 100.x.x.2)
    │
    ├── LiveKit Server  :7880
    ├── Token Server    :8081
    └── WebRTC UDP      :50000-50020
```

Tailscale assigns each device a stable `100.x.x.x` IP. Traffic between
them is end-to-end encrypted. No port forwarding, no firewall rules needed.

---

## Step 1: Create a Tailscale Account

1. Go to [https://tailscale.com](https://tailscale.com)
2. Sign up with Google, Microsoft, or GitHub
3. Free tier supports up to 100 devices — more than enough

## Step 2: Install on Windows PC (Docker Host)

1. Download Tailscale from [https://tailscale.com/download/windows](https://tailscale.com/download/windows)
2. Install and sign in
3. Tailscale icon appears in the system tray — click it and confirm it's "Connected"
4. Note your Tailscale IP:
   ```powershell
   tailscale ip -4
   ```
   Example output: `100.64.0.2`

## Step 3: Install on iPhone

1. Download **Tailscale** from the App Store
2. Open it and sign in with the same account
3. Toggle the VPN on
4. Note the iPhone's Tailscale IP (shown in the app)

## Step 4: Verify Connectivity

From your iPhone, open Safari and visit:
```
http://100.64.0.2:8081/health
```
(Replace with your PC's Tailscale IP)

Expected: `{"status": "ok"}`

If this doesn't work:
- Check both devices show as "Connected" in the Tailscale admin console
- Windows Firewall may block connections — see Step 6

## Step 5: Update Configuration

### On the Windows PC

Edit `.env`:
```env
LIVEKIT_EXTERNAL_URL=ws://100.64.0.2:7880
```

Restart the token server so it returns the new URL:
```powershell
docker compose restart token-server
```

### On the iPhone App

1. Open the Voice Assistant app
2. Go to **Settings** tab
3. Change Token Server URL to:
   ```
   http://100.64.0.2:8081
   ```
4. Tap **Save**
5. Go back and tap **Connect**

## Step 6: Windows Firewall Rules

If Tailscale traffic is blocked, add firewall rules:

```powershell
# Run PowerShell as Administrator

# LiveKit HTTP/WebSocket
New-NetFirewallRule -DisplayName "LiveKit HTTP" -Direction Inbound -Protocol TCP -LocalPort 7880 -Action Allow

# LiveKit TCP ICE
New-NetFirewallRule -DisplayName "LiveKit TCP" -Direction Inbound -Protocol TCP -LocalPort 7881 -Action Allow

# LiveKit WebRTC UDP
New-NetFirewallRule -DisplayName "LiveKit UDP" -Direction Inbound -Protocol UDP -LocalPort 50000-50020 -Action Allow

# Token Server
New-NetFirewallRule -DisplayName "Token Server" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow
```

## Step 7: LiveKit External IP (Important for WebRTC)

LiveKit needs to know its externally-reachable IP for WebRTC ICE candidates.
Edit `livekit.yaml`:

```yaml
rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 50020
  use_external_ip: true           # ← Change from false to true
  # Optionally force the IP if auto-detection fails:
  # node_ip: 100.64.0.2
```

Restart LiveKit:
```powershell
docker compose restart livekit-server
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| iPhone can't reach token server | Verify both devices are on Tailscale. Try `http://<tailscale-ip>:8081/health` in Safari. |
| Audio connects but no sound | WebRTC UDP might be blocked. Check firewall rules (Step 6). Try TCP fallback by ensuring port 7881 is open. |
| High latency | Tailscale uses direct connections when possible. If relaying through DERP servers, latency increases. Check Tailscale admin for "direct" vs "relay" status. |
| WebRTC fails to connect | Set `use_external_ip: true` and optionally `node_ip: <tailscale-ip>` in `livekit.yaml`. |
| Works on Wi-Fi but not cellular | Ensure Tailscale VPN is active on the iPhone. Check the Tailscale app shows "Connected". |

---

## Security Notes

- Tailscale traffic is **end-to-end encrypted** (WireGuard)
- No ports are exposed to the public internet
- The LiveKit API key/secret are only used between your own devices
- For production use, consider Tailscale ACLs to restrict which devices can access which ports
