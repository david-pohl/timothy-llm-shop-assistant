"use client";
import React, { useState } from "react";

const ChatPage = () => {
    const [messages, setMessages] = useState([
      { sender: "Timothy", text: "Hi, my name is Timothy. I'm your personal assistant for shopping clothes. Ask me anything." },
      { sender: "You", text: "I'm interested in purchasing a Juno Jacket. What sizes are available?" },
      { sender: "Timothy", text: "Let me check that for you." },
    ]);
  
    const [input, setInput] = useState("");
  
    const sendMessage = () => {
      if (input.trim() === "") return;
      setMessages((prev) => [...prev, { sender: "You", text: input }]);
      setInput("");
    };
  
    return (
      <div className="flex flex-col h-screen w-screen bg-stone-900 text-white">
        {/* Header */}
        <div className="flex items-center justify-between mx-32 mt-4">
          <h1 className="text-2xl font-bold text-slate-300">Timothy</h1>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex flex-col space-between">
                <span className="text-gray-200">Updating May Take a While</span>
                <span className="text-gray-400">Last: 2024/11/23 12:23 PM</span>
            </div>
            <button className="px-4 py-1 h-10 rounded-md bg-slate-600 text-slate-200 hover:bg-slate-500 transition-colors">Update</button>
          </div>
        </div>
  
        {/* Chat Messages */}
        <div className="flex flex-1 mx-32 mt-8 space-x-4 overflow-y-auto">  
          {/* Message Section */}
          <div className="flex flex-col flex-1 space-y-6">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.sender === "You" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-md px-4 py-3 rounded-md shadow-md ${
                    msg.sender === "You"
                      ? "bg-slate-600 text-slate-200"
                      : "bg-slate-700 text-slate-300"
                  }`}
                >
                  <p className="font-bold">{msg.sender}</p>
                  <p>{msg.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
  
        {/* Input Section */}
        <div className="flex items-end mx-32 my-4">
            <textarea
                placeholder="Follow up on previous answers or ask a new question."
                className="flex-1 px-4 py-2 bg-slate-600 text-slate-200 hover:bg-slate-700 rounded-md placeholder-slate-400 outline-none focus:ring-0 focus:bg-slate-700 transition-all resize-none"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault(); // Prevent new lines when pressing Enter
                        sendMessage();
                    }
                }}
                rows={Math.min(8, input.split("\n").length || 1)}
            />
          <button
            className="ml-4 w-24 h-10 bg-slate-600 text-slate-200 hover:bg-slate-500 transition-colors rounded-md flex items-center justify-center"
            onClick={sendMessage}
          >
            →
          </button>
        </div>
      </div>
    );
  };
  
export default ChatPage;