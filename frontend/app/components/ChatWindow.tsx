"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { sendChatMessage, type ChatSource } from "../../lib/api";

type Message = {
  id: string;
  sender: "user" | "advisor";
  text: string;
  sources?: ChatSource[];
};

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "advisor",
      text: "Hello! I am your AI Scholarship Advisor. Ask me anything about eligibility criteria, funding benefits, application processes, or deadlines for our catalog of scholarships.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [messages, loading]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    const userMessageId = `user-${Date.now()}`;
    const userMsg: Message = { id: userMessageId, sender: "user", text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(query);
      const advisorMsg: Message = {
        id: `advisor-${Date.now()}`,
        sender: "advisor",
        text: response.answer,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, advisorMsg]);
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setLoading(false);
    }
  }

  function parseMarkdownLinks(text: string) {
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      const [_, linkText, url] = match;
      const matchIndex = match.index;

      if (matchIndex > lastIndex) {
        const plainText = text.substring(lastIndex, matchIndex);
        elements.push(...formatLineBreaks(plainText, `text-${matchIndex}`));
      }

      elements.push(
        <Link href={url} key={`link-${matchIndex}`} className="chat-link">
          {linkText}
        </Link>
      );

      lastIndex = linkRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      const remainingText = text.substring(lastIndex);
      elements.push(...formatLineBreaks(remainingText, "text-end"));
    }

    return elements;
  }

  function formatLineBreaks(text: string, keyPrefix: string): React.ReactNode[] {
    return text.split("\n").flatMap((line, idx, array) => {
      const elements: React.ReactNode[] = [line];
      if (idx < array.length - 1) {
        elements.push(<br key={`${keyPrefix}-br-${idx}`} />);
      }
      return elements;
    });
  }

  return (
    <>
      <div className="drawer-body" ref={bodyRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble ${msg.sender}`}>
            <div>{parseMarkdownLinks(msg.text)}</div>

            {msg.sources && msg.sources.length > 0 && (
              <div className="chat-sources">
                <div className="chat-sources-title">Sources</div>
                <div className="chat-sources-list">
                  {msg.sources.map((src) => (
                    <Link
                      href={`/scheme/${src.scheme_id}`}
                      key={src.scheme_id}
                      className="chat-source-link"
                    >
                      <span>📎</span> {src.scheme_name}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble advisor">
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      <div className="drawer-footer">
        <form onSubmit={handleSend} className="chat-input-form">
          <input
            type="text"
            className="chat-input-field"
            placeholder="Ask about Punjab scholarships..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <button type="submit" className="chat-send-btn" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </>
  );
}
