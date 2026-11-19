import { useState, useRef, useEffect } from 'react'
import { Sparkles, Send, Lock, RotateCcw, ArrowUpRight } from 'lucide-react'
import DataTable from './DataTable'

const formatTime = (d) => new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

// The bot is waiting for a yes/no answer
const asksConfirmation = (summary = '') => /reply 'yes' to confirm/i.test(summary)

function BotMessage({ msg, canConfirm, onSend, busy }) {
  const denied = msg.module === 'security'
  return (
    <div className="msg bot">
      <div className="bot-avatar"><Sparkles size={14} /></div>
      <div className="msg-body">
        <div className={`bubble bot-bubble ${denied ? 'denied' : ''}`}>
          {denied
            ? <div className="denied-row"><Lock size={15} className="bubble-icon" /><p className="summary">{msg.summary}</p></div>
            : <p className="summary">{msg.summary}</p>}
          {msg.table && <DataTable table={msg.table} />}
        </div>

        {canConfirm && (
          <div className="confirm-row">
            <button className="btn primary" disabled={busy} onClick={() => onSend('yes')}>Yes, confirm</button>
            <button className="btn" disabled={busy} onClick={() => onSend('no')}>No, cancel</button>
          </div>
        )}
        <div className="time">{formatTime(msg.time)}</div>
      </div>
    </div>
  )
}

function UserMessage({ msg }) {
  return (
    <div className="msg user">
      <div className="msg-body">
        <div className="bubble user-bubble">{msg.text}</div>
        <div className="time">{formatTime(msg.time)}</div>
      </div>
    </div>
  )
}

function ChatPanel({ messages, loading, onSend, onClear, actions, starters, contextLabel }) {
  const [input, setInput] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  const submit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSend(input)
    setInput('')
  }

  const lastBotId = [...messages].reverse().find((m) => m.sender === 'bot')?.id

  return (
    <section className="chat glass">
      <header className="chat-head">
        <div>
          <div className="chat-title">Assistant</div>
          <div className="chat-sub"><span className="dot-online" />{contextLabel}</div>
        </div>
        {messages.length > 0 && (
          <button className="ghost-btn" onClick={onClear} title="Start a new conversation">
            <RotateCcw size={14} /> New chat
          </button>
        )}
      </header>

      <div className="chat-scroll">
        {messages.length === 0 ? (
          <div className="empty">
            <div className="empty-mark"><Sparkles size={22} /></div>
            <h2>How can I help today?</h2>
            <p>Ask in plain English, or start with one of these.</p>
            <div className="starters">
              {starters.map((s) => (
                <button key={s.message} className="starter" onClick={() => onSend(s.message)}>
                  <span>{s.label}</span><ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((m) => m.sender === 'user'
              ? <UserMessage key={m.id} msg={m} />
              : <BotMessage key={m.id} msg={m} busy={loading} onSend={onSend}
                            canConfirm={m.id === lastBotId && !loading && asksConfirmation(m.summary)} />)}
            {loading && (
              <div className="msg bot">
                <div className="bot-avatar"><Sparkles size={14} /></div>
                <div className="bubble bot-bubble typing"><i /><i /><i /></div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      <div className="chat-foot">
        {messages.length > 0 && actions.length > 0 && (
          <div className="chips">
            {actions.map((a) => (
              <button key={a.message} className="chip" disabled={loading} onClick={() => onSend(a.message)}>
                {a.label}
              </button>
            ))}
          </div>
        )}
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(e) => setInput(e.target.value)}
                 placeholder="Ask about leave, stock, orders, invoices…" aria-label="Message" />
          <button type="submit" className="send-btn" disabled={loading || !input.trim()} title="Send">
            <Send size={16} />
          </button>
        </form>
      </div>
    </section>
  )
}

export default ChatPanel