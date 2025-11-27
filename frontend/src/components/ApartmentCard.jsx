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

function ApartmentCard({ apartment, alertCriteria = null }) {
  // Debug: vérifier que alertCriteria est bien passé
  if (apartment?.alert_criteria_scores && !alertCriteria) {
    console.warn('⚠️ ApartmentCard: alert_criteria_scores présent mais alertCriteria est null!', {
      apartment_id: apartment.id,
      has_alert_criteria_scores: !!apartment.alert_criteria_scores,
      alertCriteria
    })
  }
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
    
    // Construire le subtitle: surface (étage sera ajouté après via useMemo)
    // Ne pas inclure le style
    const subtitleParts = [surfaceClean].filter(Boolean)
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
  
  // Calculer le score d'alerte en additionnant les 4 critères affichés
  const calculatedAlertScore = useMemo(() => {
    if (apartment.alert_criteria_scores && alertCriteria) {
      const alertCriteriaScores = apartment.alert_criteria_scores
      const primaryCriteria = alertCriteria.primary || []
      const secondaryCriteria = alertCriteria.secondary || []
      const allCriteriaNames = [...primaryCriteria, ...secondaryCriteria]
      
      // Additionner les scores des 4 critères
      let total = 0
      for (const criterionName of allCriteriaNames) {
        const criterionScore = alertCriteriaScores[criterionName]
        if (criterionScore && typeof criterionScore.score === 'number') {
          total += criterionScore.score
        }
      }
      return total
    }
    return null
  }, [apartment.alert_criteria_scores, alertCriteria])
  
  // Utiliser le score calculé (somme des critères) si disponible, sinon alert_score du backend, sinon megaScore
  const displayScore = useMemo(() => {
    if (calculatedAlertScore !== null) {
      return calculatedAlertScore
    }
    return apartment.alert_score !== undefined ? apartment.alert_score : megaScore
  }, [calculatedAlertScore, apartment.alert_score, megaScore])
  
  // maxScore: 100 pour alert_score, 90 pour megaScore
  const maxScore = useMemo(() => {
    return apartment.alert_score !== undefined ? 100 : 90
  }, [apartment.alert_score])
  
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
      <Carousel photos={photos} carouselId={carouselId} score={displayScore} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />
      <div className="apartment-info">
        <div className="apartment-title">{apartmentInfoWithEtage.title}</div>
        <div className="apartment-subtitle">{apartmentInfoWithEtage.subtitle}</div>
        
        {/* Critères */}
        {(() => {
          // Si c'est un résultat d'alerte, afficher d'abord les critères de l'alerte
          if (apartment.alert_criteria_scores && alertCriteria) {
            const alertCriteriaScores = apartment.alert_criteria_scores
            // Utiliser l'ordre depuis alertCriteria (primary puis secondary)
            const primaryCriteria = alertCriteria.primary || []
            const secondaryCriteria = alertCriteria.secondary || []
            const orderedAlertCriteriaNames = [...primaryCriteria, ...secondaryCriteria]
            // Filtrer pour ne garder que ceux qui ont des scores
            const alertCriteriaNames = orderedAlertCriteriaNames.filter(name => alertCriteriaScores[name])
            
            // Séparer les critères de l'alerte (top 4) et les autres
            const alertCriteriaSet = new Set(alertCriteriaNames)
            const otherCriteria = []
            
            // Récupérer les critères standards qui ne sont pas dans l'alerte
            if (apartment.scores_detaille) {
              const standardCriteria = {
                'localisation': { key: 'localisation', name: 'Localisation', alertKeys: ['quartier'] },
                'prix': { key: 'prix', name: 'Prix', alertKeys: ['prix'] },
                'style': { key: 'style', name: 'Style', alertKeys: ['haussmanien', 'neuf'] },
                'ensoleillement': { key: 'ensoleillement', name: 'Exposition', alertKeys: ['luminosite'] },
                'cuisine': { key: 'cuisine', name: 'Cuisine', alertKeys: ['cuisine_ouverte'] },
                'baignoire': { key: 'baignoire', name: 'Baignoire', alertKeys: ['baignoire'] }
              }
              
              // Vérifier quels critères standards ne sont pas dans l'alerte
              for (const [key, info] of Object.entries(standardCriteria)) {
                // Vérifier si un des critères d'alerte correspond à ce critère standard
                const isInAlert = info.alertKeys.some(alertKey => alertCriteriaSet.has(alertKey))
                
                if (!isInAlert) {
                  // Ce critère n'est pas dans l'alerte, l'ajouter aux autres
                  if (apartment.scores_detaille[key]) {
                    otherCriteria.push({ key, name: info.name })
                  }
                }
              }
            }
            
            return (
              <>
                {/* Afficher d'abord les critères de l'alerte (top 4) */}
                {alertCriteriaNames.map((alertCriterionName, alertIndex) => {
                  const criterionScore = alertCriteriaScores[alertCriterionName]
                  const displayName = ALERT_CRITERIA_TO_DISPLAY[alertCriterionName] || alertCriterionName
                  const tier = criterionScore?.tier || 'tier3'
                  const justification = criterionScore?.justification || ''
                  // Supprimer la bordure entre les critères de l'alerte (sauf le dernier s'il y a des autres critères)
                  const isLastAlertCriterion = alertIndex === alertCriteriaNames.length - 1
                  const noBorderBottom = !isLastAlertCriterion || otherCriteria.length === 0
                  
                  // Formater selon le type de critère
                  let customTitle = displayName
                  let customDescription = justification
                  
                  if (alertCriterionName === 'quartier' || alertCriterionName === 'localisation') {
                    const locData = formatLocalisation(apartment)
                    customTitle = locData.title || displayName
                    customDescription = locData.description || justification
                  } else if (alertCriterionName === 'prix') {
                    const prixData = formatPrixCriterion(apartment)
                    customTitle = prixData.title || displayName
                    customDescription = prixData.description || justification
                  } else if (alertCriterionName === 'haussmanien' || alertCriterionName === 'neuf') {
                    const styleData = formatStyleCriterion(apartment)
                    customTitle = styleData.title || displayName
                    customDescription = styleData.description || justification
                  } else if (alertCriterionName === 'luminosite') {
                    const expoData = formatExpositionCriterion(apartment, etage)
                    customTitle = expoData.title || displayName
                    customDescription = expoData.description || justification
                  } else if (alertCriterionName === 'cuisine_ouverte') {
                    const cuisineData = formatCuisineCriterion(apartment)
                    customTitle = cuisineData.title || displayName
                    customDescription = cuisineData.description || justification
                  } else if (alertCriterionName === 'baignoire') {
                    const baignoireData = formatBaignoireCriterion(apartment)
                    customTitle = baignoireData.title || displayName
                    customDescription = baignoireData.description || justification
                  } else {
                    // Critères simples (ascenseur, large_piece_vie, renove)
                    customTitle = displayName
                    customDescription = justification || 'Non spécifié'
                  }
                  
                  return (
                    <Criterion
                      key={alertCriterionName}
                      name={displayName}
                      score={criterionScore?.score || 0}
                      tier={tier}
                      customTitle={customTitle}
                      customDescription={customDescription}
                      alertCriterionName={alertCriterionName}
                      noBorderBottom={noBorderBottom}
                    />
                  )
                })}
                
                {/* Afficher ensuite les autres critères en gris */}
                {otherCriteria.map(({ key, name }, otherIndex) => {
                  const isLastOtherCriterion = otherIndex === otherCriteria.length - 1
                  const noBorderBottom = !isLastOtherCriterion
                  
                  if (key === 'localisation') {
                    const locData = formatLocalisation(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={apartment.scores_detaille.localisation.score || 0}
                        tier={apartment.scores_detaille.localisation.tier || 'tier3'}
                        customTitle={locData.title}
                        customDescription={locData.description}
                        descriptionClass={locData.descriptionClass}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'prix') {
                    const prixData = formatPrixCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={apartment.scores_detaille.prix.score || 0}
                        tier={apartment.scores_detaille.prix.tier || 'tier3'}
                        customTitle={prixData.title}
                        customDescription={prixData.description}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'style') {
                    const styleData = formatStyleCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={apartment.scores_detaille.style.score || 0}
                        tier={apartment.scores_detaille.style.tier || 'tier3'}
                        customTitle={styleData.title}
                        customDescription={styleData.description}
                        confidence={apartment.style_analysis?.style?.confidence}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'ensoleillement') {
                    const expoData = formatExpositionCriterion(apartment, etage)
                    let tier = apartment.scores_detaille.ensoleillement.tier || 'tier3'
                    const scoreFromTier = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={scoreFromTier}
                        tier={tier}
                        customTitle={expoData.title}
                        customDescription={expoData.description}
                        confidence={expoData.confidence}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'cuisine') {
                    const cuisineData = formatCuisineCriterion(apartment)
                    const cuisineScore = apartment.scores_detaille.cuisine || {}
                    const cuisineScoreValue = cuisineScore.score !== undefined ? cuisineScore.score : (cuisineData.tier === 'tier1' ? 10 : cuisineData.tier === 'tier2' ? 5 : 0)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={cuisineScoreValue}
                        tier={cuisineData.tier}
                        customTitle={cuisineData.title}
                        customDescription={cuisineData.description}
                        confidence={cuisineData.confidence}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'baignoire') {
                    const baignoireData = formatBaignoireCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={baignoireData.score}
                        tier={baignoireData.tier}
                        customTitle={baignoireData.title}
                        customDescription={baignoireData.description}
                        confidence={baignoireData.confidence}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  }
                  return null
                })}
              </>
            )
          }
          
          // Sinon, afficher les critères standards (comportement normal)
          return apartment.scores_detaille ? (
            <>
              {apartment.scores_detaille.localisation && (() => {
                const locData = formatLocalisation(apartment)
                return (
                  <Criterion 
                    name="Localisation"
                    score={apartment.scores_detaille.localisation.score || 0}
                    tier={apartment.scores_detaille.localisation.tier || 'tier3'}
                    customTitle={locData.title}
                    customDescription={locData.description}
                    descriptionClass={locData.descriptionClass}
                  />
                )
              })()}
              {apartment.scores_detaille.prix && (() => {
                const prixData = formatPrixCriterion(apartment)
                return (
                  <Criterion 
                    name="Prix"
                    score={apartment.scores_detaille.prix.score || 0}
                    tier={apartment.scores_detaille.prix.tier || 'tier3'}
                    customTitle={prixData.title}
                    customDescription={prixData.description}
                  />
                )
              })()}
              {apartment.scores_detaille.style && (() => {
                const styleData = formatStyleCriterion(apartment)
                return (
                  <Criterion 
                    name="Style"
                    score={apartment.scores_detaille.style.score || 0}
                    tier={apartment.scores_detaille.style.tier || 'tier3'}
                    customTitle={styleData.title}
                    customDescription={styleData.description}
                    confidence={apartment.style_analysis?.style?.confidence}
                  />
                )
              })()}
              {apartment.scores_detaille.ensoleillement && (() => {
                const expoData = formatExpositionCriterion(apartment, etage)
                let tier = apartment.scores_detaille.ensoleillement.tier || 'tier3'
                
                // Calculer le score selon le tier pour garantir la cohérence
                // tier1 (Lumineux) = 20 pts, tier2 (Luminosité moyenne) = 10 pts, tier3 (Sombre) = 0 pts
                const scoreFromTier = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
                return (
                  <Criterion 
                    name="Exposition"
                    score={scoreFromTier}
                    tier={tier}
                    customTitle={expoData.title}
                    customDescription={expoData.description}
                    confidence={expoData.confidence}
                  />
                )
              })()}
              {apartment.scores_detaille.cuisine && (() => {
                const cuisineData = formatCuisineCriterion(apartment)
                const cuisineScore = apartment.scores_detaille.cuisine || {}
                const cuisineScoreValue = cuisineScore.score !== undefined ? cuisineScore.score : (cuisineData.tier === 'tier1' ? 10 : cuisineData.tier === 'tier2' ? 5 : 0)
                
                return (
                  <Criterion 
                    name="Cuisine"
                    score={cuisineScoreValue}
                    tier={cuisineData.tier}
                    customTitle={cuisineData.title}
                    customDescription={cuisineData.description}
                    confidence={cuisineData.confidence}
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
                    customTitle={baignoireData.title}
                    customDescription={baignoireData.description}
                    confidence={baignoireData.confidence}
                  />
                )
              })()}
            </>
          ) : null
        })()}
      </div>
    </div>
  )
}

