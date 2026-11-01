import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  {
    icon: '🧠',
    title: 'Dynamic AI Questions',
    desc: 'Gemini generates every question live from your resume, role, difficulty and your previous answers — never a fixed list.',
  },
  {
    icon: '🔊',
    title: 'Voice Interviewer',
    desc: 'The AI interviewer speaks each question aloud, then listens as you answer through your microphone.',
  },
  {
    icon: '🎥',
    title: 'Body-Language Analysis',
    desc: 'Computer vision reads eye contact, posture and gestures to score your non-verbal presence.',
  },
  {
    icon: '📝',
    title: 'Speech Insights',
    desc: 'Whisper transcribes your answers and measures pace, filler words and clarity.',
  },
  {
    icon: '📊',
    title: 'Detailed Scorecards',
    desc: 'A weighted engine blends answer quality, communication and body language into one clear score.',
  },
  {
    icon: '🚀',
    title: 'Personalized Coaching',
    desc: 'Get strengths, weaknesses and targeted practice suggestions after every session.',
  },
]

export default function Landing() {
  const { user } = useAuth()
  const startTo = user ? '/dashboard' : '/register'

  return (
    <div className="container">
      <section className="hero">
        <span className="pill-top">✨ Practice interviews with a real AI interviewer</span>
        <h1>
          Ace your next interview with your <br />
          <span className="gradient-text">AI Virtual Mentor</span>
        </h1>
        <p>
          Upload your resume, pick a role and difficulty, and sit through a realistic
          spoken interview. Get instant, personalized feedback on what you said, how you
          said it, and how you showed up on camera.
        </p>
        <div className="hero-cta">
          <Link to={startTo} className="btn btn-primary btn-lg">
            {user ? 'Go to Dashboard' : 'Start Practicing Free'} →
          </Link>
          <a href="#features" className="btn btn-ghost btn-lg">
            See how it works
          </a>
        </div>
      </section>

      <section id="features" className="feature-grid">
        {FEATURES.map((f) => (
          <div key={f.title} className="feature">
            <div className="fi">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>

      <section className="card card-pad mt-32 center" style={{ marginTop: 70 }}>
        <h2 className="section-title">Ready to feel prepared?</h2>
        <p className="muted mt-8">
          Join now and run your first AI-powered mock interview in minutes.
        </p>
        <div className="hero-cta" style={{ marginTop: 22 }}>
          <Link to={startTo} className="btn btn-primary btn-lg">
            {user ? 'Open Dashboard' : 'Create your account'}
          </Link>
        </div>
      </section>
    </div>
  )
}
