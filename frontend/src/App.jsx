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

    // WebSocket pour mises à jour en temps réel
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('✅ WebSocket connecté')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'apartments_updated') {
        console.log('📢 Mise à jour des appartements détectée')
        // Recharger les données
        loadApartments()
      }
    }

    ws.onerror = (err) => {
      console.error('Erreur WebSocket:', err)
    }

    ws.onclose = () => {
      console.log('WebSocket fermé')
    }

    return () => {
      ws.close()
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

