const TOPICS = [
  { icon: '📚', label: 'Programs & Colleges', question: 'What colleges and programs does Al Ain University offer?' },
  { icon: '🎓', label: 'Admissions', question: 'What are the admission requirements for Al Ain University?' },
  { icon: '💰', label: 'Tuition & Fees', question: 'What are the tuition fees at Al Ain University?' },
  { icon: '📅', label: 'Academic Calendar', question: 'What is the academic calendar for 2025/2026 at AAU?' },
  { icon: '📝', label: 'Course Registration', question: 'How do I register for courses at AAU and what is the add/drop policy?' },
  { icon: '📊', label: 'Grading System', question: 'What is the grading system and GPA scale at Al Ain University?' },
  { icon: '🏫', label: 'Campus & Facilities', question: 'What facilities and services does AAU have on campus?' },
  { icon: '🌍', label: 'International Students', question: 'What are the requirements and visa process for international students at AAU?' },
  { icon: '🎯', label: 'Scholarships', question: 'What scholarships and financial aid does AAU offer?' },
  { icon: '📋', label: 'Academic Policies', question: 'What are the attendance policy, probation rules, and makeup exam policy at AAU?' },
  { icon: '📞', label: 'Contact AAU', question: 'How can I contact Al Ain University? What are the phone numbers and addresses?' },
]

export default function Sidebar({ isOpen, onClose, onTopicClick }) {
  return (
    <aside className={`sidebar${isOpen ? ' sidebar--open' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">AAU</div>
        <div className="sidebar-title">AAU AI Assistant</div>
        <div className="sidebar-subtitle">Al Ain University</div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-label">Quick Topics</div>
        {TOPICS.map((t) => (
          <button
            key={t.label}
            className="topic-btn"
            onClick={() => {
              onTopicClick(t.question)
              if (window.innerWidth <= 768) onClose()
            }}
          >
            <span className="topic-icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      <div className="sidebar-footer">Powered by Groq & ChromaDB</div>
    </aside>
  )
}
