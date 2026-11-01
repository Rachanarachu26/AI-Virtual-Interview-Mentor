// Small formatting / color helpers used across pages.

export function scoreColor(score) {
  const s = Number(score) || 0
  if (s >= 75) return '#34d399'
  if (s >= 55) return '#38bdf8'
  if (s >= 40) return '#fbbf24'
  return '#fb7185'
}

export function scoreLabel(score) {
  const s = Number(score) || 0
  if (s >= 85) return 'Excellent'
  if (s >= 70) return 'Strong'
  if (s >= 55) return 'Good'
  if (s >= 40) return 'Fair'
  return 'Needs Work'
}

export function difficultyClass(difficulty) {
  const d = (difficulty || '').toLowerCase()
  if (d === 'easy') return 'badge-easy'
  if (d === 'medium') return 'badge-medium'
  if (d === 'hard') return 'badge-hard'
  return ''
}

export function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

export function initials(name) {
  if (!name) return '?'
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')
}

export function asArray(v) {
  if (Array.isArray(v)) return v
  if (v == null) return []
  return [v]
}
