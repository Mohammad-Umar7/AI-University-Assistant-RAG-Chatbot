import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function useTypewriter(text, active) {
  const [displayed, setDisplayed] = useState(active ? '' : text)
  const [done, setDone] = useState(!active)

  useEffect(() => {
    if (!active) {
      setDisplayed(text)
      setDone(true)
      return
    }
    let i = 0
    setDisplayed('')
    setDone(false)
    const id = setInterval(() => {
      i += 2
      if (i >= text.length) {
        clearInterval(id)
        setDisplayed(text)
        setDone(true)
      } else {
        setDisplayed(text.slice(0, i))
      }
    }, 15)
    return () => clearInterval(id)
  }, [text, active])

  return { displayed, done }
}

export default function MessageBubble({ role, content, sources, isNew }) {
  const isUser = role === 'user'
  const { displayed, done } = useTypewriter(content, !isUser && !!isNew)

  return (
    <div className={`message ${role}`}>
      <div className="avatar">{isUser ? 'You' : 'AAU'}</div>
      <div className="bubble-wrap">
        <div className="bubble">
          {isUser
            ? content
            : (
              <>
                <ReactMarkdown>{displayed}</ReactMarkdown>
                {!done && <span className="typing-cursor">▋</span>}
              </>
            )
          }
        </div>
        {!isUser && done && sources && sources.length > 0 && (
          <div className="sources">
            {sources.map(s => (
              <span key={s} className="source-tag">{s}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
