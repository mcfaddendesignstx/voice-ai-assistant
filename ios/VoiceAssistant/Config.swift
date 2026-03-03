// Config.swift
// Central place for server URLs and constants.
//
// Why a separate config file?
//   Keeps magic strings out of view code. When you switch from LAN to
//   Tailscale, you only change values here (or in SettingsView).

import Foundation

enum AppConfig {
    // Token server URL — this is the FastAPI service running in Docker.
    // The iOS app calls this to get a LiveKit JWT before connecting.
    //
    // For local Wi-Fi:  http://<your-pc-ip>:8081
    // For Tailscale:    http://<tailscale-ip>:8081
    //
    // UserDefaults lets the user change this in SettingsView at runtime.
    static var tokenServerURL: String {
        get {
            UserDefaults.standard.string(forKey: "tokenServerURL")
                ?? "http://192.168.86.238:8082"
        }
        set {
            UserDefaults.standard.set(newValue, forKey: "tokenServerURL")
        }
    }

    // Default room name — all participants in the same room hear each other.
    // The agent auto-joins any room, so this just needs to be consistent.
    static let defaultRoomName = "voice-room"

    // Participant identity — identifies this device to the server.
    static var participantIdentity: String {
        "iphone-\(UIDevice.current.name.replacingOccurrences(of: " ", with: "-").lowercased())"
    }
}
