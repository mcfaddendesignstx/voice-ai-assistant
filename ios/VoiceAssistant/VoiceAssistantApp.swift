// VoiceAssistantApp.swift
// Entry point for the iOS app.
//
// Why SwiftUI @main?
//   SwiftUI is Apple's modern declarative UI framework. The @main attribute
//   marks this struct as the app's launch point — no AppDelegate needed.

import SwiftUI

@main
struct VoiceAssistantApp: App {
    // @State creates app-wide state that persists for the app's lifetime.
    // RoomManager is our central object that owns the LiveKit connection.
    @State private var roomManager = RoomManager()
    @State private var chatViewModel = ChatViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                // .environment() injects these into ALL child views so they
                // can access them with @Environment without manual passing.
                .environment(roomManager)
                .environment(chatViewModel)
        }
    }
}
