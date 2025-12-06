import { useState } from 'react'
import './ScoreBadge.css'

function getEtage(apartment) {
  if (apartment?.etage) return apartment.etage
  const caracteristiques = apartment?.caracteristiques || {}
  if (caracteristiques.etage) return caracteristiques.etage
  const description = apartment?.description || ''
  const etagePatterns = [
    /(\d+)(?:er?|e|ème?)\s*étage/i,
    /étage\s*(\d+)/i,
    /(\d+)(?:er?|e|ème?)\s*ét\./i,
    /RDC|rez-de-chaussée|rez de chaussée/i
  ]
  for (const pattern of etagePatterns) {
    const match = description.match(pattern)
    if (match) {
      if (pattern.source.includes('RDC')) return 'RDC'
      return `${match[1]}e étage`
    }
  }
  return null
}

function formatExpositionCriterion(apartment, etage) {
  if (apartment?.formatted_data?.exposition) {
    return {
      mainValue: apartment.formatted_data.exposition.main_value || 'Sombre',
      indices: apartment.formatted_data.exposition.indices || null,
      confidence: apartment.formatted_data.exposition.confidence || null
    }
  }
  const exposition = apartment?.exposition || {}
  const expositionDir = exposition.exposition || ''
  let mainValue = 'Luminosité moyenne'
  if (expositionDir) {
    const expoNormalized = expositionDir.toLowerCase().replace(/[_\s-]/g, '')
    if (expoNormalized === 'sud' || expoNormalized === 'sudouest' || expoNormalized === 'sudest') {
      mainValue = 'Lumineux'
    } else if (expoNormalized === 'nord' || expoNormalized === 'nordouest' || expoNormalized === 'nordest') {
      mainValue = 'Sombre'
    }
  }
  if (!expositionDir) {
    const styleAnalysis = apartment?.style_analysis || {}
    const luminositeData = styleAnalysis.luminosite || {}
    const luminositeType = luminositeData.type || ''
    if (luminositeType.toLowerCase().includes('excellente')) {
      mainValue = 'Lumineux'
    } else if (luminositeType.toLowerCase().includes('bonne') || luminositeType.toLowerCase().includes('moyenne')) {
      mainValue = 'Luminosité moyenne'
    } else {
      mainValue = 'Sombre'
    }
  }
  return { mainValue, indices: null, confidence: exposition.confidence || null }
}

// Mapping des noms de critères vers les noms d'affichage (utilisés dans le popup)
const CRITERIA_DISPLAY_NAMES = {
  'quartier': 'Quartier',
  'haussmanien': 'Style',
  'neuf': 'Style',
  'luminosite': 'Luminosité',
  'cuisine_ouverte': 'Cuisine',
  'prix': 'Prix',
  'ascenseur': 'Ascenseur',
  'large_piece_vie': 'Pièce de vie',
  'hauteur_plafond': 'Hauteur plafond',
  'renove': 'Rénové',
  'baignoire': 'Baignoire'
}

function calculateDetailedScores(apartment, alertCriteria = null) {
  if (!apartment) return null
  
  // PRIORITÉ: Utiliser les scores d'alerte si disponibles
  if (apartment.alert_criteria_scores && alertCriteria) {
    const alertCriteriaScores = apartment.alert_criteria_scores
    // Support nouveau format (all) et ancien format (primary/secondary) pour compatibilité
    const allCriteriaNames = alertCriteria.all || [...(alertCriteria.primary || []), ...(alertCriteria.secondary || [])]
    
    // Retourner les scores dans l'ordre de l'alerte avec leurs noms d'affichage
    const orderedScores = []
    
    for (const criterionName of allCriteriaNames) {
      const criterionScore = alertCriteriaScores[criterionName]
      if (criterionScore && typeof criterionScore.score === 'number') {
        const displayName = CRITERIA_DISPLAY_NAMES[criterionName] || criterionName
        const maxScore = 1 // Tous les critères sont à 1 point max (good=1pt, moyen=0.5pt, bad=0pt)
        orderedScores.push({
          key: criterionName,
          displayName,
          score: criterionScore.score, // Garder les décimales (0.5 pour moyen)
          tier: criterionScore.tier || 'tier3',
          maxScore
        })
      }
    }
    
    return {
      ordered: orderedScores, // Scores dans l'ordre de l'alerte
      isAlertScore: true
    }
  }
  
  // Fallback: utiliser les scores standards
  const scores = apartment.scores_detaille || {}
  const detailedScores = {}
  
  // Quartier (Localisation) - utiliser le score directement
  if (scores.localisation) {
    detailedScores.quartier = Math.round(scores.localisation.score || 0)
  } else {
    detailedScores.quartier = 0
  }
  
  // Style - utiliser le score directement
  if (scores.style) {
    detailedScores.style = Math.round(scores.style.score || 0)
  } else {
    detailedScores.style = 0
  }
  
  // Cuisine - utiliser le score directement depuis scores_detaille
  if (scores.cuisine) {
    // Utiliser le score depuis scores_detaille.cuisine.score si disponible
    // Sinon calculer selon le tier (même logique que calculateMegaScore)
    if (scores.cuisine.score !== undefined) {
      detailedScores.cuisine = Math.round(scores.cuisine.score)
    } else {
      const cuisineValue = apartment.style_analysis?.cuisine?.ouverte ? 'Ouverte' : 'Fermée'
      let tier = scores.cuisine.tier || 'tier3'
      if (cuisineValue === 'Ouverte' && tier !== 'tier1') {
        tier = 'tier1'
      }
      if (cuisineValue === 'Fermée' && tier !== 'tier3') {
        tier = 'tier3'
      }
      detailedScores.cuisine = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
    }
  } else {
    detailedScores.cuisine = 0
  }
  
  // Luminosité (Exposition) - utiliser le score selon le tier (même logique que calculateMegaScore)
  if (scores.ensoleillement) {
    const etage = getEtage(apartment)
    const expoData = formatExpositionCriterion(apartment, etage)
    let tier = scores.ensoleillement.tier || 'tier3'
    if (expoData.mainValue === 'Lumineux' && tier !== 'tier1') {
      tier = 'tier1'
    } else if (expoData.mainValue === 'Luminosité moyenne' && tier !== 'tier2') {
      tier = 'tier2'
    } else if (expoData.mainValue === 'Sombre' && tier !== 'tier3') {
      tier = 'tier3'
    }
    detailedScores.luminosite = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
  } else {
    detailedScores.luminosite = 0
  }
  
  // Retourner le format standard pour le fallback
  return {
    ordered: null,
    isAlertScore: false,
    quartier: detailedScores.quartier,
    style: detailedScores.style,
    cuisine: detailedScores.cuisine,
    luminosite: detailedScores.luminosite
  }
}

