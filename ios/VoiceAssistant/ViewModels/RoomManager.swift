// RoomManager.swift
// Owns the LiveKit Room connection and bridges events to SwiftUI.
//
// Why @Observable instead of ObservableObject?
//   @Observable (iOS 17+) is Apple's newer, cleaner observation system.
//   No need for @Published — any property mutation automatically triggers
//   SwiftUI view updates. Simpler code, fewer bugs.
//
// Why RoomDelegate?
//   LiveKit's Swift SDK uses the delegate pattern to notify us of events
//   like participants joining, audio tracks being published, and
//   transcription segments arriving from the agent.

import Foundation
import LiveKit
import Combine

@Observable
final class RoomManager: NSObject, RoomDelegate {

    // ── Public state (drives SwiftUI views) ─────────────────────
    var connectionState: ConnectionState = .disconnected
    var isMuted: Bool = false
    var agentConnected: Bool = false
    var agentAudioLevel: Float = 0.0
    var userAudioLevel: Float = 0.0
    var errorMessage: String?

    // ── Private ─────────────────────────────────────────────────
    let room: Room
    private let tokenService = TokenService()
    private var chatViewModel: ChatViewModel?

    // ── Init ────────────────────────────────────────────────────
    override init() {
        self.room = Room()
        super.init()
        room.add(delegate: self)
    }

    // Inject the chat view model so we can push messages to it
    func setChatViewModel(_ vm: ChatViewModel) {
        self.chatViewModel = vm
    }

    // ── Connect ─────────────────────────────────────────────────
    /// Fetches a token from the token server, then connects to LiveKit.
    func connect() async {
        do {
            errorMessage = nil
            connectionState = .connecting

            // 1. Get JWT from token server
            let details = try await tokenService.fetchConnectionDetails()

            // 2. Connect to LiveKit (this establishes WebRTC)
            try await room.connect(
                url: details.serverURL,
                token: details.token
            )

            // 3. Enable microphone — triggers iOS permission prompt on first use
            try await room.localParticipant.setMicrophone(enabled: true)

            connectionState = .connected
            chatViewModel?.addSystemMessage("Connected to room")

        } catch {
            connectionState = .disconnected
            errorMessage = error.localizedDescription
            chatViewModel?.addSystemMessage("Connection failed: \(error.localizedDescription)")
        }
    }

    // ── Disconnect ──────────────────────────────────────────────
    func disconnect() async {
        await room.disconnect()
        connectionState = .disconnected
        agentConnected = false
        isMuted = false
        chatViewModel?.addSystemMessage("Disconnected")
    }

    // ── Mute / Unmute ───────────────────────────────────────────
    func toggleMute() async {
        isMuted.toggle()
        do {
            try await room.localParticipant.setMicrophone(enabled: !isMuted)
        } catch {
            errorMessage = "Failed to toggle microphone: \(error.localizedDescription)"
            isMuted.toggle() // revert
        }
    }

    // ── Send text message to agent ──────────────────────────────
    /// Sends a text message via LiveKit data channel.
    /// The agent receives this as a chat message alongside voice.
    func sendTextMessage(_ text: String) async {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        do {
            // LiveKit's data channel topic for chat messages
            let data = text.data(using: .utf8)!
            try await room.localParticipant.publish(
                data: data,
                options: DataPublishOptions(
                    topic: "lk.chat",
                    reliable: true
                )
            )
            // Add to local chat immediately (local echo)
            chatViewModel?.upsertMessage(
                ChatMessage(content: text, role: .user)
            )
        } catch {
            errorMessage = "Failed to send message: \(error.localizedDescription)"
        }
    }

    // ── RoomDelegate: Connection state ──────────────────────────
    func room(_ room: Room, didUpdateConnectionState connectionState: ConnectionState, from oldValue: ConnectionState) {
        Task { @MainActor in
            self.connectionState = connectionState
        }
    }

    // ── RoomDelegate: Participant connected ─────────────────────
    func room(_ room: Room, participantDidConnect participant: RemoteParticipant) {
        // The agent is the only remote participant in our setup
        Task { @MainActor in
            self.agentConnected = true
            self.chatViewModel?.addSystemMessage("Agent joined the room")
        }
    }

    func room(_ room: Room, participantDidDisconnect participant: RemoteParticipant) {
        Task { @MainActor in
            self.agentConnected = false
            self.chatViewModel?.addSystemMessage("Agent left the room")
        }
    }

    // ── RoomDelegate: Transcription segments ────────────────────
    // LiveKit agents send transcription events for both user speech
    // (what the STT heard) and agent speech (what the TTS is saying).
    func room(
        _ room: Room,
        participant: Participant?,
        didReceiveTranscriptionSegments segments: [TranscriptionSegment],
        publication: TrackPublication?
    ) {
        Task { @MainActor in
            for segment in segments {
                let isAgent = participant is RemoteParticipant
                let role: ChatMessage.Role = isAgent ? .assistant : .user

                chatViewModel?.upsertMessage(
                    ChatMessage(
                        id: segment.id,
                        content: segment.text,
                        role: role,
                        isFinal: segment.isFinal
                    )
                )
            }
        }
    }

    // ── RoomDelegate: Audio level updates ───────────────────────
    func room(_ room: Room, participant: Participant, didUpdateSpeakingStatus isSpeaking: Bool) {
        Task { @MainActor in
            if participant is RemoteParticipant {
                self.agentAudioLevel = isSpeaking ? 1.0 : 0.0
            } else {
                self.userAudioLevel = isSpeaking ? 1.0 : 0.0
            }
        }
    }

    // ── RoomDelegate: Data received ─────────────────────────────
    func room(_ room: Room, participant: RemoteParticipant?, didReceiveData data: Data, forTopic topic: String) {
        // Handle chat messages from the agent
        guard topic == "lk.chat", let text = String(data: data, encoding: .utf8) else { return }
        Task { @MainActor in
            chatViewModel?.upsertMessage(
                ChatMessage(content: text, role: .assistant)
            )
        }
    }
}

// ── ConnectionState extension for display ───────────────────────
extension ConnectionState {
    var displayText: String {
        switch self {
        case .disconnected: return "Disconnected"
        case .connecting: return "Connecting..."
        case .reconnecting: return "Reconnecting..."
        case .connected: return "Connected"
        @unknown default: return "Unknown"
        }
    }

    var isConnected: Bool {
        self == .connected
    }
}
