import { useEffect, useState } from 'react'
import ApartmentCard from './components/ApartmentCard'
import { calculateMegaScore } from './utils/scoreUtils'
import './App.css'

function App() {
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

  if (loading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <p>Chargement des appartements...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '50px', color: '#F85457' }}>
          <p>Erreur: {error}</p>
          <p style={{ fontSize: '12px', marginTop: '10px' }}>
            Assurez-vous que le serveur backend est démarré sur le port 8000
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="apartments-grid">
        {apartments.map(apartment => (
          <ApartmentCard key={apartment.id} apartment={apartment} />
        ))}
      </div>
    </div>
  )
}

export default App

