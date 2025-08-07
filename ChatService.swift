//
//  ChatService.swift
//  GlowGirl
//
//  Created by Archita Nemalikanti on 8/3/25.
//

import Foundation

class ChatService: ObservableObject {
    // CHANGE THIS URL TO YOUR SERVER'S ADDRESS
    private let baseURL = "http://192.168.1.123:5000"  // Use YOUR actual IP
    
    struct ChatRequest: Codable {
        let message: String
    }
    
    struct ChatResponse: Codable {
        let response: String
        let action: String? // Optional - only present when signup is complete
    }
    
    func sendMessage(_ message: String) async throws -> ChatResponse {
        guard let url = URL(string: "\(baseURL)/chat") else {
            throw ChatError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let chatRequest = ChatRequest(message: message)
        request.httpBody = try JSONEncoder().encode(chatRequest)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw ChatError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw ChatError.serverError(httpResponse.statusCode)
        }
        
        let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
        return chatResponse
    }
}

enum ChatError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError:
            return "Network connection error"
        }
    }
} 