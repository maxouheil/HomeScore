import { useState, useEffect } from 'react'
import ApartmentCard from './ApartmentCard'
import './AlertResults.css'

function AlertResults({ alertId, alert }) {
  const [apartments, setApartments] = useState([])
  const [alertData, setAlertData] = useState(alert || null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fadeOut, setFadeOut] = useState(false)
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    if (alertId || alert) {
      setShowContent(false)
      loadAlertAndResults()
    }
  }, [alertId, alert])

  const loadAlertAndResults = async () => {
    try {
      // Fade out avant de charger
      setFadeOut(true)
      await new Promise(resolve => setTimeout(resolve, 150)) // Petit délai pour le fade-out
      
      setLoading(true)
      setError(null)
      setFadeOut(false)
      const id = alertId || alert?.id
      if (!id) {
        throw new Error('ID d\'alerte manquant')
      }

      // Charger l'alerte pour avoir les critères
      let currentAlert = alert
      if (!currentAlert) {
        const alertResponse = await fetch(`/api/alerts/${id}`)
        if (alertResponse.ok) {
          currentAlert = await alertResponse.json()
          setAlertData(currentAlert)
        }
      } else {
        setAlertData(currentAlert)
      }

      // Charger les appartements
      const response = await fetch(`/api/alerts/${id}/apartments`)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors du chargement des résultats' }))
        throw new Error(errorData.detail || `Erreur HTTP ${response.status}`)
      }
      const data = await response.json()
      // Trier par score décroissant (du plus haut au plus bas)
      // S'assurer que les scores sont des nombres
      const sorted = (data || []).sort((a, b) => {
        const scoreA = Number(a.alert_score) || 0
        const scoreB = Number(b.alert_score) || 0
        // Si les scores sont égaux, garder l'ordre original (stable sort)
        if (scoreB === scoreA) {
          return 0
        }
        return scoreB - scoreA // Décroissant : plus grand score en premier
      })
      console.log('Appartements triés par alert_score:', sorted.map(apt => ({
        id: apt.id,
        prix: apt.prix,
        alert_score: apt.alert_score,
        alert_criteria_scores: apt.alert_criteria_scores,
        // DEBUG: Vérifier les scores individuels
        criteria_scores_debug: apt.alert_criteria_scores ? Object.keys(apt.alert_criteria_scores).map(k => ({
          critere: k,
          score: apt.alert_criteria_scores[k]?.score
        })) : null
      })))
      setApartments(sorted)
      setError(null)
    } catch (err) {
      console.error('Erreur lors du chargement des résultats:', err)
      setError(err.message || 'Erreur lors du chargement des résultats')
    } finally {
      // Fade out du loader avant d'afficher le contenu
      setLoading(false)
      // Petit délai pour la transition fade-out du loader
      setTimeout(() => {
        setShowContent(true)
      }, 200)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    )
  }

  if (!showContent && !error && apartments.length > 0) {
    return (
      <div className="loading-container loading-fade-out">
        <div className="spinner"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error">
        <p>Erreur: {error}</p>
        <p style={{ fontSize: '12px', marginTop: '10px' }}>
          Assurez-vous que le serveur backend est démarré sur le port 8000
        </p>
      </div>
    )
  }

  if (apartments.length === 0) {
    return (
      <div className="empty-results" style={{ opacity: fadeOut ? 0 : 1, transition: 'opacity 0.3s ease-in-out' }}>
        <p>Aucun appartement ne correspond aux critères de cette alerte.</p>
      </div>
    )
  }

  return (
    <div className={`apartments-grid ${fadeOut ? 'fade-out' : ''}`}>
      {apartments.map((apartment, index) => (
        <div 
          key={apartment.id} 
          className="apartment-card-wrapper"
          style={{ animationDelay: `${index * 0.1}s` }}
        >
          <ApartmentCard apartment={apartment} alertCriteria={alertData?.criteria} />
        </div>
      ))}
    </div>
  )
}

export default AlertResults



