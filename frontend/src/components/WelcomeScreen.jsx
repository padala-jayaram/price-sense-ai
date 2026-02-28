import InputControls from './InputControls';
import ChatInput from './ChatInput';
import './WelcomeScreen.css';

const SCENARIOS = [
  { label: '📊 15% off Basmati Rice', product: 'Basmati Rice 5lb', discount: 15, timing: 'Next Week' },
  { label: '📊 20% off Cold Brew', product: 'Cold Brew Coffee 32oz', discount: 20, timing: 'Next Week' },
  { label: '📊 10% off Aged Cheddar', product: 'Aged Cheddar Cheese 8oz', discount: 10, timing: 'Holiday Season' },
  { label: '📊 25% off Potato Chips', product: 'Sea Salt Potato Chips 8oz', discount: 25, timing: 'Next Week' },
];

export default function WelcomeScreen({ products, onAnalyze, loading, onChat, chatDisabled }) {
  return (
    <div className="welcome">
      <div className="welcome-top">
        <InputControls products={products} onAnalyze={onAnalyze} loading={loading} />
        <p className="greeting">
          Select a product and discount above, then click <strong>Analyze</strong> to get a data-driven promotion recommendation.
        </p>
      </div>
      <div className="welcome-middle">
        <ChatInput onSend={onChat} disabled={chatDisabled} />
      </div>
      <div className="scenario-row">
        {SCENARIOS.map((s, i) => (
          <button
            key={i}
            className="scenario-card"
            disabled={loading}
            onClick={() => onAnalyze({ product: s.product, discount_pct: s.discount, duration_days: 7, timing: s.timing })}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
