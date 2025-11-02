import { useMemo } from 'react'
import Carousel from './Carousel'
import { calculateMegaScore } from '../utils/scoreUtils'
import './ApartmentCard.css'

// Fonctions utilitaires pour formater les données
function formatPrixK(prixStr) {
  if (!prixStr) return null
  const prixClean = prixStr.replace(/[^\d]/g, '')
  if (prixClean) {
    const prixInt = parseInt(prixClean)
    const prixK = Math.round(prixInt / 1000)
    return `${prixK}k`
  }
  return null
}

function getQuartierName(apartment) {
  // Priorité 1: map_info.quartier
  const mapInfo = apartment.map_info || {}
  let quartier = mapInfo.quartier || ''
  
  if (quartier && quartier !== 'Quartier non identifié') {
    quartier = quartier.replace(/\s*\(score:\s*\d+\)/g, '').trim()
    if (quartier && quartier !== 'Non identifié') {
      return quartier
    }
  }
  
  // Priorité 2: scores_detaille.localisation.justification
  const scores = apartment.scores_detaille || {}
  const localisationScore = scores.localisation || {}
  const justification = localisationScore.justification || ''
  
  const quartierMatch = justification.match(/quartier\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.])/i)
  if (quartierMatch) {
    quartier = quartierMatch[1].trim()
    if (quartier && quartier.length > 3 && 
        !['Non identifié', 'Non identifiée', 'correcte', 'bonnes zones'].includes(quartier)) {
      return quartier
    }
  }
  
  // Priorité 3: exposition.details.photo_details.quartier
  const exposition = apartment.exposition || {}
  const details = exposition.details || {}
  const photoDetails = details.photo_details || {}
  const quartierData = photoDetails.quartier || {}
  
  if (typeof quartierData === 'object' && quartierData.quartier) {
    quartier = quartierData.quartier
    if (quartier && !['Non identifié', 'Non identifiée'].includes(quartier)) {
      return quartier.replace(/\s*\(proximité\)/g, '').trim()
    }
  }
  
  // Fallback: chercher dans localisation
  const localisation = apartment.localisation || ''
  const quartiersPatterns = [
    /Buttes[- ]Chaumont/i,
    /Place des Fêtes/i,
    /Place de la Réunion/i,
    /Jourdain/i,
    /Pyrénées/i,
    /Belleville/i,
    /Ménilmontant/i,
    /Canal de l'Ourcq/i
  ]
  
  for (const pattern of quartiersPatterns) {
    const match = localisation.match(pattern)
    if (match) {
      return match[0]
    }
  }
  
  return null
}

function getMetroName(apartment) {
  const scores = apartment.scores_detaille || {}
  const localisationScore = scores.localisation || {}
  const justification = localisationScore.justification || ''
  
  // Chercher "métro XXX" dans la justification
  const metroMatch = justification.match(/métro\s+([A-Za-z\s\-éàèùîêôûçâë]+?)(?:[,\.]|\s+(?:zone|ligne|arrondissement)|\s*$)/i)
  if (metroMatch) {
    const metro = metroMatch[1].trim()
    if (metro && metro.length > 2 && metro.length < 50 && 
        !['non trouvé', 'proximité', 'immédiate'].includes(metro.toLowerCase())) {
      return metro
    }
  }
  
  // Chercher dans map_info.metros
  const mapInfo = apartment.map_info || {}
  const metros = mapInfo.metros || []
  if (metros.length > 0) {
    let metro = metros[0].trim()
    metro = metro.replace(/^métro\s+/i, '').trim()
    if (metro && metro.length > 2 && metro.length < 50) {
      return metro
    }
  }
  
  return null
}

function getEtage(apartment) {
  // Chercher dans etage directement
  if (apartment.etage) {
    return apartment.etage
  }
  
  // Chercher dans caracteristiques
  const caracteristiques = apartment.caracteristiques || {}
  if (caracteristiques.etage) {
    return caracteristiques.etage
  }
  
  // Chercher dans description
  const description = apartment.description || ''
  const etagePatterns = [
    /(\d+)(?:er?|e|ème?)\s*étage/i,
    /étage\s*(\d+)/i,
    /(\d+)(?:er?|e|ème?)\s*ét\./i,
    /RDC|rez-de-chaussée|rez de chaussée/i
  ]
  
  for (const pattern of etagePatterns) {
    const match = description.match(pattern)
    if (match) {
      if (pattern.source.includes('RDC')) {
        return 'RDC'
      }
      return `${match[1]}e étage`
    }
  }
  
  return null
}

