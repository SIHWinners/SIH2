import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, X, Sparkles, User } from 'lucide-react';

export default function CopilotModal({ isOpen, onClose, selectedWell }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hello! I am the **Oil India Digital Twin Operations Copilot**. I analyze live telemetry, SCADA streams, and ML models across our Baghewala SRP and CSS wells. How can I assist you with ${selectedWell || 'the field'} today?`,
      time: 'Just now',
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
      const resp = await fetch('/api/v1/copilot/chat', {
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
                  whiteSpace: 'pre-wrap',
                }}
              >
                {msg.text}
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
