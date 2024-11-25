"use client";
import React, { useState, useEffect, useRef } from "react";

const ChatPage = () => {
    const [messages, setMessages] = useState([
        { sender: "Timothy", text: "Hello! My name is Timothy. I'm here to assist you in your online clothing shopping. Ask me anything." },
    ]);

    const newMessage = (sender, text) => {
        setMessages((prev) => [...prev, { sender: sender, text: text }]);
    }

    const endOfMessagesRef = useRef(null);
    useEffect(() => {
        if (endOfMessagesRef.current) {
            endOfMessagesRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    const [input, setInput] = useState("");
    const [isWaiting, setIsWaiting] = useState(false)

    const sendMessage = async () => {
        let text = input.trim()
        if (text === "") { return; }
        let message = {
            sender: "You",
            text: text
        }

        let context = messages.slice(-4).map((message, index) => ({
            sender: message.sender,
            text: message.text
        }));

        newMessage("You", text);
        setInput("");
        setIsWaiting(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/send/message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(context.concat(message)), // Send the message as JSON
            });

            if (!res.ok) {
                throw new Error("Failed to send message");
            }

            const data = await res.json(); // Parse the JSON response
            newMessage("Timothy", data.message)
            setIsWaiting(false);
        } catch (error) {
            console.error("Error:", error);
        }
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
                            className={`flex ${msg.sender === "You" ? "justify-end" : "justify-start"
                                }`}
                        >
                            <div
                                className={`max-w-xl flex-1 px-4 py-3 space-y-1 rounded-md shadow-md ${msg.sender === "You"
                                    ? "bg-slate-600 text-slate-200"
                                    : "bg-slate-700 text-slate-300"
                                    }`}
                            >
                                <p className="font-bold">{msg.sender}</p>
                                <p className="whitespace-pre-line">{msg.text}</p>
                            </div>
                        </div>
                    ))}
                    {isWaiting && (
                        <div className="max-w-xl flex-1 flex justify-start mt-6">
                            <div className="flex-1 flex space-x-2 h-32 items-center justify-center">
                                <span className="w-3 h-3 bg-slate-600 rounded-md animate-pulse"></span>
                                <span className="w-3 h-3 bg-slate-600 rounded-md animate-pulse delay-100"></span>
                                <span className="w-3 h-3 bg-slate-600 rounded-md animate-pulse delay-200"></span>
                            </div>
                        </div>
                    )}
                    <div ref={endOfMessagesRef} />
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
                            e.preventDefault();
                            sendMessage();
                        }
                    }}
                    rows={Math.min(8, input.split("\n").length || 1)}
                    disabled={isWaiting}
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