function formatPrixM2(apartment) {
  let prixM2 = apartment.prix_m2 || ''
  const surface = apartment.surface || ''
  const prix = apartment.prix || ''
  
  // Si prix_m2 existe et est valide
  if (prixM2 && prixM2 !== 'Prix/m² non trouvé') {
    const prixM2Match = prixM2.replace(/\s/g, '').match(/(\d+)/)
    if (prixM2Match) {
      const prixNum = parseInt(prixM2Match[1])
      return `${prixNum.toLocaleString('fr-FR')} € / m²`
    }
  }
  
  // Sinon, calculer depuis prix et surface
  if (surface && prix) {
    const surfaceMatch = surface.match(/(\d+)/)
    const prixMatch = prix.replace(/\s/g, '').match(/(\d+)/)
    
    if (surfaceMatch && prixMatch) {
      const surfaceNum = parseInt(surfaceMatch[1])
      const prixNum = parseInt(prixMatch[1])
      
      if (surfaceNum > 0) {
        const prixM2Calc = Math.floor(prixNum / surfaceNum)
        return `${prixM2Calc.toLocaleString('fr-FR')} € / m²`
      }
    }
  }
  
  return null
}

function getStyleName(apartment) {
  const styleAnalysis = apartment.style_analysis || {}
  const styleData = styleAnalysis.style || {}
  const styleType = styleData.type || ''
  
  if (styleType && styleType !== 'autre' && styleType !== 'inconnu') {
    // Capitaliser la première lettre
    let styleName = styleType.charAt(0).toUpperCase() + styleType.slice(1)
    
    // Gérer les cas spéciaux
    if (styleType.includes('70') || styleType.toLowerCase().includes('seventies')) {
      styleName = "70s"
    } else if (styleType.toLowerCase().includes('haussmann')) {
      styleName = "Haussmannien"
    }
    
    return `Style ${styleName}`
  }
  
  return null
}

