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
 * Lightweight inline markdown-to-JSX renderer.
 * Handles: ### headings, **bold**, *italic*, `code`, - list items, numbered lists, and \n newlines.
 * No external library required.
 */
function renderMarkdown(text) {
  if (!text || typeof text !== 'string') return null;

  const lines = text.split('\n');
  const elements = [];
  let listBuffer = [];

  const flushList = () => {
    if (listBuffer.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} style={{ margin: '6px 0', paddingLeft: '18px', listStyle: 'none' }}>
          {listBuffer.map((item, i) => (
            <li key={i} style={{ padding: '3px 0', fontSize: '13px', lineHeight: '1.55', position: 'relative', paddingLeft: '14px' }}>
              <span style={{ position: 'absolute', left: 0, color: '#f59e0b', fontWeight: '700' }}>•</span>
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty line → flush any pending list and add spacer
    if (trimmed === '') {
      flushList();
      elements.push(<div key={`sp-${i}`} style={{ height: '8px' }} />);
      continue;
    }

    // ### Heading
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <div key={`h-${i}`} style={{
          fontSize: '14px',
          fontWeight: '700',
          color: '#f8fafc',
          marginBottom: '6px',
          marginTop: elements.length > 0 ? '4px' : '0',
          letterSpacing: '0.2px',
          borderBottom: '1px solid rgba(245, 158, 11, 0.25)',
          paddingBottom: '6px',
        }}>
          {renderInline(trimmed.slice(4))}
        </div>
      );
      continue;
    }

    // - List item or numbered list (e.g. "1. something")
    if (/^[-•]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed)) {
      const content = trimmed.replace(/^[-•]\s*/, '').replace(/^\d+\.\s*/, '');
      listBuffer.push(content);
      continue;
    }

    // Regular paragraph line
    flushList();
    elements.push(
      <div key={`p-${i}`} style={{ fontSize: '13px', lineHeight: '1.55', color: '#e2e8f0' }}>
        {renderInline(trimmed)}
      </div>
    );
  }

  flushList();
  return <>{elements}</>;
}

/**
 * Parse inline markdown: **bold**, *italic*, `code`
 */
function renderInline(text) {
  if (!text) return null;

  // Split by patterns: **bold**, *italic*, `code`
  const parts = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // Try **bold** first
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Try `code`
    const codeMatch = remaining.match(/`([^`]+)`/);
    // Try *italic*
    const italicMatch = remaining.match(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/);

    // Find the earliest match
    let earliest = null;
    let type = null;

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
      parts.push(<span key={keyIdx++}>{remaining}</span>);
      break;
    }

    // Text before match
    if (earliest.index > 0) {
      parts.push(<span key={keyIdx++}>{remaining.slice(0, earliest.index)}</span>);
    }

    // The matched content
    if (type === 'bold') {
      parts.push(
        <strong key={keyIdx++} style={{ fontWeight: '700', color: '#f8fafc' }}>
          {earliest[1]}
        </strong>
      );
    } else if (type === 'code') {
      parts.push(
        <code key={keyIdx++} style={{
          background: 'rgba(56, 189, 248, 0.12)',
          color: '#38bdf8',
          padding: '1px 5px',
          borderRadius: '4px',
          fontSize: '12px',
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: '500',
          border: '1px solid rgba(56, 189, 248, 0.2)',
        }}>
          {earliest[1]}
        </code>
      );
    } else if (type === 'italic') {
      parts.push(
        <em key={keyIdx++} style={{ fontStyle: 'italic', color: '#cbd5e1' }}>
          {earliest[1]}
        </em>
      );
    }

    remaining = remaining.slice(earliest.index + earliest[0].length);
  }

  return <>{parts}</>;
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
