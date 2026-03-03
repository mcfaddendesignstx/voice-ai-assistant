// ChatMessage.swift
// Data model for messages displayed in the chat UI.
//
// Why a dedicated model?
//   Keeps view code clean. Both voice transcriptions and typed messages
//   flow through the same model, making the chat view simple.

import Foundation

struct ChatMessage: Identifiable, Equatable {
    let id: String
    let timestamp: Date
    let content: String
    let role: Role
    var isFinal: Bool

    enum Role: Equatable {
        case user       // What the user said (STT transcript) or typed
        case assistant  // What the agent said (TTS transcript)
        case system     // Status messages ("Connected", "Agent joined", etc.)
    }

    // Convenience initializer for quick message creation
    init(
        id: String = UUID().uuidString,
        timestamp: Date = Date(),
        content: String,
        role: Role,
        isFinal: Bool = true
    ) {
        self.id = id
        self.timestamp = timestamp
        self.content = content
        self.role = role
        self.isFinal = isFinal
    }
}