function ApartmentCard({ apartment }) {
  const apartmentInfo = useMemo(() => {
    const prix = apartment.prix || ''
    const prixK = formatPrixK(prix)
    const quartier = getQuartierName(apartment)
    const metro = getMetroName(apartment)
    const localisation = apartment.localisation || ''
    
    // Formater le titre: "750k · Place de la Réunion" ou "750k · Ménilmontant"
    let title = 'Appartement'
    if (prixK && quartier) {
      title = `${prixK} · ${quartier}`
    } else if (prixK && metro) {
      title = `${prixK} · ${metro}`
    } else if (prixK) {
      // Extraire l'arrondissement de la localisation
      const arrMatch = localisation.match(/Paris (\d+e)/)
      if (arrMatch) {
        title = `${prixK} · Paris ${arrMatch[1]}`
      } else {
        title = `${prixK} · ${localisation}`
      }
    } else if (quartier) {
      title = quartier
    } else if (metro) {
      title = metro
    } else {
      title = localisation || 'Appartement'
    }
    
    // Extraire la surface
    const surface = apartment.surface || ''
    let surfaceClean = ''
    const surfaceMatch = surface.match(/(\d+)\s*m²/)
    if (surfaceMatch) {
      surfaceClean = `${surfaceMatch[1]} m²`
    } else {
      // Essayer depuis le titre
      const titre = apartment.titre || ''
      const titreMatch = titre.match(/(\d+)\s*m²/)
      if (titreMatch) {
        surfaceClean = `${titreMatch[1]} m²`
      }
    }
    
    // Extraire le style
    const styleName = getStyleName(apartment)
    
    // Construire le subtitle: surface · style (étage sera ajouté après via useMemo)
    const subtitleParts = [surfaceClean, styleName].filter(Boolean)
    const subtitle = subtitleParts.join(' · ') || `${surface || ''} - ${apartment.pieces || ''}`
    
    return { title, subtitle }
  }, [apartment])
  
  // Extraire l'étage (pour l'utiliser dans le subtitle et les critères)
  const etage = useMemo(() => getEtage(apartment), [apartment])
  
  // Mettre à jour le subtitle pour inclure l'étage
  const apartmentInfoWithEtage = useMemo(() => {
    const baseInfo = apartmentInfo
    if (etage) {
      // Insérer l'étage après la surface dans le subtitle
      const parts = baseInfo.subtitle.split(' · ')
      if (parts.length > 0 && parts[0].includes('m²')) {
        // Insérer l'étage après la surface
        parts.splice(1, 0, etage)
        return { ...baseInfo, subtitle: parts.join(' · ') }
      } else {
        // Ajouter l'étage au début si pas de surface
        return { ...baseInfo, subtitle: `${etage} · ${baseInfo.subtitle}` }
      }
    }
    return baseInfo
  }, [apartmentInfo, etage])
  
  // Calculer le mega score en utilisant la fonction utilitaire partagée
  const megaScore = useMemo(() => {
    return calculateMegaScore(apartment)
  }, [apartment])
  
  // Récupérer les photos
  const photos = useMemo(() => {
    const apartmentId = apartment.id
    const photoUrls = []
    
    // Chercher dans photos_v2
    // Note: En production, on pourrait avoir un endpoint API pour les photos
    // Pour l'instant, on utilise les URLs depuis les données scrapées
    if (apartment.photos && Array.isArray(apartment.photos)) {
      apartment.photos.forEach(photo => {
        const url = typeof photo === 'string' ? photo : photo.url
        if (url && !url.includes('logo') && !url.includes('Logo')) {
          // Convertir les URLs relatives en absolues si nécessaire
          if (url.startsWith('../')) {
            photoUrls.push(url.replace('../', '/'))
          } else if (!url.startsWith('http')) {
            photoUrls.push(`/data/photos/${apartmentId}/${url}`)
          } else {
            photoUrls.push(url)
          }
        }
      })
    }
    
    return photoUrls.slice(0, 10) // Limiter à 10 photos
  }, [apartment])
  
  const handleClick = () => {
    if (apartment.url) {
      window.open(apartment.url, '_blank')
    }
  }
  
  const carouselId = `carousel-${apartment.id}`
  
  return (
    <div className="scorecard" onClick={handleClick}>
      <Carousel photos={photos} carouselId={carouselId} score={megaScore} />
      <div className="apartment-info">
        <div className="apartment-title">{apartmentInfoWithEtage.title}</div>
        <div className="apartment-subtitle">{apartmentInfoWithEtage.subtitle}</div>
        
        {/* Critères */}
        {apartment.scores_detaille && (
          <>
            {apartment.scores_detaille.localisation && (
              <Criterion 
                name="Localisation"
                score={apartment.scores_detaille.localisation.score || 0}
                tier={apartment.scores_detaille.localisation.tier || 'tier3'}
                value={formatLocalisation(apartment)}
              />
            )}
            {apartment.scores_detaille.prix && (() => {
              const prixData = formatPrixCriterion(apartment)
              const tierLabel = prixData.tierLabel
              const tierClass = prixData.tierClass
              return (
                <Criterion 
                  name="Prix"
                  score={apartment.scores_detaille.prix.score || 0}
                  tier={apartment.scores_detaille.prix.tier || 'tier3'}
                  value={prixData.mainValue}
                  tierLabel={tierLabel}
                  tierClass={tierClass}
                />
              )
            })()}
            {apartment.scores_detaille.style && (
              <Criterion 
                name="Style"
                score={apartment.scores_detaille.style.score || 0}
                tier={apartment.scores_detaille.style.tier || 'tier3'}
                value={formatStyleCriterion(apartment)}
                confidence={apartment.style_analysis?.style?.confidence}
              />
            )}
            {apartment.scores_detaille.ensoleillement && (() => {
              const expoData = formatExpositionCriterion(apartment, etage)
              let tier = apartment.scores_detaille.ensoleillement.tier || 'tier3'
              
              // Vérifier la cohérence entre la valeur affichée et le tier
              // Si "Lumineux" est affiché, le tier doit être tier1
              if (expoData.mainValue === 'Lumineux' && tier !== 'tier1') {
                tier = 'tier1'
              } else if (expoData.mainValue === 'Luminosité moyenne' && tier !== 'tier2') {
                tier = 'tier2'
              } else if (expoData.mainValue === 'Sombre' && tier !== 'tier3') {
                tier = 'tier3'
              }
              
              // Calculer le score selon le tier pour garantir la cohérence
              // tier1 (Lumineux) = 20 pts, tier2 (Luminosité moyenne) = 10 pts, tier3 (Sombre) = 0 pts
              const scoreFromTier = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
              return (
                <Criterion 
                  name="Exposition"
                  score={scoreFromTier}
                  tier={tier}
                  value={expoData.mainValue}
                  indices={expoData.indices}
                  confidence={apartment.style_analysis?.luminosite?.confidence}
                />
              )
            })()}
            {apartment.scores_detaille.cuisine && (() => {
              const cuisineValue = apartment.style_analysis?.cuisine?.ouverte ? 'Ouverte' : 'Fermée'
              let tier = apartment.scores_detaille.cuisine.tier || 'tier3'
              
              // Vérifier la cohérence entre la valeur affichée et le tier
              // Si "Ouverte" est affiché, le tier doit être tier1 (10 pts)
              if (cuisineValue === 'Ouverte' && tier !== 'tier1') {
                tier = 'tier1'
              }
              // Si "Fermée" est affiché, le tier doit être tier3 (0 pts)
              if (cuisineValue === 'Fermée' && tier !== 'tier3') {
                tier = 'tier3'
              }
              
              // Calculer le score selon le tier pour garantir la cohérence
              // tier1 (Ouverte) = 10 pts, tier2 (Modifiable) = 5 pts, tier3 (Fermée) = 0 pts
              const scoreFromTier = tier === 'tier1' ? 10 : tier === 'tier2' ? 5 : 0
              return (
                <Criterion 
                  name="Cuisine ouverte"
                  score={scoreFromTier}
                  tier={tier}
                  value={cuisineValue}
                  confidence={apartment.style_analysis?.cuisine?.confidence}
                />
              )
            })()}
            {apartment.scores_detaille?.baignoire && (() => {
              const baignoireData = formatBaignoireCriterion(apartment)
              return (
                <Criterion 
                  name="Baignoire"
                  score={baignoireData.score}
                  tier={baignoireData.tier}
                  value={baignoireData.mainValue}
                  indices={baignoireData.indices}
                  confidence={baignoireData.confidence}
                />
              )
            })()}
          </>
        )}
      </div>
    </div>
  )
}

