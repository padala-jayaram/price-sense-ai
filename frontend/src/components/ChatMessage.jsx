import ReactMarkdown from 'react-markdown';
import AnalysisCard from './AnalysisCard';
import './ChatMessage.css';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const avatar = isUser ? '👨‍💻' : '✨';

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'}`}>
      <span className="chat-msg-avatar">{avatar}</span>
      <div className="chat-msg-body">
        {message.type === 'analysis' && message.recommendation ? (
          <AnalysisCard rec={message.recommendation} debugInfo={message.debugInfo} />
        ) : isUser ? (
          <p className="chat-msg-text">{message.content}</p>
        ) : (
          <div className="chat-msg-md">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
