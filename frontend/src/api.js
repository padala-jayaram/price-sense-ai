const BASE = '/api';

export async function fetchProducts() {
  const res = await fetch(`${BASE}/products`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.products || [];
}

export async function analyze({ product, discount_pct, duration_days, timing }) {
  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product, discount_pct, duration_days, timing }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
  return res.json();
}

export async function chat({ message, conversation_history, last_context }) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_history, last_context }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Chat failed');
  return res.json();
}
