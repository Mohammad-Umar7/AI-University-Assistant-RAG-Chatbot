const QUESTIONS = [
  'What programs does AAU offer?',
  'What are the admission requirements?',
  'What are the tuition fees?',
  'When does the semester start?',
  'What is the grading system?',
  'Does AAU offer scholarships?',
  'How do I register for courses?',
  'What is the attendance policy?',
  'How can I contact AAU?',
  'What are international student requirements?',
]

export default function SuggestedQuestions({ onSelect, disabled }) {
  return (
    <div className="suggestions">
      {QUESTIONS.map(q => (
        <button
          key={q}
          className="chip"
          onClick={() => onSelect(q)}
          disabled={disabled}
        >
          {q}
        </button>
      ))}
    </div>
  )
}
