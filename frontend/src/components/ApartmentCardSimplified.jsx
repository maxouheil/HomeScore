import { useMemo } from 'react'
import Carousel from './Carousel'
import './ApartmentCard.css'

// Version simplifiée qui utilise directement apartment.criteria (format normalisé)
function ApartmentCardSimplified({ apartment, alertCriteria = null }) {
  // Vérifier si c'est le format normalisé
  const isNormalized = apartment.criteria !== undefined
  
  // Si format normalisé, utiliser directement
  if (isNormalized) {
    return <ApartmentCardNormalized apartment={apartment} alertCriteria={alertCriteria} />
  }
  
  // Sinon, utiliser l'ancien format (compatibilité)
  return <ApartmentCardLegacy apartment={apartment} alertCriteria={alertCriteria} />
}

function ApartmentCardNormalized({ apartment, alertCriteria = null }) {
  // Extraire les données depuis le format normalisé
  const apartmentInfo = useMemo(() => {
    const prixK = apartment.prix ? `${Math.round(apartment.prix / 1000)}k` : null
    const localisation = apartment.localisation || {}
    const metro = localisation.metro || null
    const quartier = localisation.quartier || null
    
    // Formater le titre: "750k · Belleville" (métro en priorité)
    let title = 'Appartement'
    if (prixK && metro) {
      title = `${prixK} · ${metro.replace('Métro ', '')}`
    } else if (prixK && quartier) {
      title = `${prixK} · ${quartier}`
    } else if (prixK) {
      const arr = localisation.arrondissement
      if (arr) {
        const arrNum = arr.slice(-2)
        title = `${prixK} · Paris ${arrNum}e`
      } else {
        title = `${prixK} · ${localisation.adresse || 'Appartement'}`
      }
    } else if (metro) {
      title = metro.replace('Métro ', '')
    } else if (quartier) {
      title = quartier
    } else {
      title = localisation.adresse || 'Appartement'
    }
    
    // Construire le subtitle: surface · étage · vis-à-vis
    const subtitleParts = []
    if (apartment.surface_formatted) {
      subtitleParts.push(apartment.surface_formatted)
    }
    if (apartment.etage) {
      subtitleParts.push(apartment.etage)
    }
    
    // Ajouter vis-à-vis depuis exposition si disponible
    const expoIndices = apartment.criteria?.exposition?.display?.indices
    if (expoIndices) {
      const visavisMatch = expoIndices.match(/Vis a vis (?:bon|moyen|mauvais) \((\d+)m\)/i)
      if (visavisMatch) {
        subtitleParts.push(`Vis a vis ${visavisMatch[1]}m`)
      }
    }
    
    const subtitle = subtitleParts.join(' · ') || apartment.surface_formatted || ''
    
    return { title, subtitle }
  }, [apartment])
  
  // Calculer le score d'alerte si on est dans une vue d'alerte
  const displayScore = useMemo(() => {
    if (apartment.alert_criteria_scores && alertCriteria) {
      const alertCriteriaScores = apartment.alert_criteria_scores
      const allCriteriaNames = alertCriteria.all || [...(alertCriteria.primary || []), ...(alertCriteria.secondary || [])]
      
      let total = 0
      for (const criterionName of allCriteriaNames) {
        const criterionScore = alertCriteriaScores[criterionName]
        if (criterionScore && typeof criterionScore.score === 'number') {
          total += criterionScore.score
        }
      }
      return total
    }
    
    // Si on a alert_score, l'utiliser
    if (apartment.alert_score !== undefined) {
      if (apartment.alert_score > 5) {
        return Math.round(apartment.alert_score / 20 * 10) / 10
      }
      return apartment.alert_score
    }
    
    // Pas de score par défaut (pas de score absolu)
    return undefined
  }, [apartment.alert_criteria_scores, apartment.alert_score, alertCriteria])
  
  const maxScore = useMemo(() => {
    if (apartment.alert_criteria_scores || apartment.alert_tier || apartment.alert_score !== undefined) {
      return 5
    }
    return undefined // Pas de score absolu
  }, [apartment.alert_criteria_scores, apartment.alert_tier, apartment.alert_score])
  
  // Récupérer les photos (format normalisé: array d'objets {url, index, is_local})
  const photos = useMemo(() => {
    const photoUrls = []
    if (apartment.photos && Array.isArray(apartment.photos)) {
      apartment.photos.forEach(photo => {
        // Format normalisé: {url, index, is_local}
        let url = null
        if (typeof photo === 'string') {
          url = photo
        } else if (photo && typeof photo === 'object') {
          url = photo.url || photo.local_path
        }
        
        if (url && typeof url === 'string' && url.trim() && !url.includes('logo') && !url.includes('Logo')) {
          const trimmedUrl = url.trim()
          // Si c'est local, construire le chemin complet
          if (trimmedUrl.startsWith('/data/photos/') || trimmedUrl.startsWith('../data/photos/')) {
            photoUrls.push(trimmedUrl.replace('../', '/'))
          } else if (!trimmedUrl.startsWith('http') && !trimmedUrl.startsWith('https')) {
            photoUrls.push(`/data/photos/${apartment.id}/${trimmedUrl}`)
          } else {
            photoUrls.push(trimmedUrl)
          }
        }
      })
    }
    return photoUrls.slice(0, 10)
  }, [apartment])
  
  // Extraire l'index de la photo détectée
  const detectedPhotoIndex = useMemo(() => {
    // Chercher dans les critères cuisine ou baignoire
    const cuisineIndices = apartment.criteria?.cuisine?.display?.indices
    const baignoireIndices = apartment.criteria?.baignoire?.display?.indices
    
    if (cuisineIndices) {
      const match = cuisineIndices.match(/image\s*(\d+)/i)
      if (match) {
        const photoNum = parseInt(match[1], 10)
        if (photoNum >= 1 && photoNum <= photos.length) {
          return photoNum - 1
        }
      }
    }
    
    if (baignoireIndices) {
      const match = baignoireIndices.match(/image\s*(\d+)/i)
      if (match) {
        const photoNum = parseInt(match[1], 10)
        if (photoNum >= 1 && photoNum <= photos.length) {
          return photoNum - 1
        }
      }
    }
    
    return null
  }, [apartment, photos.length])
  
  const handleClick = () => {
    if (apartment.url) {
      window.open(apartment.url, '_blank')
    }
  }
  
  const carouselId = `carousel-${apartment.id}`
  
  return (
    <div className="scorecard" onClick={handleClick}>
      <Carousel photos={photos} carouselId={carouselId} score={displayScore} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} initialIndex={detectedPhotoIndex} />
      <div className="apartment-info">
        <div className="apartment-title">{apartmentInfo.title}</div>
        <div className="apartment-subtitle">{apartmentInfo.subtitle}</div>
        
        {/* Critères */}
        {(() => {
          // Si c'est un résultat d'alerte, afficher d'abord les critères de l'alerte
          if (apartment.alert_criteria_scores && alertCriteria) {
            const alertCriteriaScores = apartment.alert_criteria_scores
            const orderedAlertCriteriaNames = alertCriteria.all || [...(alertCriteria.primary || []), ...(alertCriteria.secondary || [])]
            const alertCriteriaNames = orderedAlertCriteriaNames.filter(name => alertCriteriaScores[name])
            
            return (
              <>
                {alertCriteriaNames.map((alertCriterionName, alertIndex) => {
                  const criterionScore = alertCriteriaScores[alertCriterionName]
                  const displayName = ALERT_CRITERIA_TO_DISPLAY[alertCriterionName] || alertCriterionName
                  const tier = criterionScore?.tier || 'tier3'
                  
                  // Mapper le nom du critère d'alerte vers le critère normalisé
                  const criterionKey = ALERT_TO_CRITERION_MAP[alertCriterionName] || alertCriterionName
                  const normalizedCriterion = apartment.criteria?.[criterionKey]
                  
                  // Utiliser les données normalisées si disponibles
                  const customTitle = normalizedCriterion?.display?.title || displayName
                  const customDescription = normalizedCriterion?.display?.description || criterionScore?.justification || ''
                  const customIndices = normalizedCriterion?.display?.indices || null
                  
                  return (
                    <Criterion
                      key={alertCriterionName}
                      name={displayName}
                      score={criterionScore?.score || 0}
                      tier={tier}
                      customTitle={customTitle}
                      customDescription={customDescription}
                      indices={customIndices}
                      alertCriterionName={alertCriterionName}
                      noBorderBottom={alertIndex < alertCriteriaNames.length - 1}
                    />
                  )
                })}
              </>
            )
          }
          
          // Sinon, afficher les critères standards depuis apartment.criteria
          const criteria = apartment.criteria || {}
          const criteriaOrder = ['localisation', 'prix', 'style', 'exposition', 'cuisine', 'baignoire', 'hauteur_plafond', 'piece_vie']
          
          return (
            <>
              {criteriaOrder.map((key) => {
                const criterion = criteria[key]
                if (!criterion) return null
                
                const display = criterion.display || {}
                return (
                  <Criterion
                    key={key}
                    name={CRITERION_NAMES[key] || key}
                    score={criterion.score || 0}
                    tier={criterion.tier || 'tier3'}
                    customTitle={display.title || ''}
                    customDescription={display.description || null}
                    indices={display.indices || null}
                    isGray={!alertCriteria}
                  />
                )
              })}
            </>
          )
        })()}
      </div>
    </div>
  )
}

