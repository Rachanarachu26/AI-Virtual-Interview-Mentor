import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiError } from '../services/api'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await register(form.full_name, form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(apiError(err, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <h1 className="section-title">Create your account</h1>
        <p className="muted mb-24">Start practicing smarter interviews today.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={onSubmit}>
          <div className="field">
            <label className="label">Full Name</label>
            <input
              className="input"
              name="full_name"
              value={form.full_name}
              onChange={onChange}
              placeholder="Jane Doe"
              required
            />
          </div>
          <div className="field">
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              name="email"
              value={form.email}
              onChange={onChange}
              placeholder="you@example.com"
              required
            />
          </div>
          <div className="field">
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              name="password"
              value={form.password}
              onChange={onChange}
              placeholder="At least 6 characters"
              required
            />
          </div>
          <div className="field">
            <label className="label">Confirm Password</label>
            <input
              className="input"
              type="password"
              name="confirm"
              value={form.confirm}
              onChange={onChange}
              placeholder="Re-enter password"
              required
            />
          </div>
          <button className="btn btn-primary btn-block btn-lg mt-8" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Create Account'}
          </button>
        </form>

        <p className="muted center mt-24" style={{ fontSize: '0.9rem' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--primary-2)', fontWeight: 600 }}>
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
