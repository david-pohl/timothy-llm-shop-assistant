"use client";
import React, { useState, useEffect, useRef } from "react";

const ChatPage = () => {
    useEffect(() => {
        document.title = "Assistant Timothy";
      }, []);

    const [messages, setMessages] = useState([
        { is_ext_llm: false, sender: "Timothy", text: "Hello, my name is Timothy. I am here to assist you in navigating our clothing retail. Ask me anything." },
    ]);
    const [isCheckedExtLLM, setIsCheckedExtLLM] = useState(false);

    const newMessage = (is_ext_llm, sender, text) => {
        setMessages((prev) => [...prev, { is_ext_llm: is_ext_llm, sender: sender, text: text }]);
    }

    const endOfMessagesRef = useRef(null);
    useEffect(() => {
        if (endOfMessagesRef.current) {
            endOfMessagesRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    const [dataVersion, setDataVersion] = useState(null);
    const [input, setInput] = useState("");
    const [isWaiting, setIsWaiting] = useState(false);
    const [isDataUpdating, setIsDataUpdating] = useState(false);

    const getBackendStatus = async () => {
        const maxRequests = 10;
        const delayNext = 1000;

        for (let i = 0; i < maxRequests; i++) {
            console.log(i);
            try {
                const response = await fetch("http://127.0.0.1:8000/is-ready");
                if (!response.ok) {
                    throw new Error();
                }
                const data = await response.json();
                return data;
            } catch (error) {
                console.error("Backend Not Ready - Retrying in " + delayNext.toString());
                await new Promise(resolve => setTimeout(resolve, delayNext));
                console.error("Retrying");
                continue;
            }
        }
        throw new Error();
    };

    useEffect(() => {
        getBackendStatus()
            .then(data => {
                console.log("Backend Ready");
                setDataVersion(data.version);
            })
            .catch(error => {
                console.error("Backend Unavailable");
            });
    }, []);

    const updateData = async () => {
        try {
            setIsDataUpdating(true);
            const response = await fetch("http://127.0.0.1:8000/update-data");
            if (response.ok) {
                const data = await response.json();
                setDataVersion(data.version);
                setIsDataUpdating(false);
            }
        }
        catch (error) {
            console.error(error);
            setIsDataUpdating(false);
        }
    };

    const sendMessage = async () => {
        let text = input.trim()
        if (text === "") { return; }
        let message = {
            sender: "You",
            text: text
        }

        let context = messages.slice(-2).map((message, index) => ({
            sender: message.sender,
            text: message.text
        }));

        let chatMessages = context.concat(message)

        newMessage(false, "You", text);
        setInput("");
        setIsWaiting(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/send/message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ messages: chatMessages, use_external_llm: isCheckedExtLLM }),
            });

            if (!res.ok) {
                throw new Error("Failed to send message");
            }

            const data = await res.json();
            newMessage(isCheckedExtLLM, "Timothy", data.response)
            setIsWaiting(false);
        } catch (error) {
            console.error("Error:", error);
        }
    };

    return (
        <div className="w-screen bg-chatBg">
            <div className="max-w-screen-2xl h-screen py-4 mx-auto flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between mx-32 mt-4">
                    <h1 className="text-2xl font-bold text-msgText">Timothy</h1>
                    <div className="flex flex-row space-x-2">
                        <span onClick={() => setIsCheckedExtLLM(false)} className={'flex cursor-pointer items-center text-sm text-right font-medium transition-all ' + (isCheckedExtLLM ? "text-grayText" : "text-msgText")}>
                            Internal LLM
                        </span>
                        <label className='relative inline-flex cursor-pointer select-none items-center opacity-75 hover:opacity-100 transition-all'>
                            <input
                                type='checkbox'
                                checked={isCheckedExtLLM}
                                onChange={() => setIsCheckedExtLLM(!isCheckedExtLLM)}
                                className='sr-only'
                            />

                            <span
                                className={`mx-2 flex h-6 w-10 items-center rounded-full p-1 transition-all ${isCheckedExtLLM ? 'bg-white' : 'bg-buttonBg'
                                    }`}
                            >
                                <span
                                    className={`dot h-4 w-4 rounded-full transition-all ${isCheckedExtLLM ? 'translate-x-4 bg-buttonBg' : 'bg-white'
                                        }`}
                                ></span>
                            </span>

                        </label>
                        <span onClick={() => setIsCheckedExtLLM(true)} className={'flex cursor-pointer items-center text-sm font-medium transition-all ' + (isCheckedExtLLM ? "text-msgText" : "text-grayText")}>
                            External LLM
                        </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                        <button onClick={updateData} disabled={isDataUpdating} className="px-4 py-1 h-10 w-24 flex-row justify-center rounded-md bg-buttonBg text-buttonText bg-opacity-85 focus:bg-opacity-100 hover:bg-opacity-100 transition-all disabled:hover:bg-opacity-75">{(isDataUpdating ? (
                            <svg class="animate-spin mx-auto h-5 w-5 text-buttonText" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>) : (<span>Update</span>))}</button>
                        <div className="flex flex-col space-between">
                            <span className="text-msgText">Updating May Take A While</span>
                            <span className="text-sm text-grayText">Data Version: {dataVersion != null ? dataVersion.join("/") : ""}</span>
                        </div>
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
                                    className={`max-w-xl flex-1 px-3 py-2 space-y-1 rounded-md shadow-md ${msg.sender === "You"
                                        ? "bg-userBg text-msgText"
                                        : "bg-timoBg text-msgText"
                                        }`}
                                >
                                    <div className="flex flex-row space-x-2 items-center">
                                        <div className="font-bold">{msg.sender}</div>
                                        {msg.is_ext_llm ? (<div className="font-normal text-sm text-buttonText">ext</div>) : (<></>)}
                                    </div>
                                    <p className="whitespace-pre-line">{msg.text}</p>
                                </div>
                            </div>
                        ))}
                        {isWaiting && (
                            <div className="max-w-xl flex-1 flex justify-start">
                                <div className="flex-1 flex space-x-4 h-32 items-center justify-center">
                                    <span className="w-3 h-3 bg-timoBg rounded-sm animate-staggeredPulseA"></span>
                                    <span className="w-3 h-3 bg-timoBg rounded-sm animate-staggeredPulseB"></span>
                                    <span className="w-3 h-3 bg-timoBg rounded-sm animate-staggeredPulseC"></span>
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
                        className="flex-1 px-4 py-2 bg-buttonBg text-buttonText bg-opacity-85 focus:bg-opacity-100 hover:bg-opacity-100 rounded-md placeholder-buttonPlaceholder outline-none focus:ring-0 transition-all resize-none"
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
                        className="ml-4 w-24 h-10 bg-buttonBg text-buttonText bg-opacity-85 focus:bg-opacity-100 hover:bg-opacity-100 transition-all rounded-md flex items-center justify-center"
                        onClick={sendMessage}
                    >
                        →
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatPage;