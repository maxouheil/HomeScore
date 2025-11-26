import { useEffect, useState } from 'react'
import ApartmentCard from './components/ApartmentCard'
import AlertList from './components/AlertList'
import AlertCreator from './components/AlertCreator'
import AlertResults from './components/AlertResults'
import { calculateMegaScore } from './utils/scoreUtils'
import './App.css'

// États de navigation
const VIEWS = {
  APARTMENTS: 'apartments',
  ALERTS: 'alerts',
  CREATE_ALERT: 'create-alert',
  ALERT_RESULTS: 'alert-results'
}

function App() {
  const [view, setView] = useState(VIEWS.APARTMENTS)
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isAlertCreatorOpen, setIsAlertCreatorOpen] = useState(false)
  
  const [apartments, setApartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
    setView(VIEWS.ALERT_RESULTS)
  }

  const handleSelectAlert = (alert) => {
    setSelectedAlert(alert)
    setView(VIEWS.ALERT_RESULTS)
  }

  const handleBackToAlerts = () => {
    setSelectedAlert(null)
    setView(VIEWS.ALERTS)
  }

  const handleBackToApartments = () => {
    setView(VIEWS.APARTMENTS)
  }

  // Navigation
  const renderNavigation = () => {
    return (
      <nav className="main-navigation">
        <button
          className={`nav-button ${view === VIEWS.APARTMENTS ? 'active' : ''}`}
          onClick={() => setView(VIEWS.APARTMENTS)}
        >
          Appartements
        </button>
        <button
          className={`nav-button ${view === VIEWS.ALERTS || view === VIEWS.CREATE_ALERT || view === VIEWS.ALERT_RESULTS ? 'active' : ''}`}
          onClick={() => {
            setView(VIEWS.ALERTS)
            setSelectedAlert(null)
          }}
        >
          Alertes
        </button>
        <button
          className="nav-button nav-button-create-alert"
          onClick={() => setIsAlertCreatorOpen(true)}
        >
          Créer une alerte
        </button>
      </nav>
    )
  }

  // Rendu selon la vue
  const renderContent = () => {
    if (view === VIEWS.ALERT_RESULTS) {
      return (
        <AlertResults
          alertId={selectedAlert?.id}
          alert={selectedAlert}
          onBack={handleBackToAlerts}
        />
      )
    }

    if (view === VIEWS.ALERTS) {
      return (
        <AlertList
          onSelectAlert={handleSelectAlert}
          onCreateNew={() => setView(VIEWS.CREATE_ALERT)}
        />
      )
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
      {renderContent()}
      <AlertCreator
        isOpen={isAlertCreatorOpen}
        onClose={() => setIsAlertCreatorOpen(false)}
        onSuccess={handleCreateAlertSuccess}
      />
    </div>
  )
}

export default App

