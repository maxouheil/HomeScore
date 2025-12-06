import { useEffect, useState } from 'react'
import ApartmentCard from './components/ApartmentCard'
import AlertCreator from './components/AlertCreator'
import AlertResults from './components/AlertResults'
import AlertSidebar from './components/AlertSidebar'
import { calculateMegaScore } from './utils/scoreUtils'
import './App.css'

// États de navigation
const VIEWS = {
  APARTMENTS: 'apartments',
  ALERTS: 'alerts'
}

function App() {
  const [view, setView] = useState(VIEWS.APARTMENTS)
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isAlertCreatorOpen, setIsAlertCreatorOpen] = useState(false)
  const [isAlertSidebarOpen, setIsAlertSidebarOpen] = useState(false)
  const [editingAlert, setEditingAlert] = useState(null)
  
  const [apartments, setApartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Charger la dernière alerte au démarrage
  useEffect(() => {
    const loadLastAlert = async () => {
      try {
        const response = await fetch('/api/alerts')
        if (response.ok) {
          const alerts = await response.json()
          // Les alertes sont déjà triées par date de création (plus récent en premier)
          if (alerts.length > 0) {
            setSelectedAlert(alerts[0])
            setView(VIEWS.ALERTS)
          }
        }
      } catch (err) {
        console.error('Erreur lors du chargement des alertes:', err)
      }
    }
    loadLastAlert()
  }, [])

  useEffect(() => {
    // Charger les données initiales
    const loadApartments = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/apartments')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        // Trier par mega score décroissant (du plus grand au plus petit)
        const sorted = data.sort((a, b) => {
          const scoreA = calculateMegaScore(a)
          const scoreB = calculateMegaScore(b)
          return scoreB - scoreA // Décroissant : plus grand score en premier
        })
        setApartments(sorted)
        setError(null)
      } catch (err) {
        console.error('Erreur lors du chargement des appartements:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadApartments()

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
              // Recharger les données
              loadApartments()
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
    setView(VIEWS.ALERTS)
    setEditingAlert(null)
  }

  const handleSelectAlert = (alert) => {
    setSelectedAlert(alert)
    setView(VIEWS.ALERTS)
    // Fermer la sidebar sur mobile après sélection
    if (window.innerWidth < 768) {
      setIsAlertSidebarOpen(false)
    }
  }

  // Ouvrir automatiquement la sidebar quand on est sur la vue alertes
  useEffect(() => {
    if (view === VIEWS.ALERTS) {
      setIsAlertSidebarOpen(true)
    } else {
      setIsAlertSidebarOpen(false)
    }
  }, [view])

  // Navigation
  const renderNavigation = () => {
    if (view === VIEWS.ALERTS) {
      // Vue Alertes : Burger menu + Nom alerte + Modifier | Tous + Créer une alerte
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
            {selectedAlert && (
              <>
                <h2 className="nav-alert-name">{selectedAlert.name || 'Alerte'}</h2>
                <button
                  className="nav-button-modify"
                  onClick={() => {
                    setEditingAlert(selectedAlert)
                    setIsAlertCreatorOpen(true)
                  }}
                >
                  Modifier
                </button>
              </>
            )}
          </div>
          <div className="nav-right">
            {/* ARCHIVÉ: Bouton "Tous" - masqué car non pertinent
            <button
              className="nav-button nav-button-all"
              onClick={() => setView(VIEWS.APARTMENTS)}
            >
              Tous
            </button>
            */}
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

    // Vue Appartements : navigation normale
    return (
      <nav className="main-navigation">
        <div className="nav-left">
          <button
            className={`nav-button ${view === VIEWS.APARTMENTS ? 'active' : ''}`}
            onClick={() => setView(VIEWS.APARTMENTS)}
          >
            Appartements
          </button>
          <button
            className={`nav-button ${view === VIEWS.ALERTS ? 'active' : ''}`}
            onClick={() => {
              // Charger la dernière alerte si aucune n'est sélectionnée
              if (!selectedAlert) {
                fetch('/api/alerts')
                  .then(res => res.json())
                  .then(alerts => {
                    if (alerts.length > 0) {
                      setSelectedAlert(alerts[0])
                    }
                  })
                  .catch(console.error)
              }
              setView(VIEWS.ALERTS)
            }}
          >
            Alertes
          </button>
        </div>
        <div className="nav-right">
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

  // Rendu selon la vue
  const renderContent = () => {
    if (view === VIEWS.ALERTS) {
      if (selectedAlert) {
        return (
          <AlertResults
            alertId={selectedAlert.id}
            alert={selectedAlert}
          />
        )
      } else {
        return (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>Aucune alerte disponible.</p>
            <button
              className="nav-button nav-button-create-alert"
              onClick={() => setIsAlertCreatorOpen(true)}
              style={{ marginTop: '20px' }}
            >
              Créer une alerte
            </button>
          </div>
        )
      }
    }

    // Vue par défaut: APARTMENTS
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
      <div className="apartments-grid">
        {apartments.map(apartment => (
          <ApartmentCard key={apartment.id} apartment={apartment} />
        ))}
      </div>
    )
  }

  return (
    <div className="container">
      {renderNavigation()}
      <div className="main-content-wrapper">
        {/* Sidebar des alertes */}
        {view === VIEWS.ALERTS && (
          <AlertSidebar
            isOpen={isAlertSidebarOpen}
            onClose={() => setIsAlertSidebarOpen(false)}
            onSelectAlert={handleSelectAlert}
            selectedAlertId={selectedAlert?.id}
          />
        )}
        
        {/* Contenu principal */}
        <div className="main-content">
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

