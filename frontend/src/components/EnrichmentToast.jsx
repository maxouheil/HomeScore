import './EnrichmentToast.css'

function EnrichmentToast({ current, total, isVisible, onClose }) {
  if (!isVisible) return null

  const percentage = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="enrichment-toast">
      <div className="enrichment-toast-content">
        <div className="enrichment-toast-header">
          <span className="enrichment-toast-title">Enrichissement en cours...</span>
          <button 
            className="enrichment-toast-close"
            onClick={onClose}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>
        <div className="enrichment-toast-message">
          Enrichissement appartement {current}/{total}
        </div>
        <div className="enrichment-toast-progress">
          <div 
            className="enrichment-toast-progress-bar"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  )
}

export default EnrichmentToast
