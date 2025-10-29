//
//  ContentView.swift
//  TickerEr
//
//  Created by Keshav Vyas on 9/17/25.
//

import SwiftUI


struct ContentView: View {
    @State private var textInput: String = ""
    @State private var showAlert: Bool = false
    @State private var urlInput: String = ""
    @State private var responseData: String = ""
    @State private var isLoading: Bool = false
    @State private var showResponseAlert: Bool = false
    
    var body: some View {
        //Image("test");
        VStack(spacing: 20) {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, Ticket Users!")
            
            TextField("Enter your text here", text: $textInput)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding(.horizontal)
            
            Button("Show Alert") {
                showAlert = true
            }
            .buttonStyle(.borderedProminent)
            
            TextField("Enter URL here", text: $urlInput)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .padding(.horizontal)
            
            Button("Make GET Request") {
                makeGetRequest()
            }
            .buttonStyle(.bordered)
            .disabled(isLoading || urlInput.isEmpty)
            
            if isLoading {
                ProgressView("Loading...")
            }
        }
        .padding()
        .alert("Your Input", isPresented: $showAlert) {
            Button("OK") { }
        } message: {
            Text(textInput.isEmpty ? "No text entered" : textInput)
        }
        .alert("API Response", isPresented: $showResponseAlert) {
            Button("OK") { }
        } message: {
            Text(responseData)
        }
    }
    
    private func makeGetRequest() {
        guard let url = URL(string: urlInput) else {
            responseData = "Invalid URL format"
            showResponseAlert = true
            return
        }
        
        isLoading = true
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                isLoading = false
                
                if let error = error {
                    responseData = "Error: \(error.localizedDescription)"
                } else if let data = data {
                    if let responseString = String(data: data, encoding: .utf8) {
                        responseData = "Response: \(responseString)"
                    } else {
                        responseData = "Response: Unable to decode data as text"
                    }
                } else {
                    responseData = "No data received"
                }
                
                showResponseAlert = true
            }
        }.resume()
    }
}

#Preview {
    ContentView()
}
