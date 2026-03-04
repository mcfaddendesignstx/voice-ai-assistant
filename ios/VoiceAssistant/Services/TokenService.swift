// TokenService.swift
// Fetches a LiveKit JWT from the token server.
//
// Why a separate service?
//   The LiveKit API secret must NEVER be on the device. Instead, the iOS app
//   asks our token server (running in Docker) to mint a short-lived JWT.
//   The app then uses that JWT to connect directly to LiveKit via WebRTC.

import Foundation

struct ConnectionDetails {
    let serverURL: String   // LiveKit WebSocket URL (ws://...)
    let token: String       // JWT the app passes to room.connect()
}

enum TokenServiceError: LocalizedError {
    case invalidURL
    case serverError(String)
    case decodingError

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid token server URL. Check Settings."
        case .serverError(let msg):
            return "Token server error: \(msg)"
        case .decodingError:
            return "Could not decode token server response."
        }
    }
}

struct TokenService {
    /// Calls GET /token?room=<room>&identity=<identity> on the token server.
    /// Returns the LiveKit URL and JWT needed to connect.
    func fetchConnectionDetails(
        room: String = AppConfig.defaultRoomName,
        identity: String = AppConfig.participantIdentity
    ) async throws -> ConnectionDetails {
        // Build the URL with query parameters
        guard var components = URLComponents(string: AppConfig.tokenServerURL + "/token") else {
            throw TokenServiceError.invalidURL
        }
        components.queryItems = [
            URLQueryItem(name: "room", value: room),
            URLQueryItem(name: "identity", value: identity),
            URLQueryItem(name: "model", value: AppConfig.selectedModel),
            URLQueryItem(name: "tts", value: AppConfig.selectedTTS),
        ]
        guard let url = components.url else {
            throw TokenServiceError.invalidURL
        }

        // Make the HTTP request
        let (data, response) = try await URLSession.shared.data(from: url)

        // Check HTTP status
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode != 200 {
            let body = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw TokenServiceError.serverError(body)
        }

        // Parse JSON: { "token": "...", "url": "ws://..." }
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let token = json["token"] as? String,
              let serverURL = json["url"] as? String
        else {
            throw TokenServiceError.decodingError
        }

        return ConnectionDetails(serverURL: serverURL, token: token)
    }
}
