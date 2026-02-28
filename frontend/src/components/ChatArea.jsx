import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import './ChatArea.css';

export default function ChatArea({ messages, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-area">
      {messages.map((msg, i) => (
        <ChatMessage key={i} message={msg} />
      ))}
      {loading && (
        <div className="chat-loading">
          <span className="chat-loading-avatar">✨</span>
          <span className="chat-loading-dots">Thinking...</span>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