// Fonctions de formatage des critères
function formatLocalisation(apartment) {
  const quartier = getQuartierName(apartment)
  const mapInfo = apartment.map_info || {}
  const streets = mapInfo.streets || []
  
  // Construire le titre: "Quartier Belleville · 166 rue Saint Maur"
  const titleParts = []
  if (quartier) {
    titleParts.push(`Quartier ${quartier}`)
  }
  
  // Chercher une rue dans streets ou dans localisation
  let rue = null
  if (streets.length > 0) {
    rue = streets[0]
  } else {
    // Extraire la rue depuis localisation (format "166 rue Saint Maur" ou similaire)
    const localisation = apartment.localisation || ''
    const rueMatch = localisation.match(/(\d+\s*(?:rue|Rue|RUE|avenue|Avenue|AVENUE|boulevard|Boulevard|BOULEVARD|place|Place|PLACE)[^·,]*)/i)
    if (rueMatch) {
      rue = rueMatch[1].trim()
    }
  }
  
  if (rue) {
    titleParts.push(rue)
  }
  
  const title = titleParts.length > 0 ? titleParts.join(' · ') : 'Localisation'
  
  // Description selon le tier
  const tier = apartment.scores_detaille?.localisation?.tier || 'tier3'
  let description = null
  let descriptionClass = null
  
  if (tier === 'tier1') {
    description = 'Votre quartier idéal'
  } else {
    description = 'Quartier proche de vos criteres'
    // Pas de descriptionClass - gris comme les autres
  }
  
  return {
    title,
    description,
    descriptionClass
  }
}

