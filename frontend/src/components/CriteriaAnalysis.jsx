import { useState, useEffect } from 'react'
import './CriteriaAnalysis.css'

const CRITERIA_NAMES = {
  'haussmanien': 'Haussmanien',
  'quartier': 'Quartier',
  'prix': 'Prix',
  'luminosite': 'Luminosité',
  'cuisine_ouverte': 'Cuisine ouverte',
  'ascenseur': 'Ascenseur',
  'large_piece_vie': 'Large pièce de vie',
  'hauteur_plafond': 'Hauteur plafond',
  'renove': 'Rénové',
  'calme': 'Calme'
}

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
  'calme': '🔇'
}

function CriteriaAnalysis() {
  const [analysisStatus, setAnalysisStatus] = useState(null)
  const [results, setResults] = useState([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  // Polling pour les mises à jour en temps réel
  useEffect(() => {
    if (!isAnalyzing) return

    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch('/api/criteria/status')
        if (statusResponse.ok) {
          const status = await statusResponse.json()
          setAnalysisStatus(status)

          // Récupérer les derniers résultats
          const latestResponse = await fetch('/api/criteria/latest')
          if (latestResponse.ok) {
            const latest = await latestResponse.json()
            setResults(latest.latest_results || [])
          }

          // Arrêter le polling si l'analyse est terminée
          if (!status.running) {
            setIsAnalyzing(false)
            // Charger tous les résultats finaux
            loadAllResults()
          }
        }
      } catch (err) {
        console.error('Erreur polling:', err)
      }
    }, 1000) // Mise à jour toutes les secondes

    return () => clearInterval(interval)
  }, [isAnalyzing])

  const startAnalysis = async () => {
    try {
      setError(null)
      setIsAnalyzing(true)
      setResults([])
      setAnalysisStatus(null)

      const response = await fetch('/api/criteria/analyze-all', {
        method: 'POST'
      })

      if (!response.ok) {
        throw new Error('Erreur lors du démarrage de l\'analyse')
      }

      // Démarrer le polling immédiatement
      const statusResponse = await fetch('/api/criteria/status')
      if (statusResponse.ok) {
        const status = await statusResponse.json()
        setAnalysisStatus(status)
      }
    } catch (err) {
      setError(err.message)
      setIsAnalyzing(false)
    }
  }

  const loadAllResults = async () => {
    try {
      const response = await fetch('/api/criteria/results')
      if (response.ok) {
        const allResults = await response.json()
        setResults(allResults)
      }
    } catch (err) {
      console.error('Erreur chargement résultats:', err)
    }
  }

  // Charger les résultats existants au montage
  useEffect(() => {
    loadAllResults()
  }, [])

  const getCriteriaValue = (criteriaData, criterion) => {
    if (!criteriaData || !criteriaData[criterion]) {
      return { value: null, confidence: null }
    }

    const data = criteriaData[criterion]
    
    // Adapter selon le type de critère
    if (criterion === 'haussmanien') {
      return { value: data.detected, confidence: data.confidence }
    } else if (criterion === 'quartier') {
      return { value: data.tier1, confidence: data.confidence }
    } else if (criterion === 'prix') {
      return { value: data.tier1, confidence: data.confidence }
    } else if (criterion === 'luminosite') {
      return { value: data.tier1, confidence: data.confidence }
    } else if (criterion === 'cuisine_ouverte') {
      return { value: data.ouverte, confidence: data.confidence }
    } else if (criterion === 'ascenseur') {
      return { value: data.present, confidence: data.confidence }
    } else if (criterion === 'large_piece_vie') {
      return { value: data.grande, confidence: data.confidence }
    } else if (criterion === 'hauteur_plafond') {
      return { value: data.haute, confidence: data.confidence }
    } else if (criterion === 'renove') {
      return { value: data.renove, confidence: data.confidence }
    } else if (criterion === 'calme') {
      return { value: data.calme, confidence: data.confidence }
    }

    return { value: null, confidence: null }
  }

  return (
    <div className="criteria-analysis-container">
      <div className="criteria-analysis-header">
        <h2>📊 Analyse des 10 Critères - 52 Appartements</h2>
        <button 
          className="btn-start-analysis" 
          onClick={startAnalysis}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? '⏳ Analyse en cours...' : '🚀 Démarrer l\'analyse'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {analysisStatus && isAnalyzing && (
        <div className="analysis-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(analysisStatus.progress / analysisStatus.total) * 100}%` }}
            />
          </div>
          <div className="progress-info">
            <span>
              {analysisStatus.progress} / {analysisStatus.total} appartements analysés
            </span>
            {analysisStatus.current_apartment && (
              <span className="current-apartment">
                En cours: {analysisStatus.current_apartment}
              </span>
            )}
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="results-summary">
          <h3>📋 Résultats ({results.length} appartements)</h3>
          
          {/* Tableau récapitulatif */}
          <div className="criteria-summary-table">
            <table>
              <thead>
                <tr>
                  <th>Appartement</th>
                  {Object.keys(CRITERIA_NAMES).map(criterion => (
                    <th key={criterion} title={CRITERIA_NAMES[criterion]}>
                      {CRITERIA_ICONS[criterion]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((result) => {
                  const criteria = result.criteria || {}
                  return (
                    <tr key={result.apartment_id}>
                      <td className="apartment-id">{result.apartment_id}</td>
                      {Object.keys(CRITERIA_NAMES).map(criterion => {
                        const { value, confidence } = getCriteriaValue(criteria, criterion)
                        return (
                          <td 
                            key={criterion}
                            className={`criterion-cell ${value === true ? 'yes' : value === false ? 'no' : 'unknown'}`}
                            title={`${CRITERIA_NAMES[criterion]}: ${value === true ? 'Oui' : value === false ? 'Non' : 'N/A'} (confiance: ${confidence ? Math.round(confidence * 100) : 'N/A'}%)`}
                          >
                            {value === true ? '✓' : value === false ? '✗' : '?'}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Statistiques par critère */}
          <div className="criteria-stats">
            <h4>📊 Statistiques par critère</h4>
            <div className="stats-grid">
              {Object.keys(CRITERIA_NAMES).map(criterion => {
                const yesCount = results.filter(r => {
                  const { value } = getCriteriaValue(r.criteria || {}, criterion)
                  return value === true
                }).length
                const noCount = results.filter(r => {
                  const { value } = getCriteriaValue(r.criteria || {}, criterion)
                  return value === false
                }).length
                const total = results.length
                const yesPct = total > 0 ? (yesCount / total * 100).toFixed(1) : 0

                return (
                  <div key={criterion} className="stat-card">
                    <div className="stat-header">
                      <span className="stat-icon">{CRITERIA_ICONS[criterion]}</span>
                      <span className="stat-name">{CRITERIA_NAMES[criterion]}</span>
                    </div>
                    <div className="stat-values">
                      <div className="stat-yes">✓ {yesCount} ({yesPct}%)</div>
                      <div className="stat-no">✗ {noCount}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {results.length === 0 && !isAnalyzing && (
        <div className="no-results">
          <p>Aucun résultat disponible. Cliquez sur "Démarrer l'analyse" pour commencer.</p>
        </div>
      )}
    </div>
  )
}

export default CriteriaAnalysis

