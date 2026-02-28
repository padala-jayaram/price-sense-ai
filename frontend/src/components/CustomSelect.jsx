import { useState, useRef, useEffect } from 'react';
import './CustomSelect.css';

export default function CustomSelect({ value, options, onChange, renderOption }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const matched = options.find(opt => (typeof opt === 'object' ? opt.value : opt) === value);
  const display = renderOption
    ? renderOption(value)
    : matched
      ? (typeof matched === 'object' ? matched.label : matched)
      : value;

  return (
    <div className="cselect" ref={ref}>
      <button className="cselect-trigger" onClick={() => setOpen(!open)} type="button" title={display}>
        <span className="cselect-value">{display}</span>
        <span className={`cselect-arrow ${open ? 'open' : ''}`}>&#9662;</span>
      </button>
      {open && (
        <ul className="cselect-menu">
          {options.map((opt) => {
            const val = typeof opt === 'object' ? opt.value : opt;
            const label = typeof opt === 'object' ? opt.label : (renderOption ? renderOption(opt) : opt);
            return (
              <li
                key={val}
                className={`cselect-option ${val === value ? 'selected' : ''}`}
                onClick={() => { onChange(val); setOpen(false); }}
              >
                {label}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
