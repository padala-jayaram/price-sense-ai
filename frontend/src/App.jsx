import { useState, useEffect, useCallback } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import InputControls from './components/InputControls';
import WelcomeScreen from './components/WelcomeScreen';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import useConversations from './hooks/useConversations';
import { fetchProducts, analyze, chat } from './api';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const {
    sortedConvs, activeId, activeConv,
    newConversation, switchConversation,
    addMessage, updateName, setLastContext,
    deleteConversation, renameConversation,
  } = useConversations();

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => {});
  }, []);

  const handleAnalyze = useCallback(async ({ product, discount_pct, duration_days, timing }) => {
    addMessage(activeId, {
      role: 'user',
      type: 'text',
      content: `Analyze: ${discount_pct}% off ${product} for ${duration_days} days (${timing})`,
    });
    setLoading(true);
    try {
      const data = await analyze({ product, discount_pct, duration_days, timing });
      const rec = data.recommendation;
      addMessage(activeId, {
        role: 'assistant',
        type: 'analysis',
        content: `**${rec.verdict || '?'}**: ${rec.verdict_summary || ''}`,
        recommendation: rec,
        debugInfo: {
          matchedProduct: data.matched_product,
          contextTokens: data.context_tokens_estimate,
        },
      });
      setLastContext(activeId, data.context || '');
      if (activeConv.name === 'New Chat') {
        updateName(activeId, `${discount_pct}% off ${product.split(' ')[0]}`);
      }
    } catch (e) {
      addMessage(activeId, { role: 'assistant', type: 'text', content: `Error: ${e.message}` });
    }
    setLoading(false);
  }, [activeId, activeConv, addMessage, updateName, setLastContext]);

  const handleChat = useCallback(async (message) => {
    addMessage(activeId, { role: 'user', type: 'text', content: message });
    setLoading(true);
    try {
      const history = activeConv.messages.slice(-10).map(m => ({ role: m.role, content: m.content }));
      const data = await chat({ message, conversation_history: history, last_context: activeConv.lastContext || '' });
      addMessage(activeId, { role: 'assistant', type: 'text', content: data.reply });
    } catch (e) {
      addMessage(activeId, { role: 'assistant', type: 'text', content: `Error: ${e.message}` });
    }
    if (activeConv.name === 'New Chat') {
      updateName(activeId, message.length > 25 ? message.slice(0, 25) + '...' : message);
    }
    setLoading(false);
  }, [activeId, activeConv, addMessage, updateName]);

  const hasMessages = activeConv && activeConv.messages.length > 0;

  return (
    <div className="app" data-theme={darkMode ? 'dark' : 'light'}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(c => !c)}
        conversations={sortedConvs}
        activeId={activeId}
        onNewChat={newConversation}
        onSelectChat={switchConversation}
        onDeleteChat={deleteConversation}
        onRenameChat={renameConversation}
      />
      <main className={`main ${sidebarCollapsed ? 'expanded' : ''}`}>
        <Header
          darkMode={darkMode}
          onToggleDark={() => setDarkMode(d => !d)}
          sidebarCollapsed={sidebarCollapsed}
          onOpenSidebar={() => setSidebarCollapsed(false)}
        />
        {hasMessages ? (
          <>
            <InputControls products={products} onAnalyze={handleAnalyze} loading={loading} />
            <ChatArea messages={activeConv.messages} loading={loading} />
            <div className="chat-input-wrap">
              <ChatInput onSend={handleChat} disabled={loading} />
            </div>
          </>
        ) : (
          <WelcomeScreen products={products} onAnalyze={handleAnalyze} loading={loading} onChat={handleChat} chatDisabled={loading} />
        )}
      </main>
    </div>
  );
}

export default App;