function ScoreBadge({ score, maxScore = 90, apartment = null, alertCriteria = null }) {
  const [isHovered, setIsHovered] = useState(false)
  const percentage = (score / maxScore) * 100
  let color = "#F85457" // Rouge par défaut
  
  if (percentage >= 80) {
    color = "#00966D" // Vert
  } else if (percentage >= 60) {
    color = "#F59E0B" // Jaune
  }
  
  // Formater le score pour l'affichage
  const displayScore = score === Math.floor(score) ? Math.floor(score) : score
  const displayStr = String(displayScore) === "00" ? "0" : String(displayScore)
  
  const detailedScoresResult = calculateDetailedScores(apartment, alertCriteria)
  
  return (
    <div 
      className="score-badge-wrapper"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div 
        className="score-badge-top" 
        style={{ background: color }}
      >
        {displayStr}
      </div>
      {detailedScoresResult && detailedScoresResult.isAlertScore && detailedScoresResult.ordered && detailedScoresResult.ordered.length > 0 && (
        <div className={`score-details-menu ${isHovered ? 'visible' : ''}`}>
          {detailedScoresResult.ordered.map((item, index) => {
            // Déterminer la couleur selon le tier : tier1 (good) = vert, tier2 (moyen) = orange, tier3 (bad) = rouge
            let scoreColor = 'score-red' // Par défaut rouge
            if (item.tier === 'tier1') {
              scoreColor = 'score-green' // Good = vert
            } else if (item.tier === 'tier2') {
              scoreColor = 'score-yellow' // Moyen = orange/jaune
            } else {
              scoreColor = 'score-red' // Bad = rouge
            }
            
            return (
              <div key={item.key || index} className="score-detail-item">
                <span className="score-detail-label">{item.displayName}</span>
                <span className={`score-detail-value ${scoreColor}`}>
                  {item.score === 1 ? '1 pt' : item.score === 0.5 ? '0.5 pt' : '0 pt'}
                </span>
              </div>
            )
          })}
        </div>
      )}
      {detailedScoresResult && !detailedScoresResult.isAlertScore && (
        <div className={`score-details-menu ${isHovered ? 'visible' : ''}`}>
          <div className="score-detail-item">
            <span className="score-detail-label">Quartier</span>
            <span className={`score-detail-value ${detailedScoresResult.quartier > 0 ? 'score-green' : 'score-red'}`}>
              {detailedScoresResult.quartier} pts
            </span>
          </div>
          <div className="score-detail-item">
            <span className="score-detail-label">Style</span>
            <span className={`score-detail-value ${detailedScoresResult.style > 0 ? 'score-yellow' : 'score-red'}`}>
              {detailedScoresResult.style} pts
            </span>
          </div>
          <div className="score-detail-item">
            <span className="score-detail-label">Cuisine</span>
            <span className={`score-detail-value ${detailedScoresResult.cuisine > 0 ? 'score-yellow' : 'score-red'}`}>
              {detailedScoresResult.cuisine} pts
            </span>
          </div>
          <div className="score-detail-item">
            <span className="score-detail-label">Luminosité</span>
            <span className={`score-detail-value ${detailedScoresResult.luminosite > 0 ? 'score-yellow' : 'score-red'}`}>
              {detailedScoresResult.luminosite} pts
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScoreBadge

