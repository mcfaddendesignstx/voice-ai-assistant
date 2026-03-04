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
    @State private var selectedModel: String = AppConfig.selectedModel
    @State private var selectedTTS: String = AppConfig.selectedTTS
    @State private var showSaved: Bool = false

    private let llmOptions = [
        ("gemini-flash", "Gemini Flash", "Google — fastest"),
        ("claude-haiku", "Claude Haiku", "Anthropic via OpenRouter"),
        ("gpt-4o-mini", "GPT-4.1 Mini", "OpenAI via OpenRouter"),
    ]

    private let ttsOptions = [
        ("kokoro", "Kokoro", "Local — fast, lightweight"),
        ("qwen3-tts", "Qwen3-TTS", "Local — expressive, GPU"),
        ("elevenlabs", "ElevenLabs", "Cloud — premium quality"),
    ]

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

                // ── LLM Model Picker ────────────────────────────
                Section {
                    ForEach(llmOptions, id: \.0) { option in
                        Button {
                            selectedModel = option.0
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(option.1)
                                        .foregroundStyle(.primary)
                                    Text(option.2)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if selectedModel == option.0 {
                                    Image(systemName: "checkmark")
                                        .foregroundStyle(.blue)
                                        .fontWeight(.semibold)
                                }
                            }
                        }
                    }
                } header: {
                    Text("LLM Model")
                } footer: {
                    Text("Choose the AI model for conversation. Takes effect on next connection.")
                }

                // ── TTS Engine Picker ───────────────────────────
                Section {
                    ForEach(ttsOptions, id: \.0) { option in
                        Button {
                            selectedTTS = option.0
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(option.1)
                                        .foregroundStyle(.primary)
                                    Text(option.2)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if selectedTTS == option.0 {
                                    Image(systemName: "checkmark")
                                        .foregroundStyle(.blue)
                                        .fontWeight(.semibold)
                                }
                            }
                        }
                    }
                } header: {
                    Text("Voice Engine")
                } footer: {
                    Text("Choose the text-to-speech engine. Kokoro is fast, Qwen3-TTS is more expressive, ElevenLabs is cloud-based premium.")
                }

                // ── Save Button ─────────────────────────────────
                Section {
                    Button {
                        AppConfig.tokenServerURL = tokenURL
                        AppConfig.selectedModel = selectedModel
                        AppConfig.selectedTTS = selectedTTS
                        showSaved = true
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
                    LabeledContent("Architecture", value: "LiveKit + Gemini/Claude/GPT + Whisper + Kokoro/Qwen3/ElevenLabs")
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
        }
    }
}
