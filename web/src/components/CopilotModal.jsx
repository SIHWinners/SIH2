import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, X, Sparkles, User, BarChart3, AlertTriangle, Activity, Flame, Cpu, Sun, Layers, ChevronRight } from 'lucide-react';
import { apiUrl } from '../api';

const getActionIcon = (label) => {
  const l = label.toLowerCase();
  if (l.includes('summary') || l.includes('overview')) return <BarChart3 size={13} color="#38bdf8" />;
  if (l.includes('critical') || l.includes('srp-004') || l.includes('diagnose')) return <AlertTriangle size={13} color="#f59e0b" />;
  if (l.includes('dyno') || l.includes('dynamometer') || l.includes('card')) return <Activity size={13} color="#a855f7" />;
  if (l.includes('css') || l.includes('thermal') || l.includes('steam')) return <Flame size={13} color="#f43f5e" />;
  if (l.includes('ai') || l.includes('spm') || l.includes('optimize') || l.includes('speed')) return <Cpu size={13} color="#10b981" />;
  if (l.includes('weather') || l.includes('temperature') || l.includes('desert')) return <Sun size={13} color="#fbbf24" />;
  return <Layers size={13} color="#94a3b8" />;
};

/**
 * Clean any raw LaTeX math or formula string into clean, human-readable Unicode & math typography.
 */
function cleanLatexMath(expr) {
  if (!expr || typeof expr !== 'string') return '';
  let s = expr.trim();

  // Strip enclosing $$ or $
  if (s.startsWith('$$') && s.endsWith('$$') && s.length >= 4) {
    s = s.slice(2, -2).trim();
  } else if (s.startsWith('$') && s.endsWith('$') && s.length >= 2) {
    s = s.slice(1, -1).trim();
  }

  // Fractions: \frac{num}{den} -> (num) / (den)
  for (let k = 0; k < 5 && /\\frac\{([^{}]+)\}\{([^{}]+)\}/.test(s); k++) {
    s = s.replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, '($1) / ($2)');
  }

  // Second derivatives & partials
  s = s.replace(/\\partial\^2\s*/g, '∂²');
  s = s.replace(/\\partial\s*/g, '∂');

  // Greek letters
  s = s.replace(/\\rho\b/g, 'ρ');
  s = s.replace(/\\mu\b/g, 'μ');
  s = s.replace(/\\nu\b/g, 'ν');
  s = s.replace(/\\alpha\b/g, 'α');
  s = s.replace(/\\beta\b/g, 'β');
  s = s.replace(/\\Delta\b/g, 'Δ');
  s = s.replace(/\\theta\b/g, 'θ');
  s = s.replace(/\\sigma\b/g, 'σ');
  s = s.replace(/\\pi\b/g, 'π');
  s = s.replace(/\\omega\b/g, 'ω');

  // Math operators
  s = s.replace(/\\times\b/g, '×');
  s = s.replace(/\\cdot\b/g, '·');
  s = s.replace(/\\approx\b/g, '≈');
  s = s.replace(/\\le\b|\\leq\b/g, '≤');
  s = s.replace(/\\ge\b|\\geq\b/g, '≥');
  s = s.replace(/\\ne\b|\\neq\b/g, '≠');
  s = s.replace(/\\pm\b/g, '±');
  s = s.replace(/\\circ\b/g, '°');
  s = s.replace(/\\infty\b/g, '∞');
  s = s.replace(/\\sqrt\{([^{}]+)\}/g, '√($1)');

  // \text{...} -> ...
  s = s.replace(/\\text\{([^{}]+)\}/g, '$1');

  // Logarithms
  s = s.replace(/\\log_\{10\}|\\log_10/g, 'log₁₀');
  s = s.replace(/\\log\b/g, 'log');

  // Superscripts
  s = s.replace(/\^2\b|\^\{2\}/g, '²');
  s = s.replace(/\^3\b|\^\{3\}/g, '³');
  s = s.replace(/\^0\b|\^\{0\}/g, '⁰');
  s = s.replace(/\^1\b|\^\{1\}/g, '¹');
  s = s.replace(/\^-\b|\^\{-\}/g, '⁻');
  s = s.replace(/\^t\b|\^\{t\}/g, 'ᵗ');

  // Subscripts: _{...} -> _...
  s = s.replace(/_\{([^{}]+)\}/g, '_$1');

  // Remove any remaining stray backslashes before words
  s = s.replace(/\\([a-zA-Z]+)/g, '$1');

  // Remove any stray dollars
  s = s.replace(/\$/g, '');

  // Clean redundant whitespace
  s = s.replace(/\s+/g, ' ').trim();
  return s;
}

