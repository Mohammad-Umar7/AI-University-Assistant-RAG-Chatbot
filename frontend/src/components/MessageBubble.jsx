import ReactMarkdown from 'react-markdown'

export default function MessageBubble({ role, content, sources }) {
  const isUser = role === 'user'

  return (
    <div className={`message ${role}`}>
      <div className="avatar">{isUser ? 'You' : 'AAU'}</div>
      <div className="bubble-wrap">
        <div className="bubble">
          {isUser ? content : <ReactMarkdown>{content}</ReactMarkdown>}
        </div>
        {!isUser && sources && sources.length > 0 && (
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
