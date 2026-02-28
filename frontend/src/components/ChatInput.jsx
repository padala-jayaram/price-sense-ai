import { useState } from 'react';
import './ChatInput.css';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const msg = text.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setText('');
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Ask about promotions or follow up on the analysis..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !text.trim()}>↑</button>
    </form>
  );
}
