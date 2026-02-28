import { useState, useMemo, useEffect } from 'react';
import CustomSelect from './CustomSelect';
import './InputControls.css';

const TIMINGS = ['Next Week', 'This Week', 'Next Month', 'Holiday Season', 'Q1', 'Q2', 'Q3', 'Q4'];

function toTitleCase(str) {
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export default function InputControls({ products, onAnalyze, loading }) {
  const categories = useMemo(() => {
    const cats = [...new Set(products.map(p => p.category))];
    return cats.map(c => ({ value: c, label: toTitleCase(c) }));
  }, [products]);

  const [category, setCategory] = useState('');
  const [product, setProduct] = useState('');
  const [discount, setDiscount] = useState(25);
  const [duration, setDuration] = useState(7);
  const [timing, setTiming] = useState('Next Week');

  // Set initial category when products load
  useEffect(() => {
    if (categories.length > 0 && !category) {
      setCategory(categories[0].value);
    }
  }, [categories, category]);

  const filteredProducts = useMemo(() => {
    return products.filter(p => p.category === category);
  }, [products, category]);

  // Reset product when category changes
  useEffect(() => {
    if (filteredProducts.length > 0) {
      setProduct(filteredProducts[0].product_name);
    }
  }, [category, filteredProducts]);

  const productOptions = filteredProducts.map(p => ({
    value: p.product_name,
    label: p.product_name,
  }));

  const handleAnalyze = () => {
    onAnalyze({ product, discount_pct: discount, duration_days: duration, timing });
  };

  return (
    <div className="input-controls">
      <div className="input-field input-category">
        <span className="input-label">Category</span>
        <CustomSelect value={category} options={categories} onChange={setCategory} />
      </div>

      <div className="input-field input-product">
        <span className="input-label">Product</span>
        {productOptions.length > 0 ? (
          <CustomSelect value={product} options={productOptions} onChange={setProduct} />
        ) : (
          <input type="text" value={product} onChange={e => setProduct(e.target.value)} placeholder="Product name" />
        )}
      </div>

      <div className="input-field input-discount">
        <span className="input-label">Discount</span>
        <div className="input-discount-row">
          <input
            type="range"
            min={1} max={50} step={1}
            value={discount}
            onChange={e => setDiscount(Number(e.target.value))}
          />
          <input
            className="range-input"
            type="number"
            min={1} max={50}
            value={discount}
            onChange={e => {
              const v = parseInt(e.target.value, 10);
              if (!isNaN(v) && v >= 1 && v <= 50) setDiscount(v);
              else if (e.target.value === '') setDiscount('');
            }}
            onBlur={() => { if (discount === '' || discount < 1) setDiscount(5); }}
          /><span className="range-suffix">%</span>
        </div>
      </div>

      <div className="input-field input-duration">
        <span className="input-label">Duration</span>
        <div className="input-duration-row">
          <input
            className="duration-input"
            type="number"
            min={1} max={365}
            value={duration}
            onChange={e => {
              const v = parseInt(e.target.value, 10);
              if (!isNaN(v) && v >= 1 && v <= 365) setDuration(v);
              else if (e.target.value === '') setDuration('');
            }}
            onBlur={() => { if (duration === '' || duration < 1) setDuration(7); }}
          /><span className="duration-suffix">days</span>
        </div>
      </div>

      <div className="input-field input-timing">
        <span className="input-label">Timing</span>
        <CustomSelect value={timing} options={TIMINGS} onChange={setTiming} />
      </div>

      <button className="analyze-btn" onClick={handleAnalyze} disabled={loading}>
        {loading ? '⏳ ...' : '🔍 Analyze'}
      </button>
    </div>
  );
}
