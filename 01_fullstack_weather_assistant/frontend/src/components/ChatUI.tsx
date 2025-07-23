"use client";
import { useEffect, useRef, useState } from "react";
import { Loader2, Bot, User } from "lucide-react";

export default function ChatUI() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const send = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const assistantMsg = { role: "assistant", text: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const response = await fetch("/api/stream-weather", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullMessage = "";

      while (reader) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        fullMessage += chunk;

        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", text: fullMessage },
        ]);
      }
    } catch (error) {
      console.error("Streaming error:", error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", text: "❌ Error while streaming." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-800 text-white font-sans px-4 py-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-center text-blue-400">
          Weather Assistant 🌦️
        </h1>

        <div className="h-[450px] overflow-y-auto rounded-lg bg-gray-800 p-4 shadow-inner space-y-4 border border-gray-700">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex gap-3 items-start ${
                m.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {m.role === "assistant" && (
                <div className="text-blue-400">
                  <Bot size={20} />
                </div>
              )}
              <div
                className={`rounded-xl px-4 py-3 max-w-[75%] text-sm whitespace-pre-line shadow-md transition-all ${
                  m.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-gray-700 text-gray-100 rounded-bl-none"
                }`}
              >
                {m.text}
              </div>
              {m.role === "user" && (
                <div className="text-blue-300">
                  <User size={20} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Loader2 className="animate-spin" size={16} />
              <span>Assistant is typing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about weather, e.g. 'What's the weather in Tokyo?'"
            className="flex-1 px-4 py-3 rounded-full bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={send}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full disabled:opacity-50 transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
