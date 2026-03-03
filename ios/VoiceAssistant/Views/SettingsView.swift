// SettingsView.swift
// Lets the user configure the token server URL at runtime.
//
// Why runtime settings?
//   When switching between LAN (192.168.x.x) and Tailscale (100.x.x.x),
//   the user needs to change the server address without recompiling.
//   UserDefaults persists the value across app launches.

import SwiftUI

struct SettingsView: View {
    @Environment(RoomManager.self) private var roomManager
    @Environment(ChatViewModel.self) private var chatViewModel
    @State private var tokenURL: String = AppConfig.tokenServerURL
    @State private var showSaved: Bool = false

    var body: some View {
        NavigationStack {
            Form {
                // ── Server Configuration ────────────────────────
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Token Server URL")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        TextField("http://192.168.1.100:8081", text: $tokenURL)
                            .font(.system(.body, design: .monospaced))
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)
                    }
                } header: {
                    Text("Server")
                } footer: {
                    Text("The HTTP address of your token server running in Docker. "
                         + "Use your PC's local IP for Wi-Fi, or Tailscale IP for remote access.")
                }

                // ── Save Button ─────────────────────────────────
                Section {
                    Button {
                        AppConfig.tokenServerURL = tokenURL
                        showSaved = true
                        // Auto-hide the confirmation after 2 seconds
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            showSaved = false
                        }
                    } label: {
                        HStack {
                            Text("Save")
                            Spacer()
                            if showSaved {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                }

                // ── Connection Info ─────────────────────────────
                Section {
                    LabeledContent("Connection", value: roomManager.connectionState.displayText)
                    LabeledContent("Agent", value: roomManager.agentConnected ? "Connected" : "Not connected")
                    LabeledContent("Room", value: AppConfig.defaultRoomName)
                    LabeledContent("Identity", value: AppConfig.participantIdentity)
                } header: {
                    Text("Status")
                }

                // ── Disconnect ──────────────────────────────────
                if roomManager.connectionState.isConnected {
                    Section {
                        Button(role: .destructive) {
                            Task { await roomManager.disconnect() }
                        } label: {
                            Label("Disconnect", systemImage: "phone.down")
                        }
                    }
                }

                // ── About ───────────────────────────────────────
                Section {
                    LabeledContent("App", value: "Voice Assistant")
                    LabeledContent("Architecture", value: "LiveKit + Ollama + Whisper + Kokoro")
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
        }
    }
}
