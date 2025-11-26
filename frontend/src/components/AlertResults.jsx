import { useState, useEffect } from 'react'
import ApartmentCard from './ApartmentCard'
import './AlertResults.css'

function AlertResults({ alertId, alert, onBack }) {
  const [apartments, setApartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (alertId || alert) {
      loadResults()
    }
  }, [alertId, alert])

  const loadResults = async () => {
    try {
      setLoading(true)
      const id = alertId || alert?.id
      if (!id) {
        throw new Error('ID d\'alerte manquant')
      }

      const response = await fetch(`/api/alerts/${id}/apartments`)
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des résultats')
      }
      const data = await response.json()
      setApartments(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatScore = (score) => {
    return score ? score.toFixed(1) : '0'
  }

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981' // Vert
    if (score >= 60) return '#f59e0b' // Orange
    return '#ef4444' // Rouge
  }

  if (loading) {
    return (
      <div className="alert-results">
        <div className="loading">Chargement des résultats...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert-results">
        <div className="error">Erreur: {error}</div>
        {onBack && (
          <button className="btn-back" onClick={onBack}>
            ← Retour
          </button>
        )}
      </div>
    )
  }

  const alertData = alert || {}

  return (
    <div className="alert-results">
      <div className="alert-results-header">
        <div>
          <h2>{alertData.name || 'Résultats de l\'alerte'}</h2>
          <p className="results-count">
            {apartments.length} appartement{apartments.length !== 1 ? 's' : ''} trouvé{apartments.length !== 1 ? 's' : ''}
          </p>
        </div>
        {onBack && (
          <button className="btn-back" onClick={onBack}>
            ← Retour
          </button>
        )}
      </div>

      {apartments.length === 0 ? (
        <div className="empty-results">
          <p>Aucun appartement ne correspond aux critères de cette alerte.</p>
          <p className="empty-hint">
            Essayez d'élargir vos filtres (budget, surface, pièces) ou modifiez les critères de l'alerte.
          </p>
        </div>
      ) : (
        <>
          <div className="alert-summary">
            <div className="summary-item">
              <strong>Budget:</strong> {alertData.filters?.budget_min?.toLocaleString('fr-FR')}€ - {alertData.filters?.budget_max?.toLocaleString('fr-FR')}€
            </div>
            <div className="summary-item">
              <strong>Surface:</strong> {alertData.filters?.surface_min}m² - {alertData.filters?.surface_max}m²
            </div>
            <div className="summary-item">
              <strong>Pièces:</strong> {alertData.filters?.pieces_min} - {alertData.filters?.pieces_max}
            </div>
            {alertData.filters?.localisation && (
              <div className="summary-item">
                <strong>Localisation:</strong> {alertData.filters.localisation}
              </div>
            )}
          </div>

          <div className="apartments-grid">
            {apartments.map((apartment) => {
              const alertScore = apartment.alert_score || 0
              const scoreColor = getScoreColor(alertScore)
              
              return (
                <div key={apartment.id} className="apartment-wrapper">
                  <div className="alert-score-badge" style={{ backgroundColor: scoreColor }}>
                    Score alerte: {formatScore(alertScore)}/100
                  </div>
                  <ApartmentCard apartment={apartment} />
                  {apartment.alert_criteria_scores && (
                    <div className="criteria-scores">
                      <h4>Détail des critères:</h4>
                      <div className="criteria-scores-grid">
                        {Object.entries(apartment.alert_criteria_scores).map(([criterion, scoreData]) => (
                          <div key={criterion} className="criterion-score-item">
                            <span className="criterion-name">{criterion}:</span>
                            <span className="criterion-score">{formatScore(scoreData.score)}pts</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

export default AlertResults



