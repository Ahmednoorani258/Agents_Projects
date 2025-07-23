"use client";
import { useState } from "react";

export default function ChatUI() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // const send = async () => {
  //   if (!input.trim()) return;

  //   const userMsg = { role: "user", text: input };
  //   setMessages((m) => [...m, userMsg]);
  //   setInput("");
  //   setLoading(true);

  //   try {
  //     const res = await fetch("/api/weather", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ message: input }),
  //     });

  //     const { response } = await res.json();
  //     setMessages((m) => [...m, { role: "assistant", text: response }]);
  //   } catch (error) {
  //     setMessages((m) => [
  //       ...m,
  //       { role: "assistant", text: "❌ Error fetching response." },
  //     ]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const send = async () => {
    if (!input.trim()) return;
  
    const userMsg = { role: "user", text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
  
    const assistantMsg = { role: "assistant", text: "🤖: " };
    setMessages((prev) => [...prev, assistantMsg]);
  
    try {
      const response = await fetch("/api/stream-weather", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
  
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
  
      let fullMessage = "🤖: ";
  
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
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <div className="h-[400px] overflow-y-auto border rounded-lg p-4 bg-white shadow">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`mb-2 p-3 rounded-lg w-fit max-w-[80%] ${
              m.role === "user"
                ? "ml-auto bg-blue-100 text-right"
                : "mr-auto bg-gray-100"
            }`}
          >
            {m.text}
          </div>
        ))}
        {loading && (
          <div className="mr-auto bg-gray-100 text-gray-500 text-sm rounded-lg p-2 animate-pulse w-fit max-w-[80%]">
            Thinking...
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-2 border rounded-md shadow focus:outline-none focus:ring focus:border-blue-400"
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
