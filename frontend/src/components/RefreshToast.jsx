import './RefreshToast.css'

function RefreshToast({ message, current, total, isVisible, onClose }) {
  if (!isVisible) return null

  const percentage = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="refresh-toast">
      <div className="refresh-toast-content">
        <div className="refresh-toast-header">
          <span className="refresh-toast-title">Rafraîchissement en cours...</span>
          <button 
            className="refresh-toast-close"
            onClick={onClose}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>
        <div className="refresh-toast-message">
          {message || (total > 0 ? `${current}/${total} appartements récupérés` : 'Connexion...')}
        </div>
        {total > 0 && (
          <div className="refresh-toast-progress">
            <div 
              className="refresh-toast-progress-bar"
              style={{ width: `${percentage}%` }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default RefreshToast
