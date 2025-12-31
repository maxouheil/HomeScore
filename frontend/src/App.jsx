import { useEffect, useState, useMemo } from 'react'
import ApartmentCard from './components/ApartmentCard'
import AlertCreator from './components/AlertCreator'
import AlertResults from './components/AlertResults'
import AlertSidebar from './components/AlertSidebar'
import EnrichmentToast from './components/EnrichmentToast'
import RefreshToast from './components/RefreshToast'
import Pagination from './components/Pagination'
import { calculateMegaScore } from './utils/scoreUtils'
import './App.css'

function App() {
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isAlertCreatorOpen, setIsAlertCreatorOpen] = useState(false)
  const [isAlertSidebarOpen, setIsAlertSidebarOpen] = useState(false)
  const [editingAlert, setEditingAlert] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState(null)
  const [refreshProgress, setRefreshProgress] = useState({ current: 0, total: 0, message: '', visible: false })
  const [isEnriching, setIsEnriching] = useState(false)
  const [enrichMessage, setEnrichMessage] = useState(null)
  const [enrichmentProgress, setEnrichmentProgress] = useState({ current: 0, total: 0, visible: false })
  
  const [apartmentsRaw, setApartmentsRaw] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [sortBy, setSortBy] = useState('date') // 'score' ou 'date' - par défaut 'date' sur la home
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 30

  // Charger les données initiales au démarrage
  useEffect(() => {
    // Charger les données initiales
    const loadApartments = async () => {
      try {
        setLoading(true)
        // Désactiver l'enrichissement par défaut car c'est trop lent avec 1400+ appartements
        const response = await fetch('/api/apartments?enrich=false')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        // Stocker les données brutes, le tri sera fait par useMemo
        console.log(`📊 Nombre d'appartements chargés: ${data.length}`)
        setApartmentsRaw(data)
        setError(null)
      } catch (err) {
        console.error('Erreur lors du chargement des appartements:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    // Charger les statistiques
    const loadStats = async () => {
      try {
        const response = await fetch('/api/apartments/stats')
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        }
      } catch (err) {
        console.error('Erreur lors du chargement des statistiques:', err)
      }
    }

    // Par défaut, afficher la vue globale (tous les appartements) au lieu d'une alerte spécifique
    loadApartments()
    loadStats()
  }, [])

  // Trier les appartements selon le type de tri sélectionné
  const apartments = useMemo(() => {
    if (apartmentsRaw.length === 0) return []
    
    const sorted = [...apartmentsRaw].sort((a, b) => {
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
        // Pour les dates ISO (2025-12-31T11:41:02.000Z), new Date() fonctionne bien
        // Mais on peut aussi comparer directement les strings ISO pour plus de fiabilité
        let comparison = 0
        try {
          const parsedDateA = new Date(dateA)
          const parsedDateB = new Date(dateB)
          
          // Si une date est invalide, la mettre à la fin
          if (isNaN(parsedDateA.getTime()) && isNaN(parsedDateB.getTime())) return 0
          if (isNaN(parsedDateA.getTime())) return 1
          if (isNaN(parsedDateB.getTime())) return -1
          
          // Plus récent en premier (ordre décroissant)
          comparison = parsedDateB.getTime() - parsedDateA.getTime()
        } catch (e) {
          // En cas d'erreur de parsing, utiliser la comparaison de strings ISO (qui fonctionne pour les dates ISO)
          console.warn('Erreur parsing date, utilisation comparaison string:', e)
          comparison = dateB.localeCompare(dateA) // Ordre décroissant (B avant A)
        }
        
        return comparison
      } else {
        // Trier par mega score décroissant (du plus grand au plus petit)
        const scoreA = calculateMegaScore(a)
        const scoreB = calculateMegaScore(b)
        return scoreB - scoreA // Décroissant : plus grand score en premier
      }
    })
    
    // Log pour vérifier le tri par date
    if (sortBy === 'date' && sorted.length > 0) {
      const firstDate = sorted[0].date_creation_annonce || sorted[0].scraped_at || 'N/A'
      const lastDate = sorted[sorted.length - 1].date_creation_annonce || sorted[sorted.length - 1].scraped_at || 'N/A'
      const firstId = sorted[0].id || 'N/A'
      const lastId = sorted[sorted.length - 1].id || 'N/A'
      console.log(`📅 Tri par date: ${sorted.length} appartements - Plus récent: ${firstDate} (ID: ${firstId}), Plus ancien: ${lastDate} (ID: ${lastId})`)
      
      // Vérifier les 5 premiers pour diagnostiquer
      console.log('📅 Top 5 dates:', sorted.slice(0, 5).map(apt => ({
        id: apt.id,
        date: apt.date_creation_annonce || apt.scraped_at,
        parsed: new Date(apt.date_creation_annonce || apt.scraped_at).toISOString()
      })))
    }
    
    return sorted
  }, [apartmentsRaw, sortBy])

  // Calculer la pagination
  const totalPages = Math.ceil(apartments.length / itemsPerPage)
  const paginatedApartments = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return apartments.slice(startIndex, endIndex)
  }, [apartments, currentPage, itemsPerPage])

  // Réinitialiser à la page 1 quand le tri change
  useEffect(() => {
    setCurrentPage(1)
  }, [sortBy, apartmentsRaw.length])

  // Faire défiler vers le haut quand la page change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [currentPage])

  useEffect(() => {
    // WebSocket pour mises à jour en temps réel (optionnel - fonctionne même si backend non démarré)
    let ws = null
    let reconnectTimeout = null
    let isConnecting = false
    
    const connectWebSocket = () => {
      // Éviter les connexions multiples simultanées
      if (isConnecting || (ws && ws.readyState === WebSocket.CONNECTING)) {
        return
      }
      
      // Fermer la connexion précédente si elle existe
      if (ws) {
        try {
          ws.close()
        } catch (e) {
          // Ignorer les erreurs de fermeture
        }
      }
      
      isConnecting = true
      
      try {
        ws = new WebSocket('ws://localhost:8000/ws')
        
        ws.onopen = () => {
          isConnecting = false
          // Réinitialiser le délai de reconnexion en cas de succès
          if (reconnectTimeout) {
            clearTimeout(reconnectTimeout)
            reconnectTimeout = null
          }
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'apartments_updated') {
              // Recharger les données et les statistiques
              fetch('/api/apartments')
                .then(res => res.json())
                .then(data => setApartmentsRaw(data))
                .catch(console.error)
              fetch('/api/apartments/stats')
                .then(res => res.json())
                .then(data => setStats(data))
                .catch(console.error)
            }
          } catch (err) {
            // Ignorer les erreurs de parsing
          }
        }

        ws.onerror = () => {
          isConnecting = false
          // Ne rien faire - l'erreur sera gérée par onclose
        }

        ws.onclose = () => {
          isConnecting = false
          // Tenter de reconnecter après 5 secondes (uniquement si pas déjà en reconnexion)
          if (!reconnectTimeout) {
            reconnectTimeout = setTimeout(() => {
              reconnectTimeout = null
              connectWebSocket()
            }, 5000)
          }
        }
      } catch (err) {
        isConnecting = false
        // Erreur lors de la création du WebSocket - réessayer plus tard
        if (!reconnectTimeout) {
          reconnectTimeout = setTimeout(() => {
            reconnectTimeout = null
            connectWebSocket()
          }, 5000)
        }
      }
    }
    
    // Attendre un peu avant de tenter la première connexion WebSocket
    // pour éviter les erreurs immédiates si le backend n'est pas démarré
    const wsTimeout = setTimeout(() => {
      connectWebSocket()
    }, 1000)

    return () => {
      clearTimeout(wsTimeout)
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (ws) {
        try {
          ws.close()
        } catch (e) {
          // Ignorer les erreurs de fermeture
        }
      }
    }
  }, [])

  const handleCreateAlertSuccess = (createdAlert) => {
    setSelectedAlert(createdAlert)
    setEditingAlert(null)
  }

  const handleSelectAlert = (alert) => {
    setSelectedAlert(alert)
    // Changer le tri en 'score' quand une alerte est sélectionnée
    setSortBy('score')
    // Fermer la sidebar après sélection
    setIsAlertSidebarOpen(false)
  }

  // Changer le tri en 'date' quand aucune alerte n'est sélectionnée (retour à la home)
  useEffect(() => {
    if (!selectedAlert) {
      setSortBy('date')
    }
  }, [selectedAlert])

  const handleRefresh = async () => {
    try {
      console.log('🔄 Début du rafraîchissement...')
      setIsRefreshing(true)
      setRefreshMessage(null)
      setError(null)
      setRefreshProgress({ current: 0, total: 0, message: '', visible: true })

      // Utiliser l'endpoint SSE pour avoir la progression en temps réel
      const response = await fetch('/api/apartments/refresh/stream', {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'connecting') {
                setRefreshProgress({ current: 0, total: 0, message: data.message, visible: true })
              } else if (data.type === 'fetching_total') {
                setRefreshProgress({ current: 0, total: 0, message: data.message, visible: true })
              } else if (data.type === 'start') {
                setRefreshProgress({ current: 0, total: data.total, message: data.message || `Récupération de ${data.total} appartements...`, visible: true })
              } else if (data.type === 'progress') {
                setRefreshProgress({ 
                  current: data.current, 
                  total: data.total, 
                  message: data.message || `${data.current}/${data.total} appartements récupérés`,
                  visible: true 
                })
              } else if (data.type === 'processing') {
                setRefreshProgress(prev => ({ 
                  current: prev.current, 
                  total: prev.total, 
                  message: data.message || 'Traitement des données...',
                  visible: true 
                }))
              } else if (data.type === 'downloading_photos') {
                setRefreshProgress(prev => ({ 
                  current: prev.current, 
                  total: prev.total, 
                  message: data.message || 'Téléchargement des photos...',
                  visible: true 
                }))
              } else if (data.type === 'saving') {
                setRefreshProgress(prev => ({ 
                  current: prev.current, 
                  total: prev.total, 
                  message: data.message || 'Sauvegarde des données...',
                  visible: true 
                }))
              } else if (data.type === 'complete') {
                setRefreshProgress(prev => ({ 
                  current: data.total_count || prev.total, 
                  total: data.total_count || prev.total, 
                  message: data.message || `${data.new_count} nouveaux appartements ajoutés, ${data.photos_downloaded} photos téléchargées`,
                  visible: false 
                }))
                setRefreshMessage(data.message || `${data.new_count} nouveaux appartements ajoutés, ${data.photos_downloaded} photos téléchargées`)
                
                // Recharger les appartements après le refresh
                console.log('🔄 Rechargement des appartements...')
                const apartmentsResponse = await fetch('/api/apartments')
                if (apartmentsResponse.ok) {
                  const apartmentsData = await apartmentsResponse.json()
                  console.log(`📊 ${apartmentsData.length} appartements rechargés`)
                  setApartmentsRaw(apartmentsData)
                }
                
                // Effacer le message après 5 secondes
                setTimeout(() => {
                  setRefreshMessage(null)
                }, 5000)
              } else if (data.type === 'error') {
                setRefreshProgress({ current: 0, total: 0, message: '', visible: false })
                throw new Error(data.message || 'Erreur lors du rafraîchissement')
              }
            } catch (e) {
              console.error('Erreur parsing SSE:', e)
            }
          }
        }
      }
    } catch (err) {
      console.error('❌ Erreur lors du rafraîchissement:', err)
      setError(err.message || 'Erreur lors du rafraîchissement')
      setRefreshProgress({ current: 0, total: 0, message: '', visible: false })
      // Afficher l'erreur aussi dans un message temporaire
      setRefreshMessage(`Erreur: ${err.message}`)
      setTimeout(() => {
        setRefreshMessage(null)
      }, 5000)
    } finally {
      setIsRefreshing(false)
      console.log('🏁 Rafraîchissement terminé')
    }
  }

  const handleEnrich = async () => {
    try {
      setIsEnriching(true)
      setEnrichMessage(null)
      setError(null)
      setEnrichmentProgress({ current: 0, total: 0, visible: true })

      // Utiliser l'endpoint SSE pour avoir la progression en temps réel
      const response = await fetch('/api/apartments/enrich/stream?limit=5', {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error(`Erreur HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'start') {
                setEnrichmentProgress({ current: 0, total: data.total, visible: true })
              } else if (data.type === 'progress') {
                setEnrichmentProgress({ 
                  current: data.current, 
                  total: data.total, 
                  visible: true 
                })
              } else if (data.type === 'complete') {
                setEnrichmentProgress({ 
                  current: data.total, 
                  total: data.total, 
                  visible: false 
                })
                setEnrichMessage(data.message || `${data.enriched_count} appartement(s) enrichi(s)`)
                
                // Recharger les appartements après l'enrichissement
                const apartmentsResponse = await fetch('/api/apartments')
                if (apartmentsResponse.ok) {
                  const apartmentsData = await apartmentsResponse.json()
                  setApartmentsRaw(apartmentsData)
                }
                
                // Effacer le message après 5 secondes
                setTimeout(() => {
                  setEnrichMessage(null)
                }, 5000)
              } else if (data.type === 'error') {
                setEnrichmentProgress({ current: 0, total: 0, visible: false })
                throw new Error(data.message || 'Erreur lors de l\'enrichissement')
              }
            } catch (e) {
              console.error('Erreur parsing SSE:', e)
            }
          }
        }
      }
    } catch (err) {
      console.error('Erreur lors de l\'enrichissement:', err)
      setError(err.message || 'Erreur lors de l\'enrichissement')
      setEnrichmentProgress({ current: 0, total: 0, visible: false })
    } finally {
      setIsEnriching(false)
    }
  }

  // Navigation
  const renderNavigation = () => {
    const totalApartments = apartmentsRaw.length
    
    return (
      <nav className="main-navigation">
        <div className="nav-left">
          <button
            className="nav-button-burger"
            onClick={() => setIsAlertSidebarOpen(!isAlertSidebarOpen)}
            aria-label="Toggle sidebar"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <h2 className="nav-title">
            {selectedAlert ? selectedAlert.name : `${totalApartments} appartement${totalApartments > 1 ? 's' : ''}`}
          </h2>
        </div>
        <div className="nav-right">
          {/* Toggle Score/Date - visible uniquement quand une alerte est sélectionnée */}
          {selectedAlert && (
            <div className="sort-toggle">
              <button
                className={`sort-toggle-button ${sortBy === 'score' ? 'active' : ''}`}
                onClick={() => setSortBy('score')}
                title="Trier par score"
              >
                Score
              </button>
              <button
                className={`sort-toggle-button ${sortBy === 'date' ? 'active' : ''}`}
                onClick={() => setSortBy('date')}
                title="Trier par date de publication"
              >
                Date
              </button>
            </div>
          )}
          <button
            className="nav-button nav-button-enrich"
            onClick={handleEnrich}
            disabled={isEnriching}
            title="Enrichir les données des appartements sans données enrichies"
          >
            {isEnriching ? (
              <>
                <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px', margin: 0 }}></div>
                <span>Enrichissement...</span>
              </>
            ) : (
              <span>Enrichir</span>
            )}
          </button>
          <button
            className="nav-button nav-button-refresh"
            onClick={handleRefresh}
            disabled={isRefreshing}
            title="Rafraîchir les appartements depuis l'API Jinka"
          >
            {isRefreshing ? (
              <>
                <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px', margin: 0 }}></div>
                <span>Rafraîchissement...</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 2.66667V5.33333M8 10.6667V13.3333M4 8H1.33333M14.6667 8H12M13.3333 4L11.3333 6M4.66667 10L2.66667 12M13.3333 12L11.3333 10M4.66667 6L2.66667 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M8 12C10.2091 12 12 10.2091 12 8C12 5.79086 10.2091 4 8 4C5.79086 4 4 5.79086 4 8C4 10.2091 5.79086 12 8 12Z" stroke="currentColor" strokeWidth="1.5"/>
                </svg>
                <span>Rafraîchir</span>
              </>
            )}
          </button>
          <button
            className="nav-button nav-button-create-alert"
            onClick={() => setIsAlertCreatorOpen(true)}
          >
            Créer une alerte
          </button>
        </div>
      </nav>
    )
  }

  // Rendu du contenu - afficher les résultats d'alerte si une alerte est sélectionnée, sinon tous les appartements
  const renderContent = () => {
    // Si une alerte est sélectionnée, afficher les résultats de l'alerte
    if (selectedAlert) {
      return (
        <AlertResults 
          alertId={selectedAlert.id} 
          alert={selectedAlert} 
          sortBy={sortBy}
        />
      )
    }

    // Sinon, afficher tous les appartements
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <p>Chargement des appartements...</p>
        </div>
      )
    }

    if (error) {
      return (
        <div style={{ textAlign: 'center', padding: '50px', color: '#F85457' }}>
          <p>Erreur: {error}</p>
          <p style={{ fontSize: '12px', marginTop: '10px' }}>
            Assurez-vous que le serveur backend est démarré sur le port 8000
          </p>
        </div>
      )
    }

    return (
      <div className="all-apartments-view">
        {/* Message de succès de l'enrichissement */}
        {enrichMessage && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#d4edda',
            color: '#155724',
            borderRadius: '6px',
            marginBottom: '20px',
            border: '1px solid #c3e6cb'
          }}>
            ✅ {enrichMessage}
          </div>
        )}
        <div className="apartments-grid">
          {paginatedApartments.map(apartment => (
            <ApartmentCard key={apartment.id} apartment={apartment} showScore={false} />
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

  return (
    <div className="container">
      {renderNavigation()}
      <EnrichmentToast
        current={enrichmentProgress.current}
        total={enrichmentProgress.total}
        isVisible={enrichmentProgress.visible}
        onClose={() => setEnrichmentProgress({ current: 0, total: 0, visible: false })}
      />
      <RefreshToast
        message={refreshProgress.message}
        current={refreshProgress.current}
        total={refreshProgress.total}
        isVisible={refreshProgress.visible}
        onClose={() => setRefreshProgress({ current: 0, total: 0, message: '', visible: false })}
      />
      <div className="main-content-wrapper">
        {/* Sidebar des alertes */}
        <AlertSidebar
          isOpen={isAlertSidebarOpen}
          onClose={() => setIsAlertSidebarOpen(false)}
          onSelectAlert={handleSelectAlert}
          selectedAlertId={selectedAlert?.id}
          totalApartments={apartmentsRaw.length}
          onShowAllApartments={() => setSelectedAlert(null)}
        />
        
        {/* Contenu principal */}
        <div className="main-content">
          {/* Message de succès/erreur du refresh */}
          {refreshMessage && (
            <div style={{
              padding: '12px 16px',
              backgroundColor: refreshMessage.startsWith('Erreur:') ? '#f8d7da' : '#d4edda',
              color: refreshMessage.startsWith('Erreur:') ? '#721c24' : '#155724',
              borderRadius: '6px',
              marginBottom: '20px',
              border: `1px solid ${refreshMessage.startsWith('Erreur:') ? '#f5c6cb' : '#c3e6cb'}`,
              fontWeight: '500'
            }}>
              {refreshMessage.startsWith('Erreur:') ? '❌' : '✅'} {refreshMessage}
            </div>
          )}
          {renderContent()}
        </div>
      </div>
      <AlertCreator
        isOpen={isAlertCreatorOpen}
        onClose={() => {
          setIsAlertCreatorOpen(false)
          setEditingAlert(null)
        }}
        onSuccess={handleCreateAlertSuccess}
        editingAlert={editingAlert}
      />
    </div>
  )
}

export default App

