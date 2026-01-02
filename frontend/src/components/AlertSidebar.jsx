import { useState, useEffect } from 'react'
import './AlertSidebar.css'

const CRITERIA_ICONS = {
  'haussmanien': '🔑',
  'quartier': '📍',
  'prix': '💰',
  'luminosite': '☀️',
  'cuisine_ouverte': '👨‍🍳',
  'ascenseur': '🛗',
  'large_piece_vie': '🛋️',
  'hauteur_plafond': '📏',
  'renove': '🔨',
  'neuf': '✨'
}

function AlertSidebar({ isOpen, onClose, onSelectAlert, selectedAlertId, totalApartments = 0, onShowAllApartments }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isClosing, setIsClosing] = useState(false)
  const [apartmentCounts, setApartmentCounts] = useState({}) // { alertId: count }

  useEffect(() => {
    if (isOpen) {
      setIsClosing(false)
      loadAlerts()
    } else {
      setIsClosing(true)
      const timer = setTimeout(() => {
        setIsClosing(false)
      }, 300) // Durée de l'animation
      return () => clearTimeout(timer)
    }
  }, [isOpen])

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
      
      // Charger le nombre d'appartements pour chaque alerte
      loadApartmentCounts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadApartmentCounts = async (alertsList) => {
    const counts = {}
    
    // Charger les comptes en parallèle (utiliser l'endpoint léger sans scoring)
    const promises = alertsList.map(async (alert) => {
      try {
        const response = await fetch(`/api/alerts/${alert.id}/apartments/count`)
        if (response.ok) {
          const data = await response.json()
          counts[alert.id] = data.count || 0
        } else {
          counts[alert.id] = 0
        }
      } catch (err) {
        counts[alert.id] = 0
      }
    })
    
    await Promise.all(promises)
    setApartmentCounts(counts)
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

  const getCriteriaIcons = (criteria) => {
    // Support nouveau format (all) et ancien format (primary/secondary) pour compatibilité
    const allCriteria = criteria.all || [...(criteria.primary || []), ...(criteria.secondary || [])]
    return allCriteria.map(c => CRITERIA_ICONS[c] || '•').slice(0, 5)
  }

  const getLocationText = (alert) => {
    const quartiers = alert.filters?.localisation
    if (!quartiers) return 'Tous les quartiers'
    
    // Extraire les noms de quartiers (enlever "Métro " si présent)
    const quartierList = quartiers.split(',').map(q => {
      const trimmed = q.trim()
      if (trimmed.startsWith('Métro ')) {
        return trimmed.replace('Métro ', '')
      }
      return trimmed
    })
    
    // Limiter à 3 quartiers max pour l'affichage
    if (quartierList.length <= 3) {
      return quartierList.join(' • ')
    }
    return quartierList.slice(0, 2).join(' • ') + ' • ...'
  }

  if (!isOpen && !isClosing) return null

  return (
    <>
      {/* Overlay */}
      <div 
        className={`alert-sidebar-overlay ${isClosing ? 'closing' : ''}`} 
        onClick={(e) => {
          // Ne fermer que si on clique directement sur l'overlay, pas sur la sidebar
          if (e.target === e.currentTarget) {
            onClose()
          }
        }} 
      />
      
      {/* Sidebar */}
      <div 
        className={`alert-sidebar ${isClosing ? 'closing' : ''}`}
        onClick={(e) => {
          // Empêcher les clics sur la sidebar de fermer l'overlay
          e.stopPropagation()
        }}
      >
        {/* Header */}
        <div className="alert-sidebar-header">
          <h2>Alertes</h2>
          <button className="btn-close-sidebar" onClick={onClose} title="Fermer">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        
        {/* Navigation back to all apartments */}
        <div className="alert-sidebar-nav">
          <button
            className="alert-sidebar-nav-button"
            onClick={() => {
              if (onShowAllApartments) {
                onShowAllApartments()
              }
              onClose()
            }}
          >
            {totalApartments} appartement{totalApartments > 1 ? 's' : ''}
          </button>
        </div>
        
        {/* Liste des alertes */}
        <div className="alert-sidebar-content">
          {loading ? (
            <div className="alert-sidebar-loading">
              <div className="spinner"></div>
            </div>
          ) : error ? (
            <div className="alert-sidebar-error">Erreur: {error}</div>
          ) : alerts.length === 0 ? (
            <div className="alert-sidebar-empty">
              <p>Aucune alerte créée pour le moment.</p>
            </div>
          ) : (
            <div className="alert-sidebar-list">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`alert-sidebar-item ${selectedAlertId === alert.id ? 'selected' : ''}`}
                  onClick={(e) => {
                    // Ne pas déclencher si on clique sur le bouton de suppression
                    if (e.target.closest('.btn-delete-alert')) {
                      return
                    }
                    if (onSelectAlert) {
                      onSelectAlert(alert)
                    }
                  }}
                >
                  <div className="alert-sidebar-item-header">
                    <h3>{alert.name}</h3>
                    <button
                      className="btn-delete-alert"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(alert.id, e)
                      }}
                      title="Supprimer l'alerte"
                    >
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M2 4H4H14M5 4V2C5 1.73478 5.10536 1.48043 5.29289 1.29289C5.48043 1.10536 5.73478 1 6 1H10C10.2652 1 10.5196 1.10536 10.7071 1.29289C10.8946 1.48043 11 1.73478 11 2V4M13 4V14C13 14.2652 12.8946 14.5196 12.7071 14.7071C12.5196 14.8946 12.2652 15 12 15H4C3.73478 15 3.48043 14.8946 3.29289 14.7071C3.10536 14.5196 3 14.2652 3 14V4H13Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M6 7V11M10 7V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  </div>
                  <div className="alert-sidebar-item-location">
                    {getLocationText(alert)}
                  </div>
                  {apartmentCounts[alert.id] !== undefined && (
                    <div className="alert-sidebar-item-count">
                      {apartmentCounts[alert.id]} appartement{apartmentCounts[alert.id] > 1 ? 's' : ''}
                    </div>
                  )}
                  <div className="alert-sidebar-item-icons">
                    {getCriteriaIcons(alert.criteria || {}).map((icon, idx) => (
                      <span key={idx} className="alert-sidebar-icon">{icon}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default AlertSidebar