// Mapping des critères d'alerte vers les critères normalisés
const ALERT_TO_CRITERION_MAP = {
  'quartier': 'localisation',
  'localisation': 'localisation',
  'prix': 'prix',
  'haussmanien': 'style',
  'neuf': 'style',
  'luminosite': 'exposition',
  'cuisine_ouverte': 'cuisine',
  'baignoire': 'baignoire',
  'hauteur_plafond': 'hauteur_plafond',
  'large_piece_vie': 'piece_vie'
}

// Mapping des critères d'alerte vers les noms d'affichage
const ALERT_CRITERIA_TO_DISPLAY = {
  'haussmanien': 'Style',
  'neuf': 'Style',
  'quartier': 'Localisation',
  'prix': 'Prix',
  'luminosite': 'Exposition',
  'cuisine_ouverte': 'Cuisine',
  'ascenseur': 'Ascenseur',
  'large_piece_vie': 'Pièce de vie',
  'hauteur_plafond': 'Hauteur plafond',
  'renove': 'Rénové',
  'baignoire': 'Baignoire'
}

// Noms des critères
const CRITERION_NAMES = {
  'localisation': 'Localisation',
  'prix': 'Prix',
  'style': 'Style',
  'exposition': 'Exposition',
  'cuisine': 'Cuisine',
  'baignoire': 'Baignoire',
  'hauteur_plafond': 'Hauteur plafond',
  'piece_vie': 'Pièce de vie'
}

