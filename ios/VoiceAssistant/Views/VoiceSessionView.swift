// VoiceSessionView.swift
// The main voice interaction screen — shows audio visualization,
// agent status, and mute/disconnect controls.
//
// Why a dedicated voice view?
//   Voice and text are separate interaction modes. The voice view focuses
//   on audio levels, agent speaking state, and minimal controls so the
//   user can glance at it during a conversation.

import SwiftUI

struct VoiceSessionView: View {
    @Environment(RoomManager.self) private var roomManager

    var body: some View {
        VStack(spacing: 0) {
            // ── Status bar ──────────────────────────────────────
            HStack {
                Circle()
                    .fill(roomManager.agentConnected ? .green : .orange)
                    .frame(width: 8, height: 8)

                Text(roomManager.agentConnected ? "Agent connected" : "Waiting for agent...")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Spacer()

                Text(roomManager.isMuted ? "Muted" : "Listening")
                    .font(.subheadline)
                    .foregroundStyle(roomManager.isMuted ? .red : .green)
            }
            .padding(.horizontal)
            .padding(.top, 8)

            Spacer()

            // ── Audio visualization ─────────────────────────────
            VStack(spacing: 24) {
                // Agent speaking indicator — pulsing ring
                ZStack {
                    // Outer pulse (visible when agent is speaking)
                    Circle()
                        .stroke(Color.blue.opacity(0.3), lineWidth: 3)
                        .frame(width: 180, height: 180)
                        .scaleEffect(roomManager.agentAudioLevel > 0 ? 1.15 : 1.0)
                        .opacity(roomManager.agentAudioLevel > 0 ? 0.8 : 0.0)
                        .animation(
                            .easeInOut(duration: 0.6).repeatForever(autoreverses: true),
                            value: roomManager.agentAudioLevel
                        )

                    // Middle ring
                    Circle()
                        .stroke(Color.blue.opacity(0.5), lineWidth: 4)
                        .frame(width: 150, height: 150)
                        .scaleEffect(roomManager.agentAudioLevel > 0 ? 1.08 : 1.0)
                        .animation(.easeInOut(duration: 0.4), value: roomManager.agentAudioLevel)

                    // Center circle
                    Circle()
                        .fill(
                            roomManager.agentAudioLevel > 0
                                ? Color.blue
                                : Color.blue.opacity(0.2)
                        )
                        .frame(width: 120, height: 120)
                        .animation(.easeInOut(duration: 0.2), value: roomManager.agentAudioLevel)

                    // Icon in center
                    Image(systemName: roomManager.agentAudioLevel > 0
                          ? "waveform"
                          : "waveform.badge.minus")
                        .font(.system(size: 36))
                        .foregroundStyle(.white)
                }

                Text(roomManager.agentAudioLevel > 0 ? "Agent is speaking..." : "Agent is listening")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            // ── User speaking indicator ─────────────────────────
            if !roomManager.isMuted {
                HStack(spacing: 4) {
                    ForEach(0..<5, id: \.self) { i in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(Color.green)
                            .frame(width: 4, height: roomManager.userAudioLevel > 0
                                   ? CGFloat.random(in: 8...28)
                                   : 8)
                            .animation(
                                .easeInOut(duration: 0.15)
                                    .repeatForever(autoreverses: true)
                                    .delay(Double(i) * 0.05),
                                value: roomManager.userAudioLevel
                            )
                    }
                }
                .frame(height: 32)
                .padding(.bottom, 8)
            }

            // ── Controls ────────────────────────────────────────
            HStack(spacing: 40) {
                // Mute button
                Button {
                    Task { await roomManager.toggleMute() }
                } label: {
                    VStack(spacing: 6) {
                        Image(systemName: roomManager.isMuted
                              ? "mic.slash.fill"
                              : "mic.fill")
                            .font(.title2)
                            .frame(width: 60, height: 60)
                            .background(
                                roomManager.isMuted
                                    ? Color.red.opacity(0.2)
                                    : Color.green.opacity(0.2),
                                in: Circle()
                            )

                        Text(roomManager.isMuted ? "Unmute" : "Mute")
                            .font(.caption)
                    }
                }
                .tint(roomManager.isMuted ? .red : .green)

                // Disconnect button
                Button {
                    Task { await roomManager.disconnect() }
                } label: {
                    VStack(spacing: 6) {
                        Image(systemName: "phone.down.fill")
                            .font(.title2)
                            .frame(width: 60, height: 60)
                            .background(Color.red.opacity(0.2), in: Circle())

                        Text("End")
                            .font(.caption)
                    }
                }
                .tint(.red)
            }
            .padding(.bottom, 24)
        }
    }
}
