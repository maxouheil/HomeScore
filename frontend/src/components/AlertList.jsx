import { useState, useEffect } from 'react'
import './AlertList.css'

function AlertList({ onSelectAlert, onCreateNew }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/alerts')
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des alertes')
      }
      const data = await response.json()
      setAlerts(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (alertId, e) => {
    e.stopPropagation()
    
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette alerte ?')) {
      return
    }

    try {
      const response = await fetch(`/api/alerts/${alertId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression')
      }

      // Recharger la liste
      loadAlerts()
    } catch (err) {
      alert('Erreur lors de la suppression: ' + err.message)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Date inconnue'
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getCriteriaNames = (criteria) => {
    const allCriteria = [...(criteria.primary || []), ...(criteria.secondary || [])]
    return allCriteria.join(', ')
  }

  if (loading) {
    return (
      <div className="alert-list">
        <div className="loading">Chargement des alertes...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert-list">
        <div className="error">Erreur: {error}</div>
      </div>
    )
  }

  return (
    <div className="alert-list">
      <div className="alert-list-header">
        <h2>Mes alertes</h2>
        {onCreateNew && (
          <button className="btn-create" onClick={onCreateNew}>
            + Créer une alerte
          </button>
        )}
      </div>

      {alerts.length === 0 ? (
        <div className="empty-state">
          <p>Aucune alerte créée pour le moment.</p>
          {onCreateNew && (
            <button className="btn-create" onClick={onCreateNew}>
              Créer ma première alerte
            </button>
          )}
        </div>
      ) : (
        <div className="alerts-grid">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="alert-card"
              onClick={() => onSelectAlert && onSelectAlert(alert)}
            >
              <div className="alert-card-header">
                <h3>{alert.name}</h3>
                <button
                  className="btn-delete"
                  onClick={(e) => handleDelete(alert.id, e)}
                  title="Supprimer l'alerte"
                >
                  ×
                </button>
              </div>

              <div className="alert-card-body">
                <div className="alert-info">
                  <div className="info-item">
                    <strong>Budget:</strong> {alert.filters?.budget_min?.toLocaleString('fr-FR')}€ - {alert.filters?.budget_max?.toLocaleString('fr-FR')}€
                  </div>
                  <div className="info-item">
                    <strong>Surface:</strong> {alert.filters?.surface_min}m² - {alert.filters?.surface_max}m²
                  </div>
                  <div className="info-item">
                    <strong>Pièces:</strong> {alert.filters?.pieces_min} - {alert.filters?.pieces_max}
                  </div>
                  {alert.filters?.localisation && (
                    <div className="info-item">
                      <strong>Localisation:</strong> {alert.filters.localisation}
                    </div>
                  )}
                </div>

                <div className="alert-criteria">
                  <div className="criteria-section">
                    <strong>Critères principaux (30pts):</strong>
                    <ul>
                      {alert.criteria?.primary?.map((criterion, idx) => (
                        <li key={idx}>{criterion}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="criteria-section">
                    <strong>Critère secondaire (10pts):</strong>
                    <ul>
                      {alert.criteria?.secondary?.map((criterion, idx) => (
                        <li key={idx}>{criterion}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="alert-card-footer">
                <span className="alert-date">Créée le {formatDate(alert.created_at)}</span>
                <button className="btn-view" onClick={(e) => {
                  e.stopPropagation()
                  onSelectAlert && onSelectAlert(alert)
                }}>
                  Voir les résultats →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default AlertList



