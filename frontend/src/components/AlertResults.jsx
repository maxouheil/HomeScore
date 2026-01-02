import { useState, useEffect, useMemo, useCallback } from 'react'
import ApartmentCardSimplified from './ApartmentCardSimplified'
import Pagination from './Pagination'
import './AlertResults.css'

// Fonction helper pour vérifier si un appartement a des photos valides
// Utilise exactement la même logique que ApartmentCard.jsx
function hasValidPhotos(apartment) {
  if (!apartment || !apartment.photos) {
    return false
  }
  
  if (!Array.isArray(apartment.photos) || apartment.photos.length === 0) {
    return false
  }
  
  const apartmentId = apartment.id
  const photoUrls = []
  
  // Utiliser exactement la même logique que dans ApartmentCard.jsx
  apartment.photos.forEach(photo => {
    // Ignorer les valeurs null, undefined, ou vides
    if (!photo) return
    
    const url = typeof photo === 'string' ? photo : (photo.url || photo.local_path)
    
    // Vérifier que l'URL est valide et non vide (même logique que ApartmentCard)
    if (url && typeof url === 'string' && url.trim() !== '' && 
        !url.includes('logo') && !url.includes('Logo')) {
      // La conversion des URLs se fait dans ApartmentCard, ici on vérifie juste que l'URL existe
      photoUrls.push(url.trim())
    }
  })
  
  // Retourner true seulement si on a au moins une photo valide
  return photoUrls.length > 0
}

