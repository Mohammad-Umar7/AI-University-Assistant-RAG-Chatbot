import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import SuggestedQuestions from './components/SuggestedQuestions'
import { sendMessage } from './api'

const WELCOME = {
  role: 'assistant',
  content:
    "Hello! I'm the **AAU AI Assistant** for Al Ain University. I can help you with information about programs, admissions, fees, academic calendar, campus facilities, and more.\n\nHow can I help you today?",
  sources: [],
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleSend = useCallback(
    async (text) => {
      const question = (text ?? input).trim()
      if (!question || isLoading) return

      setInput('')
      setMessages((prev) => [...prev, { role: 'user', content: question }])
      setIsLoading(true)

      try {
        const result = await sendMessage(question, history)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: result.answer, sources: result.sources },
        ])
        setHistory((prev) => [
          ...prev,
          { role: 'user', content: question },
          { role: 'assistant', content: result.answer },
        ])
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content:
              "I'm having trouble connecting to the server right now. Please try again or contact AAU directly at **+800-22864**.",
            sources: [],
          },
        ])
      } finally {
        setIsLoading(false)
      }
    },
    [input, isLoading, history]
  )

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

  const showSuggestions = messages.length <= 2

  return (
    <div className={`app${sidebarOpen ? ' sidebar-open' : ''}`}>
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onTopicClick={handleSend}
      />

      <div className="main">
        <header className="header">
          <button className="menu-btn" onClick={() => setSidebarOpen((v) => !v)}>
            ☰
          </button>
          <div className="header-brand">
            <div className="header-logo-box">AAU</div>
            <div>
              <div className="header-title">AAU AI Assistant</div>
              <div className="header-sub">Al Ain University — جامعة العين</div>
            </div>
          </div>
          <button className="clear-btn" onClick={handleClear}>
            Clear Chat
          </button>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} />

        {showSuggestions && (
          <SuggestedQuestions onSelect={handleSend} disabled={isLoading} />
        )}

        <div className="input-area">
          <input
            className="input-field"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
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