// Mapping des emojis
const CRITERION_EMOJIS = {
  'Localisation': '📍',
  'Prix': '💰',
  'Style': '🎨',
  'Exposition': '☀️',
  'Cuisine': '👨‍🍳',
  'Baignoire': '🛁',
  'Hauteur plafond': '📏',
  'Pièce de vie': '🛋️'
}

const ALERT_CRITERIA_EMOJIS = {
  'haussmanien': '🔑',
  'neuf': '✨',
  'quartier': '📍',
  'prix': '💰',
  'luminosite': '☀️',
  'cuisine_ouverte': '👨‍🍳',
  'ascenseur': '🛗',
  'large_piece_vie': '🛋️',
  'hauteur_plafond': '📏',
  'renove': '🔨',
  'baignoire': '🛁'
}

function Criterion({ name, score, tier, value, confidence, indices, customTitle, customDescription, descriptionClass, isGray = false, alertCriterionName = null, noBorderBottom = false, noBorderTop = false }) {
  const badgeClass = tier === 'tier1' ? 'green' : tier === 'tier2' ? 'yellow' : 'red'
  const emoji = alertCriterionName && ALERT_CRITERIA_EMOJIS[alertCriterionName] 
    ? ALERT_CRITERIA_EMOJIS[alertCriterionName] 
    : CRITERION_EMOJIS[name] || '📋'
  
  const title = customTitle || name
  const description = customDescription !== undefined ? customDescription : value
  
  const criterionClasses = ['criterion']
  if (isGray) criterionClasses.push('criterion-gray')
  if (noBorderBottom) criterionClasses.push('criterion-no-border-bottom')
  if (noBorderTop) criterionClasses.push('criterion-no-border-top')
  
  const descriptionClassFinal = descriptionClass 
    ? `criterion-description-${descriptionClass}` 
    : ''
  
  return (
    <div className={criterionClasses.join(' ')}>
      <div className="criterion-content">
        <div className="criterion-header">
          <span className={`criterion-emoji ${isGray ? 'gray' : badgeClass}`}>{emoji}</span>
          <div className="criterion-text-wrapper">
            <div className="criterion-name">{title}</div>
            {/* Description (données API, en gris) et Indices (données IA, en bleu) */}
            {(description || indices) && (
              <div className="criterion-description-wrapper">
                {/* Description API (gris) */}
                {description && (
                  <span className="criterion-description criterion-description-api">
                    {typeof description === 'string' ? (
                      <span dangerouslySetInnerHTML={{ __html: description.replace(/m²/g, 'm<sup>2</sup>') }} />
                    ) : (
                      description
                    )}
                  </span>
                )}
                {/* Séparateur si on a description ET indices */}
                {description && indices && (
                  <span className="criterion-separator"> · </span>
                )}
                {/* Indices IA (bleu) */}
                {indices && (
                  <span className="criterion-indices-inline">
                    {indices
                      .replace(/^Style Indice:\n?/, '')
                      .replace(/^Expo Indice:\n?/, '')
                      .replace(/^Exposition Indice:\n?/, '')
                      .replace(/^Cuisine Indice:\n?/, '')
                      .replace(/^Baignoire Indice:\n?/, '')
                      .replace(/^Baignoire:\n?/, '')
                      .replace(/^Prix Indice:\n?/, '')
                      .replace(/^Hauteur Indice:\n?/, '')
                      .replace(/^Pièce de vie Indice:\n?/, '')}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Composant legacy pour compatibilité (à supprimer une fois tout normalisé)
function ApartmentCardLegacy({ apartment, alertCriteria = null }) {
  // Pour l'instant, on peut rediriger vers l'ancien composant ou afficher un message
  return (
    <div className="scorecard">
      <div className="apartment-info">
        <div className="apartment-title">Format non normalisé - Migration en cours</div>
        <div className="apartment-subtitle">ID: {apartment.id}</div>
      </div>
    </div>
  )
}

export default ApartmentCardSimplified