function AlertResults({ alertId, alert, sortBy = 'score' }) {
  const [apartmentsRaw, setApartmentsRaw] = useState([])
  const [alertData, setAlertData] = useState(alert || null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [fadeOut, setFadeOut] = useState(false)
  const [showContent, setShowContent] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 30

  const loadAlertAndResults = useCallback(async () => {
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
      // Stocker les données brutes, le tri sera fait par useMemo
      console.log('📦 Appartements chargés:', data.map(apt => ({
        id: apt.id,
        prix: apt.prix,
        alert_score: apt.alert_score,
        alert_tier: apt.alert_tier,
        has_alert_criteria_scores: !!apt.alert_criteria_scores,
        date_creation_annonce: apt.date_creation_annonce
      })))
      console.log('📋 AlertData chargé:', {
        id: currentAlert?.id,
        name: currentAlert?.name,
        has_criteria: !!currentAlert?.criteria,
        criteria: currentAlert?.criteria
      })
      setApartmentsRaw(data || [])
      setError(null)
      setHasLoaded(true)
    } catch (err) {
      console.error('Erreur lors du chargement des résultats:', err)
      setError(err.message || 'Erreur lors du chargement des résultats')
      setHasLoaded(false)
    } finally {
      // Fade out du loader avant d'afficher le contenu
      setLoading(false)
      // Petit délai pour la transition fade-out du loader
      setTimeout(() => {
        setShowContent(true)
      }, 200)
    }
  }, [alertId, alert])

  // Charger automatiquement les appartements quand l'alerte change
  useEffect(() => {
    if (alertId || alert) {
      const id = alertId || alert?.id
      if (id) {
        // Réinitialiser l'état
        setHasLoaded(false)
        setApartmentsRaw([])
        setShowContent(false)
        setError(null)
        // Charger automatiquement les appartements
        loadAlertAndResults()
      }
    }
  }, [alertId, alert, loadAlertAndResults])

  // Trier les appartements selon le type de tri sélectionné
  const apartments = useMemo(() => {
    if (apartmentsRaw.length === 0) return []
    
    // Filtrer les appartements sans photos
    const apartmentsWithPhotos = apartmentsRaw.filter(apartment => hasValidPhotos(apartment))
    
    return [...apartmentsWithPhotos].sort((a, b) => {
      if (sortBy === 'date') {
        // Trier par date de publication (plus récent en premier)
        const dateA = a.date_creation_annonce || a.scraped_at || ''
        const dateB = b.date_creation_annonce || b.scraped_at || ''
        
        // Si les deux dates sont vides, garder l'ordre original
        if (!dateA && !dateB) return 0
        
        // Les appartements sans date vont à la fin
        if (!dateA) return 1
        if (!dateB) return -1
        
        // Parser les dates et comparer
        const parsedDateA = new Date(dateA)
        const parsedDateB = new Date(dateB)
        
        // Si une date est invalide, la mettre à la fin
        if (isNaN(parsedDateA.getTime()) && isNaN(parsedDateB.getTime())) return 0
        if (isNaN(parsedDateA.getTime())) return 1
        if (isNaN(parsedDateB.getTime())) return -1
        
        // Plus récent en premier (ordre décroissant)
        return parsedDateB.getTime() - parsedDateA.getTime()
      } else {
        // Trier par score décroissant (du plus haut au plus bas)
        const scoreA = Number(a.alert_score) || 0
        const scoreB = Number(b.alert_score) || 0
        if (scoreB === scoreA) {
          return 0
        }
        return scoreB - scoreA // Décroissant : plus grand score en premier
      }
    })
  }, [apartmentsRaw, sortBy])

  // Calculer la pagination
  const totalPages = Math.ceil(apartments.length / itemsPerPage)
  const paginatedApartments = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return apartments.slice(startIndex, endIndex)
  }, [apartments, currentPage, itemsPerPage])

  // Réinitialiser à la page 1 quand l'alerte ou le tri change
  useEffect(() => {
    setCurrentPage(1)
  }, [alertId, alert?.id, sortBy, apartmentsRaw.length])

  // Faire défiler vers le haut quand la page change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [currentPage])

  const handleRefresh = useCallback(async () => {
    const id = alertId || alert?.id
    if (!id) {
      setError('ID d\'alerte manquant')
      return
    }

    try {
      setIsRefreshing(true)
      setRefreshMessage(null)
      setError(null)

      const response = await fetch(`/api/alerts/${id}/refresh`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors du rafraîchissement' }))
        throw new Error(errorData.detail || `Erreur HTTP ${response.status}`)
      }

      const data = await response.json()
      setRefreshMessage(data.message || `${data.new_count} nouveaux appartements ajoutés, ${data.photos_downloaded} photos téléchargées`)
      
      // Recharger les appartements après le refresh
      await loadAlertAndResults()
      
      // Effacer le message après 5 secondes
      setTimeout(() => {
        setRefreshMessage(null)
      }, 5000)
    } catch (err) {
      console.error('Erreur lors du rafraîchissement:', err)
      setError(err.message || 'Erreur lors du rafraîchissement')
    } finally {
      setIsRefreshing(false)
    }
  }, [alertId, alert, loadAlertAndResults])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p style={{ marginTop: '20px', fontSize: '16px' }}>
          Analyse des appartements en cours...
        </p>
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
        <button
          onClick={loadAlertAndResults}
          style={{
            marginTop: '20px',
            padding: '10px 20px',
            fontSize: '14px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Réessayer
        </button>
      </div>
    )
  }

  if (apartments.length === 0 && hasLoaded) {
    return (
      <div className="empty-results" style={{ opacity: fadeOut ? 0 : 1, transition: 'opacity 0.3s ease-in-out' }}>
        <p>Aucun appartement ne correspond aux critères de cette alerte.</p>
        <button
          onClick={loadAlertAndResults}
          style={{
            marginTop: '20px',
            padding: '10px 20px',
            fontSize: '14px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🔄 Rafraîchir
        </button>
      </div>
    )
  }

  return (
    <div>
      {/* Titre avec le nombre d'appartements et bouton refresh */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2 className="alert-results-count-title" style={{ margin: 0 }}>
          {apartments.length} appartement{apartments.length > 1 ? 's' : ''} dans les critères
        </h2>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            backgroundColor: isRefreshing ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: isRefreshing ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'background-color 0.2s'
          }}
          title="Rafraîchir les appartements depuis l'API Jinka"
        >
          {isRefreshing ? (
            <>
              <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
              <span>Rafraîchissement...</span>
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 1V3M8 13V15M3 8H1M15 8H13M12.364 3.636L10.95 5.05M5.05 10.95L3.636 12.364M12.364 12.364L10.95 10.95M5.05 5.05L3.636 3.636" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M8 12C10.2091 12 12 10.2091 12 8C12 5.79086 10.2091 4 8 4C5.79086 4 4 5.79086 4 8C4 10.2091 5.79086 12 8 12Z" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
              <span>Rafraîchir</span>
            </>
          )}
        </button>
      </div>
      {/* Message de succès du refresh */}
      {refreshMessage && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#d4edda',
          color: '#155724',
          borderRadius: '6px',
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          ✅ {refreshMessage}
        </div>
      )}
      {/* Grille des appartements */}
      <div className={`apartments-grid ${fadeOut ? 'fade-out' : ''}`}>
        {paginatedApartments.map((apartment, index) => (
          <div 
            key={apartment.id} 
            className="apartment-card-wrapper"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <ApartmentCardSimplified 
              apartment={apartment} 
              alertCriteria={alertData?.criteria}
              key={`card-${apartment.id}`}
            />
          </div>
        ))}
      </div>
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  )
}

export default AlertResults



