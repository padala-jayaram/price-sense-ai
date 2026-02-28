import { useState, useRef, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({ collapsed, onToggle, conversations, activeId, onNewChat, onSelectChat, onDeleteChat, onRenameChat }) {
  const [menuOpen, setMenuOpen] = useState(null);
  const [renaming, setRenaming] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const menuRef = useRef(null);
  const renameRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(null);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    if (renaming && renameRef.current) {
      renameRef.current.focus();
      renameRef.current.select();
    }
  }, [renaming]);

  const handleRenameStart = (id, currentName) => {
    setMenuOpen(null);
    setRenaming(id);
    setRenameValue(currentName);
  };

  const handleRenameSubmit = (id) => {
    const trimmed = renameValue.trim();
    if (trimmed && trimmed !== '') {
      onRenameChat(id, trimmed);
    }
    setRenaming(null);
  };

  const handleDelete = (id) => {
    setMenuOpen(null);
    onDeleteChat(id);
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sb-top">
        <span className="sb-logo">Price Sense AI</span>
        <button className="sb-close" onClick={onToggle} title="Close sidebar">&#x2715;</button>
      </div>

      <button className="sb-new-chat" onClick={onNewChat}>&#xFF0B; New chat</button>

      <hr className="sb-divider" />

      <p className="sb-label">Your chats</p>

      <div className="sb-chat-list">
        {conversations.length > 0 ? (
          conversations.map(([id, conv]) => (
            <div key={id} className={`sb-chat-item ${id === activeId ? 'active' : ''}`}>
              {renaming === id ? (
                <input
                  ref={renameRef}
                  className="sb-rename-input"
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRenameSubmit(id);
                    if (e.key === 'Escape') setRenaming(null);
                  }}
                  onBlur={() => handleRenameSubmit(id)}
                />
              ) : (
                <button className="sb-chat-btn" onClick={() => onSelectChat(id)}>
                  {conv.name.length > 28 ? conv.name.slice(0, 28) + '...' : conv.name}
                </button>
              )}
              <div className="sb-menu-anchor" ref={menuOpen === id ? menuRef : null}>
                <button
                  className="sb-dots"
                  onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === id ? null : id); }}
                  title="Options"
                >
                  &#x22EE;
                </button>
                {menuOpen === id && (
                  <div className="sb-menu">
                    <button className="sb-menu-option" onClick={() => handleRenameStart(id, conv.name)}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                      Rename
                    </button>
                    <button className="sb-menu-option sb-menu-delete" onClick={() => handleDelete(id)}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <p className="sb-empty">No chats yet. Click &#xFF0B; to start.</p>
        )}
      </div>
    </aside>
  );
}
