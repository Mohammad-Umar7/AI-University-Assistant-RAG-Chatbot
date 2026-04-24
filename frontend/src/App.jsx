import { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import SuggestedQuestions from './components/SuggestedQuestions'
import { sendMessage } from './api'

const WELCOME = {
  role: 'assistant',
  content: "Hello! I'm the **AAU AI Assistant** for Al Ain University. I can help you with programs, admissions, fees, academic calendar, campus life, and more.\n\nHow can I help you today?",
  sources: [],
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])

  const handleSend = useCallback(async (text) => {
    const q = (text ?? input).trim()
    if (!q || isLoading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setIsLoading(true)

    try {
      const result = await sendMessage(q, history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        sources: result.sources,
      }])
      setHistory(prev => [
        ...prev,
        { role: 'user', content: q },
        { role: 'assistant', content: result.answer },
      ])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting right now. Please try again or contact AAU at **+800-22864**.",
        sources: [],
      }])
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, history])

  const handleClear = () => {
    setMessages([WELCOME])
    setHistory([])
    setInput('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="app">
      <div className="chat-card">

        <header className="header">
          <div className="header-brand">
            <div className="header-logo">AAU</div>
            <div>
              <div className="header-title">AAU AI Assistant</div>
              <div className="header-sub">Al Ain University · جامعة العين</div>
            </div>
          </div>
          <button className="clear-btn" onClick={handleClear}>Clear chat</button>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} />

        {messages.length <= 2 && (
          <SuggestedQuestions onSelect={handleSend} disabled={isLoading} />
        )}

        <div className="input-area">
          <input
            className="input-field"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask me anything about AAU..."
            disabled={isLoading}
          />
          <button
            className="send-btn"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
          >
            Send
          </button>
        </div>

      </div>
    </div>
  )
}