// Fonctions de formatage des critères
function formatLocalisation(apartment) {
  const metro = getMetroName(apartment)
  const quartier = getQuartierName(apartment)
  
  const parts = []
  if (metro) {
    parts.push(`Metro ${metro}`)
  }
  if (quartier) {
    parts.push(quartier)
  }
  
  return parts.length > 0 ? parts.join(' · ') : 'Non spécifié'
}

function formatPrixCriterion(apartment) {
  const prixM2Formatted = formatPrixM2(apartment)
  const tier = apartment.scores_detaille?.prix?.tier || 'tier3'
  
  let tierLabel = 'Bad'
  let tierClass = 'bad'
  if (tier === 'tier1') {
    tierLabel = 'Good'
    tierClass = 'good'
  } else if (tier === 'tier2') {
    tierLabel = 'Moyen'
    tierClass = 'moyen'
  }
  
  if (prixM2Formatted) {
    // Formater avec superscript pour m² et tier label séparés
    const prixM2Display = prixM2Formatted.replace('m²', 'm²')
    return {
      mainValue: prixM2Display,
      tierLabel,
      tierClass
    }
  }
  
  return {
    mainValue: 'Prix/m² non disponible',
    tierLabel,
    tierClass
  }
}

function formatStyleCriterion(apartment) {
  // Utiliser le tier du score détaillé pour déterminer Ancien / Atypique / Neuf
  const scoresDetaille = apartment.scores_detaille || {}
  const styleScore = scoresDetaille.style || {}
  const tier = styleScore.tier || 'tier3'
  
  // Si tier1 = Ancien (20pts), tier2 = Atypique (10pts), tier3 = Neuf (0pts)
  if (tier === 'tier1') {
    return 'Ancien'
  } else if (tier === 'tier2') {
    return 'Atypique'
  } else {
    return 'Neuf'
  }
}

