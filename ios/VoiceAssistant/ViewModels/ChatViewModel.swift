// ChatViewModel.swift
// Manages the list of chat messages displayed in ChatView.
//
// Why separate from RoomManager?
//   Single Responsibility — RoomManager handles the LiveKit connection,
//   ChatViewModel handles message storage and display logic.
//   RoomManager feeds messages into this view model.

import Foundation
import SwiftUI

@Observable
final class ChatViewModel {
    // Ordered list of all messages (user transcripts + agent transcripts + system)
    var messages: [ChatMessage] = []

    // Adds or updates a message. Transcription segments arrive incrementally:
    // the same segment ID gets updated until isFinal = true.
    func upsertMessage(_ message: ChatMessage) {
        if let index = messages.firstIndex(where: { $0.id == message.id }) {
            messages[index] = message
        } else {
            messages.append(message)
        }
    }

    // Convenience for adding a one-shot system message
    func addSystemMessage(_ text: String) {
        messages.append(ChatMessage(content: text, role: .system))
    }

    // Clear all messages (e.g., on disconnect)
    func clear() {
        messages.removeAll()
    }
}
