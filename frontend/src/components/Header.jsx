import './Header.css';

export default function Header({ darkMode, onToggleDark, sidebarCollapsed, onOpenSidebar }) {
  return (
    <header className="header">
      <div className="header-left">
        {sidebarCollapsed && (
          <button className="header-menu-btn" onClick={onOpenSidebar} title="Open sidebar">☰</button>
        )}
        {sidebarCollapsed && <span className="header-logo">📈 Price Sense AI</span>}
      </div>
      <div className="header-right">
        <label className="toggle">
          <input type="checkbox" checked={darkMode} onChange={onToggleDark} />
          <span className="toggle-slider">{darkMode ? '🌙' : '☀️'}</span>
        </label>
        <div className="avatar">G</div>
        <span className="avatar-name">Guest</span>
      </div>
    </header>
  );
}
