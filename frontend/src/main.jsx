import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// StrictMode is intentionally omitted: its dev-only double mount/unmount
// re-triggers getUserMedia and speech synthesis on the Live Interview page.
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
