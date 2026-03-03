// ChatView.swift
// Text chat UI — shows transcriptions from voice + allows typed input.
//
// Why text alongside voice?
//   1. Users can read what the AI said (useful in noisy environments)
//   2. Users can type when they can't speak
//   3. Transcripts serve as a conversation log

import SwiftUI

struct ChatView: View {
    @Environment(RoomManager.self) private var roomManager
    @Environment(ChatViewModel.self) private var chatViewModel
    @State private var inputText: String = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // ── Message list ────────────────────────────────────
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(chatViewModel.messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: chatViewModel.messages.count) { _, _ in
                    // Auto-scroll to the latest message
                    if let lastMessage = chatViewModel.messages.last {
                        withAnimation(.easeOut(duration: 0.2)) {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            Divider()

            // ── Text input ──────────────────────────────────────
            HStack(spacing: 12) {
                TextField("Type a message...", text: $inputText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .lineLimit(1...4)
                    .focused($isInputFocused)
                    .onSubmit { sendMessage() }

                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .tint(.blue)
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
            .background(.ultraThinMaterial)
        }
        .navigationBarTitleDisplayMode(.inline)
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        Task {
            await roomManager.sendTextMessage(text)
        }
    }
}

// ── Message Bubble ──────────────────────────────────────────────
struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 60) }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                // Role label
                if message.role != .system {
                    Text(message.role == .user ? "You" : "Assistant")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                // Message content
                Text(message.content)
                    .font(message.role == .system ? .caption : .body)
                    .foregroundStyle(message.role == .system ? .secondary : .primary)
                    .opacity(message.isFinal ? 1.0 : 0.7)
                    .padding(.horizontal, message.role == .system ? 0 : 14)
                    .padding(.vertical, message.role == .system ? 4 : 10)
                    .background(backgroundColor, in: bubbleShape)
            }

            if message.role == .assistant || message.role == .system { Spacer(minLength: 60) }
        }
    }

    private var backgroundColor: Color {
        switch message.role {
        case .user:      return .blue
        case .assistant: return Color(.systemGray5)
        case .system:    return .clear
        }
    }

    private var bubbleShape: some Shape {
        RoundedRectangle(cornerRadius: 16)
    }
}
