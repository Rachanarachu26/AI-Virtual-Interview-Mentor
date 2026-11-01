import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { initials } from '../utils/format'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const handleLogout = () => {
    setMenuOpen(false)
    logout()
    navigate('/')
  }

  // Close the dropdown on outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    const onKey = (e) => {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen])

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to={user ? '/dashboard' : '/'} className="brand">
          <span className="brand-badge">🎙️</span>
          <span>
            Interview<span style={{ color: 'var(--primary-2)' }}>Mentor</span>
          </span>
        </Link>

        {user ? (
          <div className="nav-user">
            <div className="nav-links">
              <NavLink to="/dashboard" className="nav-link">
                Dashboard
              </NavLink>
              <NavLink to="/interview/category" className="nav-link">
                New Interview
              </NavLink>
              <NavLink to="/history" className="nav-link">
                History
              </NavLink>
              <NavLink to="/resume" className="nav-link">
                Resume
              </NavLink>
            </div>

            <div className="user-menu" ref={menuRef}>
              <button
                type="button"
                className="avatar avatar-btn"
                title={user.full_name}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((o) => !o)}
              >
                {initials(user.full_name)}
              </button>

              {menuOpen && (
                <div className="user-dropdown" role="menu">
                  <div className="user-dropdown-header">
                    <div className="avatar avatar-lg">{initials(user.full_name)}</div>
                    <div className="user-dropdown-id">
                      <div className="user-dropdown-name">{user.full_name}</div>
                      {user.email && (
                        <div className="user-dropdown-email">{user.email}</div>
                      )}
                    </div>
                  </div>

                  <div className="user-dropdown-divider" />

                  <button
                    className="user-dropdown-item"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false)
                      navigate('/dashboard')
                    }}
                  >
                    <span className="user-dropdown-ico">📊</span> Dashboard
                  </button>
                  <button
                    className="user-dropdown-item"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false)
                      navigate('/profile')
                    }}
                  >
                    <span className="user-dropdown-ico">📄</span> My Resume
                  </button>

                  <div className="user-dropdown-divider" />

                  <button
                    className="user-dropdown-item user-dropdown-danger"
                    role="menuitem"
                    onClick={handleLogout}
                  >
                    <span className="user-dropdown-ico">↩</span> Log out
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="nav-links">
            <NavLink to="/login" className="nav-link">
              Login
            </NavLink>
            <Link to="/register" className="btn btn-primary btn-sm">
              Get Started
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