function formatPrixCriterion(apartment) {
  const prixM2Formatted = formatPrixM2(apartment)
  const tier = apartment.scores_detaille?.prix?.tier || 'tier3'
  
  // Titre selon le tier
  let title = 'Prix'
  if (tier === 'tier1') {
    title = 'Prix en dessous du marché'
  } else if (tier === 'tier2') {
    title = 'Prix du marché'
  } else {
    title = 'Prix au dessus du marché'
  }
  
  // Description: prix/m² sans good/moyen/bad
  const description = prixM2Formatted || 'Prix/m² non disponible'
  
  return {
    title,
    description
  }
}

function formatStyleCriterion(apartment) {
  const styleAnalysis = apartment.style_analysis || {}
  const styleData = styleAnalysis.style || {}
  const styleType = styleData.type || ''
  
  // Titre: "Style haussmanien" (ou autre style)
  let title = 'Style'
  if (styleType && styleType !== 'autre' && styleType !== 'inconnu') {
    let styleName = styleType.charAt(0).toUpperCase() + styleType.slice(1)
    
    // Gérer les cas spéciaux
    if (styleType.includes('70') || styleType.toLowerCase().includes('seventies')) {
      styleName = "70s"
    } else if (styleType.toLowerCase().includes('haussmann')) {
      styleName = "Haussmannien"
    }
    
    title = `Style ${styleName}`
  }
  
  // Description: "Construction X (si date dispo) + indices (moulures · parquet..)"
  const descriptionParts = []
  
  // Année de construction
  const caracteristiques = apartment.caracteristiques || {}
  const anneeConstruction = caracteristiques.annee_construction || apartment.annee_construction
  if (anneeConstruction) {
    descriptionParts.push(`Construction ${anneeConstruction}`)
  }
  
  // Indices du style (moulures, cheminée, etc.)
  const details = styleData.details || ''
  const justification = styleData.justification || ''
  const textToSearch = `${details} ${justification}`.toLowerCase()
  
  const keywords = []
  if (textToSearch.includes('moulures') || textToSearch.includes('moldings')) {
    keywords.push('Moulures')
  }
  if (textToSearch.includes('cheminée') || textToSearch.includes('fireplace')) {
    keywords.push('Cheminée')
  }
  if (textToSearch.includes('parquet')) {
    keywords.push('Parquet')
  }
  if (textToSearch.includes('hauteur sous plafond')) {
    keywords.push('Hauteur sous plafond')
  }
  
  // Utiliser les indices depuis formatted_data si disponibles
  let styleIndices = apartment.formatted_data?.style?.indices
  if (styleIndices && styleIndices !== 'Style expo cuisine et baignoire') {
    // Extraire les détails depuis les indices
    let indicesClean = styleIndices
      .replace(/^Style Indice:\n?/i, '')
      .replace(/^Style:\n?/i, '')
      .replace(/Style\s+(?:haussmannien|neuf|atypique|70s|autre|inconnu)[\s·,]*/gi, '') // Retirer "Style haussmannien" ou similaire
      .replace(/\([^)]*construction[^)]*\)/gi, '') // Retirer les parenthèses avec "construction"
      .trim()
    
    if (indicesClean && !indicesClean.includes('Non spécifié') && indicesClean.length > 0) {
      descriptionParts.push(indicesClean)
    } else if (keywords.length > 0) {
      descriptionParts.push(keywords.join(' · '))
    }
  } else if (keywords.length > 0) {
    descriptionParts.push(keywords.join(' · '))
  }
  
  const description = descriptionParts.length > 0 ? descriptionParts.join(' · ') : null
  
  return {
    title,
    description
  }
}

