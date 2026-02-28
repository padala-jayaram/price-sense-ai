import { useState, useCallback } from 'react';

function createConv() {
  const id = crypto.randomUUID().slice(0, 8);
  return {
    id,
    data: {
      name: 'New Chat',
      messages: [],
      lastContext: null,
      createdAt: new Date().toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
    },
  };
}

export default function useConversations() {
  const first = createConv();
  const [conversations, setConversations] = useState({ [first.id]: first.data });
  const [activeId, setActiveId] = useState(first.id);

  const newConversation = useCallback(() => {
    const c = createConv();
    setConversations(prev => ({ ...prev, [c.id]: c.data }));
    setActiveId(c.id);
    return c.id;
  }, []);

  const switchConversation = useCallback((id) => {
    setActiveId(id);
  }, []);

  const addMessage = useCallback((convId, msg) => {
    setConversations(prev => ({
      ...prev,
      [convId]: {
        ...prev[convId],
        messages: [...prev[convId].messages, msg],
      },
    }));
  }, []);

  const updateName = useCallback((convId, name) => {
    setConversations(prev => ({
      ...prev,
      [convId]: { ...prev[convId], name },
    }));
  }, []);

  const setLastContext = useCallback((convId, ctx) => {
    setConversations(prev => ({
      ...prev,
      [convId]: { ...prev[convId], lastContext: ctx },
    }));
  }, []);

  const deleteConversation = useCallback((convId) => {
    setConversations(prev => {
      const next = { ...prev };
      delete next[convId];
      const ids = Object.keys(next);
      if (ids.length === 0) {
        const c = createConv();
        setActiveId(c.id);
        return { [c.id]: c.data };
      }
      if (convId === activeId) {
        setActiveId(ids[0]);
      }
      return next;
    });
  }, [activeId]);

  const renameConversation = useCallback((convId, name) => {
    setConversations(prev => ({
      ...prev,
      [convId]: { ...prev[convId], name },
    }));
  }, []);

  const activeConv = conversations[activeId] || null;

  const sortedConvs = Object.entries(conversations)
    .sort(([, a], [, b]) => (b.createdAt || '').localeCompare(a.createdAt || ''))
    .filter(([, c]) => !(c.name === 'New Chat' && c.messages.length === 0));

  return {
    conversations,
    sortedConvs,
    activeId,
    activeConv,
    newConversation,
    switchConversation,
    addMessage,
    updateName,
    setLastContext,
    deleteConversation,
    renameConversation,
  };
}
