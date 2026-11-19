import { useState, useRef, useCallback } from 'react'
import { sendMessage } from '../services/api'

/**
 * Holds the whole conversation: messages, the "typing" state, and send().
 * `onReply` runs after every bot reply (used to refresh the dashboard numbers).
 */
export function useChat(onReply) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const busy = useRef(false)
  const nextId = useRef(0)

  const send = useCallback(async (text) => {
    const clean = (text || '').trim()
    if (!clean || busy.current) return
    busy.current = true

    setMessages((prev) => [...prev, { id: ++nextId.current, sender: 'user', text: clean, time: new Date() }])
    setLoading(true)

    try {
      const data = await sendMessage(clean)
      setMessages((prev) => [...prev, {
        id: ++nextId.current, sender: 'bot', time: new Date(),
        summary: data.summary, table: data.table, module: data.module,
      }])
    } catch {
      setMessages((prev) => [...prev, {
        id: ++nextId.current, sender: 'bot', time: new Date(), module: 'general',
        summary: 'Sorry, I could not reach the server. Please try again in a moment.', table: null,
      }])
    } finally {
      busy.current = false
      setLoading(false)
      if (onReply) onReply()
    }
  }, [onReply])

  const clear = useCallback(() => setMessages([]), [])

  return { messages, loading, send, clear }
}