function formatExpositionCriterion(apartment, etage) {
  // Utiliser les données formatées depuis le backend si disponibles
  let mainValue = 'Sombre'
  let indices = null
  let confidence = null
  
  if (apartment.formatted_data?.exposition) {
    mainValue = apartment.formatted_data.exposition.main_value || 'Sombre'
    indices = apartment.formatted_data.exposition.indices || null
    // Nettoyer le préfixe "Exposition Indice:" ou "exposition indice:" si présent
    if (indices && typeof indices === 'string') {
      indices = indices
        .replace(/^Exposition Indice:\s*/i, '')
        .replace(/^Exposition indice:\s*/i, '')
        .replace(/^exposition indice:\s*/i, '')
        .replace(/^Expo Indice:\s*/i, '')
        .replace(/^\n+/, '')
        .trim()
    }
    confidence = apartment.formatted_data.exposition.confidence || null
  } else {
    // Fallback: utiliser directement apartment.exposition si disponible
    const exposition = apartment.exposition || {}
    const expositionDir = exposition.exposition || ''
    
    // Classifier l'orientation pour déterminer mainValue
    if (expositionDir) {
      const expoNormalized = expositionDir.toLowerCase().replace(/[_\s-]/g, '')
      // Lumineux: sud, sudouest, sudest
      if (expoNormalized === 'sud' || expoNormalized === 'sudouest' || expoNormalized === 'sudest') {
        mainValue = 'Lumineux'
      }
      // Sombre: nord, nordouest, nordest
      else if (expoNormalized === 'nord' || expoNormalized === 'nordouest' || expoNormalized === 'nordest') {
        mainValue = 'Sombre'
      }
      // Moyen: est, ouest (déjà la valeur par défaut)
    }
    
    // Si pas d'exposition directionnelle, essayer style_analysis
    if (!expositionDir) {
      const styleAnalysis = apartment.style_analysis || {}
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
    
    // Construire les indices (ordre: étage, vis-à-vis)
    const indicesArray = []
    if (etage) {
      indicesArray.push(etage)
    }
    
    // Ajouter vis-à-vis si disponible
    const visavisDistance = exposition.details?.visavis_distance
    if (visavisDistance !== null && visavisDistance !== undefined) {
      indicesArray.push(`vis a vis ${visavisDistance} m`)
    }
    
    indices = indicesArray.length > 0 ? indicesArray.join(' · ') : null
    confidence = exposition.confidence || null
  }
  
  // Titre: "Bonne luminosité" (ou "Luminosité moyenne" / "Faible luminosité")
  let title = 'Exposition'
  if (mainValue === 'Lumineux') {
    title = 'Bonne luminosité'
  } else if (mainValue === 'Luminosité moyenne') {
    title = 'Luminosité moyenne'
  } else {
    title = 'Faible luminosité'
  }
  
  // Description: "3e etage · vis a vis X m"
  const description = indices
  
  return {
    title,
    description,
    confidence
  }
}

function formatCuisineCriterion(apartment) {
  // Vérifier que scores_detaille existe
  if (!apartment.scores_detaille) {
    return {
      title: 'Cuisine',
      description: 'Non analysée',
      tier: 'tier3',
      confidence: null
    }
  }
  
  // PRIORITÉ: Utiliser le résultat final depuis scores_detaille (après validation croisée texte + photos)
  const cuisineScore = apartment.scores_detaille.cuisine || {}
  const cuisineDetails = cuisineScore.details || {}
  const photoValidation = cuisineDetails.photo_validation || {}
  const validationStatus = cuisineDetails.validation_status || ''
  
  // Chercher la valeur depuis photo_result (résultat final après validation)
  let cuisineOuverte = null
  if (photoValidation.photo_result) {
    // Si pas de conflit, utiliser photo_result.ouverte
    // Si conflit, le tier représente le résultat final (texte peut gagner)
    if (validationStatus !== 'conflict') {
      cuisineOuverte = photoValidation.photo_result.ouverte
    }
  }
  
  // Fallback: utiliser style_analysis si pas trouvé
  if (cuisineOuverte === null || cuisineOuverte === undefined) {
    cuisineOuverte = apartment.style_analysis?.cuisine?.ouverte
  }
  
  let tier = cuisineScore.tier || 'tier3'
  
  // Titre: "Cuisine ouverte" ou "Cuisine fermée"
  let title = 'Cuisine'
  if (tier === 'tier2') {
    title = 'Cuisine'
  } else {
    // Si toujours None OU si conflit, vérifier le tier pour déduire (tier = résultat final après validation)
    if (cuisineOuverte === null || cuisineOuverte === undefined || validationStatus === 'conflict') {
      // tier1 = ouverte (10pts), tier3 = fermée (0pts)
      // En cas de conflit, le tier représente le résultat final après validation croisée
      cuisineOuverte = (tier === 'tier1')
    }
    
    title = cuisineOuverte ? 'Cuisine ouverte' : 'Cuisine fermée'
  }
  
  // Description: "Detectee en image 7"
  let description = null
  
  // Chercher les photos détectées
  const detectedPhotos = photoValidation.photo_result?.detected_photos || []
  if (detectedPhotos.length > 0) {
    const photoNum = detectedPhotos[0]
    description = `Detectee en image ${photoNum}`
  } else {
    // Fallback: utiliser les indices depuis formatted_data
    const cuisineIndices = apartment.formatted_data?.cuisine?.indices
    if (cuisineIndices && cuisineIndices !== 'Style expo cuisine et baignoire') {
      // Extraire le numéro d'image depuis les indices
      const imageMatch = cuisineIndices.match(/image\s*(\d+)/i)
      if (imageMatch) {
        description = `Detectee en image ${imageMatch[1]}`
      }
    }
  }
  
  // Récupérer la confiance depuis cuisineDetails ou style_analysis
  const confidence = cuisineDetails.confidence || apartment.style_analysis?.cuisine?.confidence
  
  return {
    title,
    description,
    tier,
    confidence
  }
}

function formatBaignoireCriterion(apartment) {
  // PRIORITÉ: Utiliser formatted_data depuis le backend (comme pour cuisine)
  // Récupérer les indices depuis formatted_data (backend) en priorité
  let indices = apartment.formatted_data?.baignoire?.indices || null
  
  // Utiliser les scores depuis scores_detaille.baignoire
  const scoresDetaille = apartment.scores_detaille || {}
  const baignoireScore = scoresDetaille.baignoire || {}
  const baignoireDetails = baignoireScore.details || {}
  const photoValidation = baignoireDetails.photo_validation || {}
  const photoResult = photoValidation.photo_result || {}
  
  // Récupérer le score et le tier depuis scores_detaille
  const score = baignoireScore.score || 0
  const tier = baignoireScore.tier || 'tier3'
  
  // Chercher les données baignoire depuis différentes sources pour les détails
  const baignoireData = apartment.baignoire_data || apartment.baignoire || {}
  const hasBaignoire = baignoireData.has_baignoire || baignoireData.has_baignoire === true
  const confidence = baignoireData.confidence || baignoireScore.details?.confidence || 0
  
  // Vérifier si des photos ont été analysées
  const photosAnalyzed = photoResult.has_baignoire !== undefined || photoResult.has_douche !== undefined
  const detectedPhotos = photoResult.detected_photos || []
  const photoHasBaignoire = photoResult.has_baignoire
  const photoHasDouche = photoResult.has_douche
  
  // Valeur principale - utiliser formatted_data si disponible, sinon déduire depuis hasBaignoire ou tier
  let mainValue = apartment.formatted_data?.baignoire?.main_value
  if (!mainValue) {
    // Si tier2 = non analysée (note moyenne par défaut) → afficher "Non spécifié"
    if (tier === 'tier2') {
      mainValue = 'Non spécifié'
    } else {
      mainValue = hasBaignoire ? 'Oui' : 'Non'
    }
  }
  
  // Calculer la confiance en pourcentage
  let confidencePct = apartment.formatted_data?.baignoire?.confidence
  if (confidencePct === null || confidencePct === undefined) {
    if (confidence !== null && confidence !== undefined) {
      if (typeof confidence === 'number' && confidence <= 1) {
        confidencePct = Math.round(confidence * 100)
      } else if (typeof confidence === 'number' && confidence <= 100) {
        confidencePct = Math.round(confidence)
      }
    }
  }
  
  // Titre: "Baignoire" ou "Baignoire non spécifiée" si pas trouvée
  let title = 'Baignoire'
  let description = null
  
  // Si pas de baignoire trouvée (tier2 ou tier3 sans baignoire)
  if (tier === 'tier2' || (tier === 'tier3' && !hasBaignoire && !photoHasBaignoire)) {
    title = 'Baignoire non spécifiée'
    description = 'info non disponible'
  } else {
    // Construire les indices avec distinction claire entre "information non disponible" et "trouvé dans image X"
    if (!indices || indices === 'Style expo cuisine et baignoire') {
      if (photosAnalyzed && detectedPhotos.length > 0) {
        // Photos analysées et quelque chose détecté
        const photosStr = detectedPhotos.map(p => `image ${p}`).join(', ')
        if (photoHasBaignoire === true) {
          description = `Baignoire trouvée dans ${photosStr}`
        } else if (photoHasDouche === true) {
          description = `Douche trouvée dans ${photosStr}`
        } else {
          description = 'info non disponible'
        }
      } else if (photosAnalyzed) {
        // Photos analysées mais rien détecté
        description = 'info non disponible'
      } else {
        // Pas de photos analysées
        const justification = baignoireScore.justification || ''
        if (justification) {
          const justificationLower = justification.toLowerCase()
          if (justificationLower.includes('photo') || justificationLower.includes('détectée') || justificationLower.includes('analysée')) {
            if (hasBaignoire) {
              description = 'Analyse photo : Baignoire détectée'
            } else {
              description = 'Analyse photo : Douche détectée'
            }
          } else if (justificationLower.includes('description') || justificationLower.includes('caractéristiques')) {
            if (hasBaignoire) {
              description = 'Baignoire mentionnée dans le texte'
            } else {
              description = 'Douche mentionnée dans le texte'
            }
          } else if (justification.length < 100) {
            description = justification
          } else {
            description = 'info non disponible'
          }
        } else {
          description = 'info non disponible'
        }
      }
    } else {
      // Nettoyer les indices existants pour enlever les préfixes
      let cleanedIndices = indices
        .replace(/^Baignoire Indice:\n?/i, '')
        .replace(/^Baignoire:\n?/i, '')
        .trim()
      
      // Si les indices contiennent "Non spécifié", remplacer par "info non disponible"
      if (cleanedIndices.toLowerCase().includes('non spécifié')) {
        description = 'info non disponible'
      } else {
        // Si les indices contiennent "détectée" mais pas de numéro d'image, essayer d'ajouter les numéros
        if (cleanedIndices.includes('détectée') && !cleanedIndices.includes('image') && detectedPhotos.length > 0) {
          const photosStr = detectedPhotos.map(p => `image ${p}`).join(', ')
          if (cleanedIndices.includes('Baignoire')) {
            description = `Baignoire trouvée dans ${photosStr}`
          } else if (cleanedIndices.includes('Douche')) {
            description = `Douche trouvée dans ${photosStr}`
          } else {
            description = cleanedIndices
          }
        } else {
          description = cleanedIndices
        }
      }
    }
  }
  
  return {
    title,
    description,
    tier,
    score,
    confidence: confidencePct
  }
}

// Mapping des critères vers leurs emojis
const CRITERION_EMOJIS = {
  'Localisation': '📍',
  'Prix': '💰',
  'Style': '🎨',
  'Exposition': '☀️',
  'Cuisine': '👨‍🍳',
  'Baignoire': '🛁'
}

// Mapping des critères d'alerte vers les critères affichés
const ALERT_CRITERIA_TO_DISPLAY = {
  'haussmanien': 'Style',
  'neuf': 'Style',
  'quartier': 'Localisation',
  'prix': 'Prix',
  'luminosite': 'Exposition',
  'cuisine_ouverte': 'Cuisine',
  'ascenseur': 'Ascenseur',
  'large_piece_vie': 'Pièce de vie',
  'renove': 'Rénové',
  'baignoire': 'Baignoire'
}

// Mapping des emojis pour les critères d'alerte
const ALERT_CRITERIA_EMOJIS = {
  'haussmanien': '🔑',
  'neuf': '✨',
  'quartier': '📍',
  'prix': '💰',
  'luminosite': '☀️',
  'cuisine_ouverte': '👨‍🍳',
  'ascenseur': '🛗',
  'large_piece_vie': '🛋️',
  'renove': '🔨',
  'baignoire': '🛁'
}

function Criterion({ name, score, tier, value, confidence, indices, tierLabel, tierClass, customTitle, customDescription, descriptionClass, isGray = false, alertCriterionName = null, noBorderBottom = false, noBorderTop = false }) {
  const badgeClass = tier === 'tier1' ? 'green' : tier === 'tier2' ? 'yellow' : 'red'
  // Utiliser l'emoji du critère d'alerte si fourni, sinon l'emoji standard
  const emoji = alertCriterionName && ALERT_CRITERIA_EMOJIS[alertCriterionName] 
    ? ALERT_CRITERIA_EMOJIS[alertCriterionName] 
    : CRITERION_EMOJIS[name] || '📋'
  
  // Si value est un objet (pour exposition), extraire mainValue et indices
  let displayValue = value
  let displayIndices = indices
  
  if (typeof value === 'object' && value !== null && value.mainValue) {
    displayValue = value.mainValue
    displayIndices = value.indices || null
  }
  
  // Utiliser customTitle si fourni, sinon utiliser name
  const title = customTitle || name
  // Utiliser customDescription si fourni, sinon utiliser displayValue
  const description = customDescription !== undefined ? customDescription : displayValue
  
  // Construire les classes CSS
  const criterionClasses = ['criterion']
  if (isGray) criterionClasses.push('criterion-gray')
  if (noBorderBottom) criterionClasses.push('criterion-no-border-bottom')
  if (noBorderTop) criterionClasses.push('criterion-no-border-top')
  
  return (
    <div className={criterionClasses.join(' ')}>
      <div className="criterion-content">
        <div className="criterion-header">
          <span className={`criterion-emoji ${isGray ? 'gray' : badgeClass}`}>{emoji}</span>
          <div className="criterion-text-wrapper">
            <div className="criterion-name">{title}</div>
            {description && (
              <div className={`criterion-description ${descriptionClass ? `criterion-description-${descriptionClass}` : ''}`}>
                {typeof description === 'string' ? (
                  <span dangerouslySetInnerHTML={{ __html: description.replace(/m²/g, 'm<sup>2</sup>') }} />
                ) : (
                  description
                )}
                {/* Indice de confiance caché pour l'instant */}
              </div>
            )}
            {displayIndices && (
              <div className="criterion-sub-details">
                <div className="indices-icon-wrapper">
                  <svg 
                    className="indices-icon" 
                    width="16" 
                    height="16" 
                    viewBox="0 0 16 16" 
                    fill="none" 
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M11.5474 5.63862C11.5474 3.63498 9.91239 2 7.90875 2C5.9051 2 4.27012 3.63498 4.27012 5.63862C4.27012 5.92714 4.30218 6.21566 4.38233 6.50419C4.47851 6.96903 4.65483 7.25756 4.89527 7.65829C4.94335 7.75446 5.00747 7.85064 5.07158 7.96285C5.15173 8.09108 5.21585 8.21931 5.29599 8.33152C5.61658 8.86048 5.80893 9.16504 5.80893 9.79017V11.2969C5.80893 11.6816 6.08143 11.9862 6.4501 12.0503C6.61039 12.8678 7.09126 13.3807 7.90875 13.3807C8.72623 13.3807 9.22313 12.8678 9.3674 12.0503C9.73607 11.9862 10.0086 11.6656 10.0086 11.2969V9.79017C10.0086 9.16504 10.2009 8.84445 10.5215 8.33152C10.5856 8.21931 10.6658 8.09108 10.7459 7.96285C10.81 7.85064 10.8741 7.75446 10.9222 7.65829C11.1627 7.25756 11.339 6.96903 11.4352 6.50419C11.5153 6.21566 11.5474 5.92714 11.5474 5.63862ZM9.38343 10.1749H6.46612V9.8062C6.46612 9.72605 6.46613 9.66193 6.4501 9.59781H9.38343C9.38343 9.66193 9.3674 9.72605 9.3674 9.8062V10.1749H9.38343ZM9.23916 11.4412H6.57833C6.49818 11.4412 6.4501 11.3771 6.4501 11.3129V10.816H9.3674V11.3129C9.38342 11.3771 9.31931 11.4412 9.23916 11.4412ZM7.90875 12.7556C7.73242 12.7556 7.28361 12.7556 7.10729 12.0823H8.72623C8.54991 12.7556 8.08507 12.7556 7.90875 12.7556ZM10.81 6.37596C10.7299 6.7286 10.6016 6.96904 10.3772 7.33771C10.3131 7.43388 10.265 7.53006 10.2009 7.64226C10.1208 7.7705 10.0567 7.89872 9.99254 7.9949C9.80019 8.31548 9.62387 8.60401 9.51166 8.94062H6.33789C6.22569 8.60401 6.06539 8.31548 5.85702 7.9949C5.7929 7.88269 5.71275 7.7705 5.64864 7.64226C5.58452 7.53006 5.5204 7.41785 5.47231 7.33771C5.2479 6.95301 5.11967 6.7286 5.03952 6.35993C4.97541 6.11949 4.94335 5.87906 4.94335 5.63862C4.94335 3.98762 6.2898 2.64117 7.94081 2.64117C9.59181 2.64117 10.9383 3.98762 10.9383 5.63862C10.9062 5.87906 10.8741 6.11949 10.81 6.37596Z" fill="#7B7F87"/>
                  </svg>
                </div>
                <div className="indices-text-wrapper">
                  <span className="indices-text">
                    {displayIndices
                      .replace(/^Style Indice:\n?/, '')
                      .replace(/^Expo Indice:\n?/, '')
                      .replace(/^Exposition Indice:\n?/, '')
                      .replace(/^Cuisine Indice:\n?/, '')
                      .replace(/^Baignoire Indice:\n?/, '')
                      .replace(/^Baignoire:\n?/, '')}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      {/* <span className={`criterion-score-badge ${badgeClass}`}>{score} pts</span> */}
    </div>
  )
}

export default ApartmentCard