function formatExpositionCriterion(apartment, etage) {
  const styleAnalysis = apartment.style_analysis || {}
  const luminositeData = styleAnalysis.luminosite || {}
  const luminositeType = luminositeData.type || ''
  
  let mainValue = 'Sombre'
  if (luminositeType.toLowerCase().includes('excellente')) {
    mainValue = 'Lumineux'
  } else if (luminositeType.toLowerCase().includes('bonne') || luminositeType.toLowerCase().includes('moyenne')) {
    mainValue = 'Luminosité moyenne'
  }
  
  // Ajouter l'étage comme indice
  const indices = []
  if (etage) {
    indices.push(etage)
  }
  
  // Ajouter exposition directionnelle si disponible
  const exposition = apartment.exposition || {}
  const expositionDir = exposition.exposition || ''
  if (expositionDir && !['inconnue', 'inconnu', 'non spécifiée'].includes(expositionDir.toLowerCase())) {
    indices.push(`Exposition ${expositionDir} détectée`)
  }
  
  return {
    mainValue,
    indices: indices.length > 0 ? indices.join(' · ') : null
  }
}

function formatBaignoireCriterion(apartment) {
  // Utiliser les scores depuis scores_detaille.baignoire
  const scoresDetaille = apartment.scores_detaille || {}
  const baignoireScore = scoresDetaille.baignoire || {}
  
  // Récupérer le score et le tier depuis scores_detaille
  const score = baignoireScore.score || 0
  const tier = baignoireScore.tier || 'tier3'
  const justification = baignoireScore.justification || ''
  
  // Chercher les données baignoire depuis différentes sources pour les détails
  const baignoireData = apartment.baignoire_data || apartment.baignoire || {}
  const hasBaignoire = baignoireData.has_baignoire || baignoireData.has_baignoire === true
  const hasDouche = baignoireData.has_douche || baignoireData.has_douche === true
  const confidence = baignoireData.confidence || baignoireScore.details?.photo_validation?.photo_confidence || 0
  
  // Valeur principale
  const mainValue = hasBaignoire ? 'Oui' : 'Non'
  
  // Calculer la confiance en pourcentage
  let confidencePct = null
  if (confidence !== null && confidence !== undefined) {
    if (typeof confidence === 'number' && confidence <= 1) {
      confidencePct = Math.round(confidence * 100)
    } else if (typeof confidence === 'number' && confidence <= 100) {
      confidencePct = Math.round(confidence)
    }
  }
  
  // Extraire les indices depuis justification ou details
  let indices = null
  if (justification) {
    const justificationLower = justification.toLowerCase()
    if (justificationLower.includes('photo') || justificationLower.includes('détectée') || justificationLower.includes('analysée')) {
      if (hasBaignoire) {
        indices = 'Analyse photo : Baignoire détectée'
      } else if (hasDouche) {
        indices = 'Analyse photo : Douche détectée'
      }
    } else if (justificationLower.includes('description') || justificationLower.includes('caractéristiques')) {
      if (hasBaignoire) {
        indices = 'Baignoire mentionnée dans le texte'
      } else if (hasDouche) {
        indices = 'Douche mentionnée dans le texte'
      }
    } else if (justification.length < 100) {
      indices = justification
    }
  }
  
  return {
    mainValue,
    confidence: confidencePct,
    indices,
    tier,
    score
  }
}

function Criterion({ name, score, tier, value, confidence, indices, tierLabel, tierClass }) {
  const badgeClass = tier === 'tier1' ? 'green' : tier === 'tier2' ? 'yellow' : 'red'
  
  // Si value est un objet (pour exposition), extraire mainValue et indices
  let displayValue = value
  let displayIndices = indices
  
  if (typeof value === 'object' && value !== null && value.mainValue) {
    displayValue = value.mainValue
    displayIndices = value.indices || null
  }
  
  return (
    <div className="criterion">
      <div className="criterion-content">
        <div className="criterion-name">{name}</div>
        <div className="criterion-details">
          {typeof displayValue === 'string' ? (
            <span dangerouslySetInnerHTML={{ __html: displayValue.replace(/m²/g, 'm<sup>2</sup>') }} />
          ) : (
            displayValue
          )}
          {tierLabel && (
            <>
              {' · '}
              <span className={`tier-label ${tierClass || 'bad'}`}>{tierLabel}</span>
            </>
          )}
          {confidence !== undefined && confidence !== null && (
            <span className="confidence-badge">
              {typeof confidence === 'number' && confidence <= 1 
                ? Math.round(confidence * 100) 
                : Math.round(confidence)}% confiance
            </span>
          )}
          {displayIndices && (
            <div className="criterion-sub-details">{displayIndices}</div>
          )}
        </div>
      </div>
      <span className={`criterion-score-badge ${badgeClass}`}>{score} pts</span>
    </div>
  )
}

export default ApartmentCard