/**
 * Parse inline markdown: **bold**, *italic*, `code`, $math$
 */
function renderInline(text, depth = 0) {
  if (!text) return null;
  if (depth > 4) return text;

  const parts = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // Try $math$ first
    const mathMatch = remaining.match(/\$([^$\n]+?)\$/);
    // Try **bold**
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Try `code`
    const codeMatch = remaining.match(/`([^`]+)`/);
    // Try *italic*
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)/);

    let earliest = null;
    let type = null;

    if (mathMatch && (!earliest || mathMatch.index < earliest.index)) {
      earliest = mathMatch;
      type = 'math';
    }
    if (boldMatch && (!earliest || boldMatch.index < earliest.index)) {
      earliest = boldMatch;
      type = 'bold';
    }
    if (codeMatch && (!earliest || codeMatch.index < earliest.index)) {
      earliest = codeMatch;
      type = 'code';
    }
    if (italicMatch && (!earliest || italicMatch.index < earliest.index)) {
      earliest = italicMatch;
      type = 'italic';
    }

    if (!earliest) {
      const cleanPlain = remaining.includes('\\') ? cleanLatexMath(remaining) : remaining;
      parts.push(<span key={keyIdx++}>{cleanPlain}</span>);
      break;
    }

    if (earliest.index > 0) {
      const beforeText = remaining.slice(0, earliest.index);
      const cleanBefore = beforeText.includes('\\') ? cleanLatexMath(beforeText) : beforeText;
      parts.push(<span key={keyIdx++}>{cleanBefore}</span>);
    }

    if (type === 'math') {
      parts.push(
        <span
          key={keyIdx++}
          style={{
            display: 'inline-block',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.28)',
            color: '#38bdf8',
            padding: '0 6px',
            borderRadius: '4px',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px',
            fontWeight: '500',
            margin: '0 2px',
            verticalAlign: 'baseline',
          }}
        >
          {cleanLatexMath(earliest[1])}
        </span>
      );
    } else if (type === 'bold') {
      parts.push(
        <strong key={keyIdx++} style={{ fontWeight: '700', color: '#f8fafc' }}>
          {renderInline(earliest[1], depth + 1)}
        </strong>
      );
    } else if (type === 'code') {
      parts.push(
        <code
          key={keyIdx++}
          style={{
            background: 'rgba(56, 189, 248, 0.12)',
            color: '#38bdf8',
            padding: '1px 5px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: '500',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            verticalAlign: 'baseline',
          }}
        >
          {cleanLatexMath(earliest[1])}
        </code>
      );
    } else if (type === 'italic') {
      parts.push(
        <em key={keyIdx++} style={{ fontStyle: 'italic', color: '#cbd5e1' }}>
          {renderInline(earliest[1], depth + 1)}
        </em>
      );
    }

    remaining = remaining.slice(earliest.index + earliest[0].length);
  }

  return <>{parts}</>;
}

/**
 * Comprehensive inline markdown & engineering equation renderer.
 * Handles headings, section headers, block math, lists, sub-bullets, and typography.
 */
function renderMarkdown(text) {
  if (!text || typeof text !== 'string') return null;

  const lines = text.split('\n');
  const elements = [];
  let listBuffer = [];
  let inEquationBlock = false;
  let equationBuffer = [];

  const flushList = () => {
    if (listBuffer.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} style={{ margin: '6px 0', padding: 0, listStyle: 'none' }}>
          {listBuffer.map((item, i) => (
            <li
              key={i}
              style={{
                padding: '3px 0',
                fontSize: '13px',
                lineHeight: '1.55',
                position: 'relative',
                paddingLeft: item.isIndented ? '28px' : '16px',
                color: '#e2e8f0',
              }}
            >
              {item.type === 'bullet' ? (
                <span
                  style={{
                    position: 'absolute',
                    left: item.isIndented ? '14px' : '0',
                    color: item.isIndented ? '#94a3b8' : '#f59e0b',
                    fontWeight: '700',
                    fontSize: item.isIndented ? '10px' : '13px',
                  }}
                >
                  {item.isIndented ? '▫' : '•'}
                </span>
              ) : (
                <span
                  style={{
                    position: 'absolute',
                    left: '0',
                    color: '#f59e0b',
                    fontWeight: '700',
                    fontSize: '11px',
                  }}
                >
                  {item.num}
                </span>
              )}
              {renderInline(item.content)}
            </li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  };

  const flushEquation = () => {
    if (equationBuffer.length > 0) {
      const eqText = equationBuffer.join(' ').trim();
      elements.push(
        <div
          key={`eq-${elements.length}`}
          style={{
            margin: '8px 0',
            padding: '8px 12px',
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid rgba(56, 189, 248, 0.28)',
            borderLeft: '3px solid #38bdf8',
            borderRadius: '6px',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12.5px',
            color: '#38bdf8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '10px',
            boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.4)',
            overflowX: 'auto',
          }}
        >
          <span style={{ fontWeight: '500', letterSpacing: '0.3px', whiteSpace: 'nowrap' }}>
            {cleanLatexMath(eqText)}
          </span>
          <span
            style={{
              fontSize: '9px',
              textTransform: 'uppercase',
              color: '#64748b',
              letterSpacing: '0.8px',
              padding: '1px 5px',
              background: 'rgba(56, 189, 248, 0.08)',
              borderRadius: '3px',
              flexShrink: 0,
              fontWeight: '700',
            }}
          >
            Formula
          </span>
        </div>
      );
      equationBuffer = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Multi-line $$ equation block handling
    if (inEquationBlock) {
      if (trimmed.endsWith('$$')) {
        const content = trimmed.slice(0, -2).trim();
        if (content) equationBuffer.push(content);
        flushEquation();
        inEquationBlock = false;
      } else {
        equationBuffer.push(trimmed);
      }
      continue;
    }

    if (trimmed.startsWith('$$')) {
      flushList();
      if (trimmed.endsWith('$$') && trimmed.length > 2) {
        const content = trimmed.slice(2, -2).trim();
        equationBuffer.push(content);
        flushEquation();
      } else {
        inEquationBlock = true;
        const after = trimmed.slice(2).trim();
        if (after) equationBuffer.push(after);
      }
      continue;
    }

    // Empty line -> flush list and add spacer
    if (trimmed === '') {
      flushList();
      elements.push(<div key={`sp-${elements.length}`} style={{ height: '6px' }} />);
      continue;
    }

    // Headings: #, ##, ###
    if (/^#{1,3}\s/.test(trimmed)) {
      flushList();
      const headingContent = trimmed.replace(/^#{1,3}\s*/, '');
      elements.push(
        <div
          key={`h-${elements.length}`}
          style={{
            fontSize: '14px',
            fontWeight: '700',
            color: '#f8fafc',
            marginBottom: '6px',
            marginTop: elements.length > 0 ? '6px' : '0',
            letterSpacing: '0.2px',
            borderBottom: '1px solid rgba(245, 158, 11, 0.25)',
            paddingBottom: '5px',
          }}
        >
          {renderInline(headingContent)}
        </div>
      );
      continue;
    }

    // Major Section Headers: e.g. "**1. Operational Telemetry Comparison:**" or "**2. Physical Safety Envelope Bounding:**"
    const sectionMatch = trimmed.match(/^\*\*(\d+\.\s*[^*]+?)\*\*:?$/) || trimmed.match(/^(\d+\.\s+[A-Z][^:]+?:)$/);
    if (sectionMatch) {
      flushList();
      elements.push(
        <div
          key={`sec-${elements.length}`}
          style={{
            fontSize: '13px',
            fontWeight: '700',
            color: '#f8fafc',
            marginTop: elements.length > 0 ? '10px' : '2px',
            marginBottom: '4px',
            letterSpacing: '0.2px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span style={{ color: '#f59e0b', fontSize: '9px' }}>▶</span>
          <span>{renderInline(sectionMatch[1])}</span>
        </div>
      );
      continue;
    }

    // List item detection (bullets or numbered)
    const isIndented = rawLine.startsWith('  ') || rawLine.startsWith('\t');
    const bulletMatch = trimmed.match(/^[-•*]\s+(.*)$/);
    const numberMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);

    if (bulletMatch) {
      listBuffer.push({
        type: 'bullet',
        content: bulletMatch[1],
        isIndented,
      });
      continue;
    }

    if (numberMatch) {
      listBuffer.push({
        type: 'number',
        num: `${numberMatch[1]}.`,
        content: numberMatch[2],
        isIndented,
      });
      continue;
    }

    // Regular paragraph line
    flushList();
    elements.push(
      <div key={`p-${elements.length}`} style={{ fontSize: '13px', lineHeight: '1.55', color: '#e2e8f0', marginBottom: '2px' }}>
        {renderInline(trimmed)}
      </div>
    );
  }

  flushList();
  flushEquation();
  return <>{elements}</>;
}

export default function CopilotModal({ isOpen, onClose, selectedWell }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Welcome to the Oil India Digital Twin Operations Intelligence Console (Engineered by Team brain.exe_crashed for SIH26120).\n\nGrounded in continuous SCADA telemetry, thermodynamic reservoir modeling, and machine learning inferences across the Baghewala Asset.\n\nSelect an operational inquiry to initiate analysis:`,
      suggestedActions: [
        'Field Operations Summary',
        'Diagnose Critical Unit SRP-004',
        'Dynamometer Card Technical Analysis',
        'CSS Thermal Recovery Kinetics',
        'How AI Optimizes VFD Stroke Speed',
        'Thar Desert Surface Meteorological Telemetry',
      ],
      time: 'Ready',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    `Field Operations Summary`,
    `Why is SRP-004 in critical state?`,
    `Diagnose SRP-002 Fluid Pound`,
    `Explain CSS-101 Thermal Recovery`,
    `Recommend VFD Speed for ${selectedWell || 'SRP-001'}`,
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = { role: 'user', text: query, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const resp = await fetch(apiUrl('/api/v1/copilot/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      });
      const data = await resp.json();
      const botMsg = {
        role: 'assistant',
        text: data.answer,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestedActions: data.suggested_actions,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      const errorMsg = {
        role: 'assistant',
        text: 'Sorry, I encountered a temporary connection issue while querying field SCADA RTUs. Please try again.',
        time: 'Now',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: '460px',
      maxWidth: '100vw',
      background: 'rgba(11, 17, 32, 0.95)',
      backdropFilter: 'blur(16px)',
      borderLeft: '1px solid rgba(245, 158, 11, 0.3)',
      boxShadow: '-10px 0 40px rgba(0, 0, 0, 0.7)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{
        padding: '18px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(90deg, rgba(245, 158, 11, 0.12) 0%, transparent 100%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: '#f59e0b', borderRadius: '8px', padding: '6px', color: '#0b1120' }}>
            <Bot size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', margin: 0 }}>Oil India AI Copilot</h3>
            <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
              Grounded in Live SCADA & ML
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Quick Prompt Chips */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '6px', overflowX: 'auto' }}>
        {quickPrompts.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(chip)}
            style={{
              background: 'rgba(30, 41, 59, 0.7)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#94a3b8',
              fontSize: '11px',
              padding: '4px 10px',
              borderRadius: '9999px',
              whiteSpace: 'nowrap',
              cursor: 'pointer',
            }}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: '10px',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '90%',
            }}
          >
            {msg.role === 'assistant' && (
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0b1120', flexShrink: 0, marginTop: '2px' }}>
                <Bot size={16} />
              </div>
            )}
            <div>
              <div
                style={{
                  background: msg.role === 'user' ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' : 'rgba(15, 23, 42, 0.85)',
                  color: msg.role === 'user' ? '#0b1120' : '#f8fafc',
                  border: msg.role === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                  padding: '12px 14px',
                  fontSize: '13px',
                  lineHeight: '1.5',
                  fontWeight: msg.role === 'user' ? '600' : '400',
                }}
              >
                {msg.role === 'assistant' ? renderMarkdown(msg.text) : msg.text}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.6px', fontWeight: '700', color: '#64748b', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Activity size={12} color="#f59e0b" /> Recommended Operational Inquiries
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {msg.suggestedActions.map((action, actIdx) => (
                        <button
                          key={actIdx}
                          onClick={() => handleSend(action)}
                          style={{
                            background: 'rgba(14, 22, 38, 0.85)',
                            border: '1px solid rgba(56, 189, 248, 0.2)',
                            color: '#e2e8f0',
                            fontSize: '11px',
                            fontWeight: '500',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '8px',
                            transition: 'all 0.15s ease',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)';
                            e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.5)';
                            e.currentTarget.style.color = '#38bdf8';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(14, 22, 38, 0.85)';
                            e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.2)';
                            e.currentTarget.style.color = '#e2e8f0';
                          }}
                        >
                          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {getActionIcon(action)}
                            <span>{action}</span>
                          </span>
                          <ChevronRight size={12} style={{ opacity: 0.6, flexShrink: 0 }} />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span style={{ fontSize: '10px', color: '#64748b', marginTop: '3px', display: 'block', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                {msg.time}
              </span>
            </div>
            {msg.role === 'user' && (
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#38bdf8', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0b1120', flexShrink: 0, marginTop: '2px' }}>
                <User size={16} />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: '8px', color: '#94a3b8', fontSize: '12px', alignItems: 'center' }}>
            <Sparkles size={16} className="pulse-animation" /> Analyzing wellhead sensor vectors...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div style={{ padding: '14px', borderTop: '1px solid rgba(255,255,255,0.08)', background: 'rgba(15, 23, 42, 0.7)' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '8px' }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask AI Copilot about any well, dyno card, or thermal phase..."
            style={{
              flex: 1,
              background: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              padding: '10px 14px',
              color: '#f8fafc',
              fontSize: '13px',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: '0 16px', borderRadius: '8px' }}
            disabled={loading}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
