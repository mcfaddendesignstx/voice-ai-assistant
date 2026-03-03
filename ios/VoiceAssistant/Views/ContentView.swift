// ContentView.swift
// Root view — shows ConnectView when disconnected, SessionView when connected.
//
// Why this pattern?
//   A single "router" view that switches based on connection state keeps
//   navigation simple. No NavigationStack needed for this two-state app.

import SwiftUI

struct ContentView: View {
    @Environment(RoomManager.self) private var roomManager
    @Environment(ChatViewModel.self) private var chatViewModel

    var body: some View {
        Group {
            if roomManager.connectionState.isConnected {
                SessionView()
            } else {
                ConnectView()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: roomManager.connectionState.isConnected)
        .onAppear {
            // Wire up the chat view model to the room manager
            roomManager.setChatViewModel(chatViewModel)
        }
    }
}

// ── Session View: Voice + Chat in tabs ──────────────────────────
struct SessionView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            VoiceSessionView()
                .tabItem {
                    Label("Voice", systemImage: "waveform")
                }
                .tag(0)

            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "message")
                }
                .tag(1)

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(2)
        }
        .tint(.blue)
    }
}
