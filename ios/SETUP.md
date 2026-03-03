# iOS App — Xcode Project Setup

Step-by-step instructions to create the Xcode project from these source files.

**Prerequisites:**
- Mac with Xcode 15.0+ installed (free from the Mac App Store)
- Apple ID (free tier is fine for testing on your own device)
- iPhone running iOS 17.0+
- Both Mac and iPhone on the same Wi-Fi as your Windows Docker host (or both on Tailscale)

---

## Step 1: Create a New Xcode Project

1. Open Xcode
2. **File → New → Project...**
3. Choose **iOS → App**, click **Next**
4. Fill in:
   - **Product Name:** `VoiceAssistant`
   - **Organization Identifier:** `com.yourname` (any reverse-DNS string)
   - **Interface:** `SwiftUI`
   - **Language:** `Swift`
   - **Storage:** `None`
5. Click **Next**, choose a location, click **Create**

## Step 2: Add the LiveKit Swift SDK via SPM

1. In Xcode, go to **File → Add Package Dependencies...**
2. In the search bar, paste: `https://github.com/livekit/client-sdk-swift.git`
3. Set **Dependency Rule** to **Up to Next Major Version**, starting from `2.0.0`
4. Click **Add Package**
5. When prompted, check the **LiveKit** library, click **Add Package**

## Step 3: Replace the Generated Source Files

Xcode created some default files. Replace them with the files from this folder:

1. **Delete** the auto-generated `ContentView.swift` and `VoiceAssistantApp.swift` from the Xcode project navigator (choose "Move to Trash")

2. **Drag and drop** the entire `VoiceAssistant/` folder contents into the Xcode project navigator:
   - `VoiceAssistantApp.swift`
   - `Config.swift`
   - `Models/` folder
   - `Services/` folder
   - `ViewModels/` folder
   - `Views/` folder

3. When Xcode asks, ensure:
   - **Copy items if needed** is checked
   - **Create groups** is selected
   - **Add to targets: VoiceAssistant** is checked

## Step 4: Configure Info.plist

1. In the project navigator, click on the **VoiceAssistant** project (top-level blue icon)
2. Select the **VoiceAssistant** target
3. Go to the **Info** tab
4. Under **Custom iOS Target Properties**, add these keys manually, OR:
5. Replace the auto-generated `Info.plist` with the one from this folder

The key entries needed are:
- `NSMicrophoneUsageDescription` — Microphone access reason
- `NSLocalNetworkUsageDescription` — Local network reason
- `NSAppTransportSecurity` → `NSAllowsArbitraryLoads = YES` — Allows HTTP (not just HTTPS)

## Step 5: Configure the Server URL

1. Open `Config.swift`
2. Change the default URL to match your Windows PC's IP address:
   ```swift
   ?? "http://192.168.1.100:8081"  // ← Replace with your PC's IP
   ```

**Finding your PC's IP:**
- On your Windows PC, open PowerShell and run: `ipconfig`
- Look for the IPv4 address under your Wi-Fi or Ethernet adapter
- Example: `192.168.1.42`

## Step 6: Run on Your iPhone

1. Connect your iPhone to your Mac via USB cable
2. Select your iPhone as the run destination in the top toolbar
3. If this is your first time:
   - Xcode may prompt you to enable Developer Mode on the iPhone
   - Go to **iPhone Settings → Privacy & Security → Developer Mode → Enable**
   - You may need to trust your developer certificate: **iPhone Settings → General → VPN & Device Management**
4. Click the **Run** button (▶) or press `Cmd + R`
5. The app will build, install, and launch on your iPhone

## Step 7: First Run

1. The app opens on the **Connect** screen
2. Verify the token server URL is correct (matches your Docker host IP)
3. Tap **Connect**
4. iOS will prompt for **microphone permission** — tap Allow
5. The app connects to LiveKit, the agent joins, and you should hear a greeting

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not connect to token server" | Check the IP in Settings. Make sure Docker is running and port 8081 is accessible. Try `curl http://<ip>:8081/health` from Mac. |
| "Microphone permission denied" | Go to iPhone Settings → VoiceAssistant → Microphone → Enable |
| App crashes on launch | Make sure you're targeting iOS 17.0+ in project settings |
| "Untrusted Developer" on iPhone | iPhone Settings → General → VPN & Device Management → Trust |
| No audio from agent | Check that Kokoro TTS is running: `docker compose logs kokoro` |
| Agent never joins | Check agent logs: `docker compose logs agent` |
