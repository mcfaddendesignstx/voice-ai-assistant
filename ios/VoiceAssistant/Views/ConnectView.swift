// ConnectView.swift
// Shown when the app is not connected to a LiveKit room.
// Displays a big "Connect" button and the server URL for verification.
//
// Why a dedicated connect screen?
//   The user needs to confirm the server URL is correct before connecting.
//   This also shows any connection errors clearly.

import SwiftUI

struct ConnectView: View {
    @Environment(RoomManager.self) private var roomManager

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                Spacer()

                // App icon / branding area
                VStack(spacing: 12) {
                    Image(systemName: "waveform.circle.fill")
                        .font(.system(size: 80))
                        .foregroundStyle(.blue)

                    Text("Voice Assistant")
                        .font(.largeTitle.bold())

                    Text("Self-hosted AI voice chat")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                // Server info + current selections
                VStack(spacing: 12) {
                    Label("Token Server", systemImage: "server.rack")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text(AppConfig.tokenServerURL)
                        .font(.system(.callout, design: .monospaced))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)

                    Divider()

                    HStack(spacing: 24) {
                        VStack(spacing: 4) {
                            Text("LLM")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Text(AppConfig.selectedModel)
                                .font(.caption.bold())
                        }
                        VStack(spacing: 4) {
                            Text("Voice")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Text(AppConfig.selectedTTS)
                                .font(.caption.bold())
                        }
                    }
                }
                .padding()
                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))

                Spacer()

                // Error display
                if let error = roomManager.errorMessage {
                    Text(error)
                        .font(.callout)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                // Connect button
                Button {
                    Task {
                        await roomManager.connect()
                    }
                } label: {
                    Group {
                        if roomManager.connectionState == .connecting {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Label("Connect", systemImage: "phone.fill")
                        }
                    }
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .frame(height: 54)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(roomManager.connectionState == .connecting)
                .padding(.horizontal, 32)

                // Link to settings
                NavigationLink {
                    SettingsView()
                } label: {
                    Text("Settings")
                        .font(.callout)
                        .foregroundStyle(.blue)
                }
                .padding(.bottom, 32)
            }
            .padding()
        }
    }
}
