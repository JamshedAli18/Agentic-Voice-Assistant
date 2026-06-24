// src/components/ChatHistory.jsx

import { useEffect, useRef } from 'react';
import './ChatHistory.css';

export default function ChatHistory({ messages, status }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-empty">
        <div className="chat-empty-icon">💬</div>
        <h2>Voice AI Assistant</h2>
        <p>Click the microphone or type your message to start a conversation. I'll respond with text and voice.</p>
      </div>
    );
  }

  return (
    <div className="chat-history">
      {messages.map((msg) => (
        <div key={msg.id} className={`chat-message chat-message--${msg.role}`}>
          <div className="chat-avatar">
            {msg.role === 'user' ? 'You' : 'AI'}
          </div>
          <div className="chat-bubble">
            <span className="chat-role">
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </span>
            <p className="chat-content">
              {msg.isStreaming ? (
                <>
                  {msg.content}
                  <span className="chat-streaming">
                    <span className="chat-streaming-dot"></span>
                    <span className="chat-streaming-dot"></span>
                    <span className="chat-streaming-dot"></span>
                  </span>
                </>
              ) : (
                msg.content
              )}
            </p>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}