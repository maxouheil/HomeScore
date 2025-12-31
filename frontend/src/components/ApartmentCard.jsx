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

// Fonction helper pour arrondir
function round(value, decimals) {
  return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals)
}

function ApartmentCard({ apartment, alertCriteria = null, showScore = true }) {
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
    
    // Formater le titre: "750k · Belleville" (métro en priorité) ou "750k · Combat" (quartier en fallback)
    let title = 'Appartement'
    if (prixK && metro) {
      title = `${prixK} · ${metro}`
    } else if (prixK && quartier) {
      title = `${prixK} · ${quartier}`
    } else if (prixK) {
      // Extraire l'arrondissement de la localisation
      const arrMatch = localisation.match(/Paris (\d+e)/)
      if (arrMatch) {
        title = `${prixK} · Paris ${arrMatch[1]}`
      } else {
        title = `${prixK} · ${localisation}`
      }
    } else if (metro) {
      title = metro
    } else if (quartier) {
      title = quartier
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
  
  // Extraire la distance vis-à-vis avec catégorie
  const visavisDistance = useMemo(() => {
    // Priorité 1: depuis exposition.details.visavis_distance et visavis_category
    const exposition = apartment.exposition || {}
    const visavisDist = exposition.details?.visavis_distance
    const visavisCategory = exposition.details?.visavis_category
    
    // Fonction pour traduire la catégorie en français
    const translateCategory = (cat) => {
      if (cat === 'good') return 'bon'
      if (cat === 'moyen') return 'moyen'
      if (cat === 'bad') return 'mauvais'
      return cat
    }
    
    // Si on a distance ET catégorie, formater avec catégorie
    if (visavisDist !== null && visavisDist !== undefined && visavisDist !== '') {
      if (visavisCategory) {
        const categoryFr = translateCategory(visavisCategory)
        return `Vis a vis ${categoryFr} (${visavisDist}m)`
      } else {
        // Pas de catégorie, juste la distance
        return `Vis a vis ${visavisDist}m`
      }
    }
    
    // Priorité 2: extraire depuis formatted_data.exposition.indices si disponible
    if (apartment.formatted_data?.exposition?.indices) {
      const indices = apartment.formatted_data.exposition.indices
      // Chercher différents formats: "vis a vis Xm", "vis-à-vis Xm", "Vis-à-vis Xm"
      const visavisMatch = indices.match(/vis[-\sà]?[aà][-\sà]?vis\s+(\d+)\s*m/i)
      if (visavisMatch) {
        return `Vis a vis ${visavisMatch[1]}m`
      }
    }
    
    return null
  }, [apartment])
  
  // Mettre à jour le subtitle pour inclure l'étage et le vis-à-vis
  const apartmentInfoWithEtage = useMemo(() => {
    const baseInfo = apartmentInfo
    const subtitleParts = []
    
    // Extraire la surface depuis le subtitle original ou depuis apartment.surface
    const parts = baseInfo.subtitle.split(' · ')
    const surfacePart = parts.find(p => p.includes('m²'))
    if (surfacePart) {
      subtitleParts.push(surfacePart)
    } else {
      // Fallback: extraire depuis apartment.surface
      const surface = apartment.surface || ''
      const surfaceMatch = surface.match(/(\d+)\s*m²/)
      if (surfaceMatch) {
        subtitleParts.push(`${surfaceMatch[1]} m²`)
      }
    }
    
    // Ajouter l'étage si disponible (formater correctement: 1er au lieu de 1e)
    if (etage) {
      let etageFormatted = etage
      // Convertir "1e étage" en "1er étage"
      if (etage.match(/^1e\s*étage$/i)) {
        etageFormatted = '1er étage'
      }
      subtitleParts.push(etageFormatted)
    }
    
    // Ajouter le vis-à-vis après l'étage si disponible
    if (visavisDistance) {
      subtitleParts.push(visavisDistance)
    }
    
    // Si on a des parties, les joindre, sinon utiliser le subtitle original
    if (subtitleParts.length > 0) {
      return { ...baseInfo, subtitle: subtitleParts.join(' · ') }
    }
    
    return baseInfo
  }, [apartmentInfo, etage, visavisDistance, apartment])
  
  // Calculer le mega score en utilisant la fonction utilitaire partagée
  const megaScore = useMemo(() => {
    return calculateMegaScore(apartment)
  }, [apartment])
  
  // Calculer le score d'alerte en additionnant les 5 critères affichés
  const calculatedAlertScore = useMemo(() => {
    if (apartment.alert_criteria_scores) {
      const alertCriteriaScores = apartment.alert_criteria_scores
      
      // Si alertCriteria est fourni, utiliser l'ordre des critères depuis l'alerte
      // Sinon, utiliser toutes les clés de alert_criteria_scores
      let allCriteriaNames = []
      if (alertCriteria) {
        // Support nouveau format (all) et ancien format (primary/secondary) pour compatibilité
        allCriteriaNames = alertCriteria.all || [...(alertCriteria.primary || []), ...(alertCriteria.secondary || [])]
      } else {
        // Utiliser toutes les clés de alert_criteria_scores
        allCriteriaNames = Object.keys(alertCriteriaScores)
      }
      
      // Additionner les scores des critères (5 critères à 1pt chacun max = 5pts max)
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
    // DEBUG: Log pour comprendre le problème
    console.log(`🔍 ApartmentCard ${apartment.id}:`, {
      has_alert_criteria_scores: !!apartment.alert_criteria_scores,
      has_alert_score: apartment.alert_score !== undefined,
      alert_score: apartment.alert_score,
      has_alert_tier: !!apartment.alert_tier,
      calculatedAlertScore,
      has_alertCriteria: !!alertCriteria
    })
    
    // PRIORITÉ ABSOLUE: Si on a alert_criteria_scores, TOUJOURS utiliser le calcul local (sur 5)
    // C'est la source de vérité car elle contient les scores individuels à jour (1pt, 0.5pt, 0pt)
    if (calculatedAlertScore !== null && calculatedAlertScore !== undefined) {
      // DEBUG: Vérifier que le score calculé est bien sur 5
      if (calculatedAlertScore > 5) {
        console.warn(`⚠️ ApartmentCard: calculatedAlertScore ${calculatedAlertScore} > 5 pour appartement ${apartment.id}`)
      }
      console.log(`✅ ApartmentCard ${apartment.id}: Utilisation calculatedAlertScore = ${calculatedAlertScore}`)
      return calculatedAlertScore
    }
    
    // Si on a alert_criteria_scores mais que calculatedAlertScore est null, 
    // c'est qu'il y a un problème avec le calcul. On recalcule manuellement.
    if (apartment.alert_criteria_scores) {
      const alertCriteriaScores = apartment.alert_criteria_scores
      let total = 0
      for (const criterionName in alertCriteriaScores) {
        const criterionScore = alertCriteriaScores[criterionName]
        if (criterionScore && typeof criterionScore.score === 'number') {
          total += criterionScore.score
        }
      }
      if (total > 0 || total === 0) { // Afficher même si 0
        console.log(`✅ ApartmentCard ${apartment.id}: Utilisation recalcul manuel = ${round(total, 2)}`)
        return round(total, 2)
      }
    }
    
    // Si on a alert_score, utiliser directement alert_score du backend (PRIORITÉ ABSOLUE)
    // Le backend renvoie maintenant toujours sur 5
    // Ne pas vérifier alertCriteria ici - si alert_score existe, c'est qu'on est dans une vue d'alerte
    if (apartment.alert_score !== undefined) {
      // DEBUG: Vérifier que le score est bien sur 5
      if (apartment.alert_score > 5) {
        console.warn(`⚠️ ApartmentCard: alert_score ${apartment.alert_score} > 5 pour appartement ${apartment.id}, conversion nécessaire`)
        // Ancien système (sur 100), convertir en divisant par 20
        const converted = round(apartment.alert_score / 20, 2)
        console.log(`✅ ApartmentCard ${apartment.id}: Utilisation alert_score converti = ${converted}`)
        return converted
      }
      // Sinon, c'est déjà sur 5 (ou moins)
      console.log(`✅ ApartmentCard ${apartment.id}: Utilisation alert_score direct = ${apartment.alert_score}`)
      return apartment.alert_score
    }
    
    // Si aucune alerte n'est sélectionnée (pas d'alertCriteria passé en prop), ne pas afficher de score
    // Sur la page d'accueil sans critères sélectionnés, les appartements ne doivent pas avoir de mega score
    if (!alertCriteria) {
      console.log(`❌ ApartmentCard ${apartment.id}: Pas d'alertCriteria, retour undefined`)
      return undefined
    }
    
    // Sinon, utiliser megaScore (score standard) - SEULEMENT si ce n'est PAS une alerte
    // Si on est dans la vue Alertes, on ne devrait jamais arriver ici
    console.log(`✅ ApartmentCard ${apartment.id}: Utilisation megaScore = ${megaScore}`)
    return megaScore
  }, [calculatedAlertScore, apartment.alert_score, apartment.alert_criteria_scores, apartment.alert_tier, apartment.id, megaScore, alertCriteria])
  
  // maxScore: 5 pour alert_score (si alert_criteria_scores, alert_tier ou alert_score présent), 90 pour megaScore
  const maxScore = useMemo(() => {
    // Si on a des critères d'alerte, un tier d'alerte, ou un alert_score, c'est une alerte (score sur 5)
    if (apartment.alert_criteria_scores || apartment.alert_tier || apartment.alert_score !== undefined) {
      // DEBUG: Vérifier que maxScore est bien 5
      if (apartment.alert_score !== undefined && apartment.alert_score > 5) {
        console.warn(`⚠️ ApartmentCard: alert_score ${apartment.alert_score} > 5 mais maxScore devrait être 5 pour appartement ${apartment.id}`)
      }
      return 5
    }
    // Sinon, c'est un score standard (megaScore sur 90)
    return megaScore !== undefined ? 90 : 90
  }, [apartment.alert_criteria_scores, apartment.alert_tier, apartment.alert_score, apartment.id, megaScore])
  
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
      <Carousel photos={photos} carouselId={carouselId} score={showScore ? displayScore : undefined} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />
      <div className="apartment-info">
        <div className="apartment-title">{apartmentInfoWithEtage.title}</div>
        <div className="apartment-subtitle">{apartmentInfoWithEtage.subtitle}</div>
        
        {/* Critères */}
        {(() => {
          // Dans la vue "all apartments" (showScore={false}), vérifier les données enrichies
          if (!showScore) {
            // Vérifier si l'appartement a des données enrichies (formatted_data)
            const formattedData = apartment.formatted_data || {}
            const hasEnrichedData = Object.keys(formattedData).length > 0 && 
                                   Object.values(formattedData).some(data => 
                                     data && (data.indices || data.main_value)
                                   )
            
            // Si pas de données enrichies, afficher les données manuelles par défaut
            if (!hasEnrichedData) {
              const manualCriteria = formatManualDataCriteria(apartment, etage)
              return (
                <>
                  {manualCriteria.map((criterion, index) => (
                    <Criterion
                      key={criterion.name}
                      name={criterion.name}
                      score={0}
                      tier="tier3"
                      customTitle={criterion.title}
                      customDescription={criterion.description}
                      indices={criterion.indices}
                      isGray={true}
                      noBorderBottom={index < manualCriteria.length - 1}
                    />
                  ))}
                </>
              )
            }
            
            // Sinon, afficher les critères formatés même sans score
            // (le code continue après cette condition)
          }
          
          // Vérifier si l'appartement a un score (pour les vues avec score)
          const hasScore = apartment.alert_score !== undefined || 
                           apartment.alert_criteria_scores || 
                           apartment.scores_detaille
          
          // Si pas de score ET qu'on affiche les scores, afficher "Appartement sans score"
          if (showScore && !hasScore) {
            return (
              <div style={{
                padding: '16px',
                textAlign: 'center',
                color: '#666',
                fontSize: '14px',
                fontStyle: 'italic',
                borderTop: '1px solid #eee'
              }}>
                Appartement sans score
              </div>
            )
          }
          
          // Si c'est un résultat d'alerte, afficher d'abord les critères de l'alerte
          if (apartment.alert_criteria_scores && alertCriteria) {
            const alertCriteriaScores = apartment.alert_criteria_scores
            // Utiliser l'ordre depuis alertCriteria (nouveau format: all, ou ancien: primary/secondary)
            const orderedAlertCriteriaNames = alertCriteria.all || [...(alertCriteria.primary || []), ...(alertCriteria.secondary || [])]
            // Filtrer pour ne garder que ceux qui ont des scores
            const alertCriteriaNames = orderedAlertCriteriaNames.filter(name => alertCriteriaScores[name])
            
            // Séparer les critères de l'alerte (top 5) et les autres
            const alertCriteriaSet = new Set(alertCriteriaNames)
            const otherCriteria = []
            
            // Récupérer les critères standards qui ne sont pas dans l'alerte
            const standardCriteria = {
              'localisation': { key: 'localisation', name: 'Localisation', alertKeys: ['quartier'], alwaysShow: false },
              'prix': { key: 'prix', name: 'Prix', alertKeys: ['prix'], alwaysShow: true },
              'style': { key: 'style', name: 'Style', alertKeys: ['haussmanien', 'neuf'], alwaysShow: false },
              'ensoleillement': { key: 'ensoleillement', name: 'Exposition', alertKeys: ['luminosite'], alwaysShow: false },
              'cuisine': { key: 'cuisine', name: 'Cuisine', alertKeys: ['cuisine_ouverte'], alwaysShow: false },
              'baignoire': { key: 'baignoire', name: 'Baignoire', alertKeys: ['baignoire'], alwaysShow: true },
              'calme': { key: 'calme', name: 'Calme', alertKeys: [], alwaysShow: true },
              'large_piece_vie': { key: 'large_piece_vie', name: 'Pièce de vie', alertKeys: ['large_piece_vie'], alwaysShow: true }
            }
            
            // Vérifier quels critères standards ne sont pas dans l'alerte
            for (const [key, info] of Object.entries(standardCriteria)) {
              // Vérifier si un des critères d'alerte correspond à ce critère standard
              const isInAlert = info.alertKeys.some(alertKey => alertCriteriaSet.has(alertKey))
              
              if (!isInAlert) {
                // Ce critère n'est pas dans l'alerte, l'ajouter aux autres
                // Toujours afficher si alwaysShow est true, sinon seulement si dans scores_detaille
                if (info.alwaysShow || apartment.scores_detaille?.[key]) {
                  otherCriteria.push({ key, name: info.name })
                }
              }
            }
            
            return (
              <>
                {/* Afficher d'abord les critères de l'alerte (top 5) */}
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
                  let customIndices = null
                  
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
                    // Passer les indices séparément pour l'affichage avec l'icône
                    customIndices = styleData.indices || null
                  } else if (alertCriterionName === 'luminosite') {
                    const expoData = formatExpositionCriterion(apartment, etage)
                    customTitle = expoData.title || displayName
                    customDescription = expoData.description || justification
                    // Pour l'exposition, les indices sont déjà dans la description
                  } else if (alertCriterionName === 'cuisine_ouverte') {
                    const cuisineData = formatCuisineCriterion(apartment)
                    customTitle = cuisineData.title || displayName
                    customDescription = cuisineData.description || justification
                  } else if (alertCriterionName === 'baignoire') {
                    const baignoireData = formatBaignoireCriterion(apartment)
                    customTitle = baignoireData.title || displayName
                    customDescription = baignoireData.description || justification
                  } else {
                    // Critères simples (ascenseur, large_piece_vie, hauteur_plafond, renove)
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
                      indices={customIndices}
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
                    const prixScore = apartment.scores_detaille?.prix || {}
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={prixScore.score || 0}
                        tier={prixScore.tier || 'tier3'}
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
                        indices={styleData.indices}
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
                    const cuisineScoreValue = cuisineScore.score !== undefined ? cuisineScore.score : (cuisineData.tier === 'tier1' ? 20 : cuisineData.tier === 'tier2' ? 10 : 0)
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
                  } else if (key === 'calme') {
                    const calmeData = formatCalmeCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={calmeData.score}
                        tier={calmeData.tier}
                        customTitle={calmeData.title}
                        customDescription={calmeData.description}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'large_piece_vie') {
                    const largePieceVieData = formatLargePieceVieCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={largePieceVieData.score}
                        tier={largePieceVieData.tier}
                        customTitle={largePieceVieData.title}
                        customDescription={largePieceVieData.description}
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
          // Dans la vue "all apartments" (showScore={false}), afficher depuis formatted_data même sans scores_detaille
          const hasScoresDetaille = apartment.scores_detaille && Object.keys(apartment.scores_detaille).length > 0
          const hasFormattedData = apartment.formatted_data && Object.keys(apartment.formatted_data).length > 0
          
          // Si on est dans la vue "all apartments" (showScore={false}), afficher les critères formatés même sans score
          if (!showScore) {
            // Afficher tous les critères disponibles depuis formatted_data ou depuis les données brutes
            const formattedData = apartment.formatted_data || {}
            
            return (
              <>
                {/* Localisation - toujours disponible depuis les données brutes */}
                {(() => {
                  const locData = formatLocalisation(apartment)
                  // Debug: vérifier ce qui est extrait
                  if (process.env.NODE_ENV === 'development') {
                    console.log('Localisation data:', {
                      id: apartment.id,
                      title: locData.title,
                      description: locData.description,
                      localisation: apartment.localisation,
                      localisation_precise: apartment.localisation_precise,
                      map_info_streets: apartment.map_info?.streets
                    })
                  }
                  if (locData.title || locData.description) {
                    return (
                      <Criterion 
                        name="Localisation"
                        score={0}
                        tier="tier3"
                        customTitle={locData.title}
                        customDescription={locData.description}
                        descriptionClass={locData.descriptionClass}
                        isGray={true}
                      />
                    )
                  }
                  return null
                })()}
                {/* Prix - toujours utiliser formatPrixCriterion pour le format correct */}
                {(() => {
                  const prixData = formatPrixCriterion(apartment)
                  if (prixData.title && prixData.description && prixData.description !== 'Non analysé') {
                    return (
                      <Criterion 
                        name="Prix"
                        score={0}
                        tier="tier3"
                        customTitle={prixData.title}
                        customDescription={prixData.description}
                        isGray={true}
                      />
                    )
                  }
                  return null
                })()}
                {/* Style - toujours utiliser formatStyleCriterion pour le format correct */}
                {(() => {
                  const styleData = formatStyleCriterion(apartment)
                  if (styleData.title || styleData.description) {
                    return (
                      <Criterion 
                        name="Style"
                        score={0}
                        tier="tier3"
                        customTitle={styleData.title}
                        customDescription={styleData.description}
                        indices={styleData.indices}
                        confidence={apartment.style_analysis?.style?.confidence}
                        isGray={true}
                      />
                    )
                  }
                  return null
                })()}
                {/* Exposition - toujours utiliser formatExpositionCriterion pour le format correct */}
                {(() => {
                  const expoData = formatExpositionCriterion(apartment, etage)
                  if (expoData.title || expoData.description) {
                    return (
                      <Criterion 
                        name="Exposition"
                        score={0}
                        tier="tier3"
                        customTitle={expoData.title}
                        customDescription={expoData.description}
                        confidence={expoData.confidence}
                        isGray={true}
                      />
                    )
                  }
                  return null
                })()}
                {/* Cuisine - toujours utiliser formatCuisineCriterion pour le format correct */}
                {(() => {
                  const cuisineData = formatCuisineCriterion(apartment)
                  if (cuisineData.title && cuisineData.description && cuisineData.description !== 'Non analysée') {
                    return (
                      <Criterion 
                        name="Cuisine"
                        score={0}
                        tier="tier3"
                        customTitle={cuisineData.title}
                        customDescription={cuisineData.description}
                        confidence={cuisineData.confidence}
                        isGray={true}
                      />
                    )
                  }
                  return null
                })()}
                {/* Baignoire - toujours utiliser formatBaignoireCriterion pour le format correct */}
                {(() => {
                  // Vérifier si on a des données baignoire (formatted_data ou scores_detaille)
                  if (formattedData.baignoire || apartment.scores_detaille?.baignoire) {
                    const baignoireData = formatBaignoireCriterion(apartment)
                    if (baignoireData.title && baignoireData.description && baignoireData.description !== 'Non analysé') {
                      return (
                        <Criterion 
                          name="Baignoire"
                          score={0}
                          tier="tier3"
                          customTitle={baignoireData.title}
                          customDescription={baignoireData.description}
                          confidence={baignoireData.confidence}
                          isGray={true}
                        />
                      )
                    }
                  }
                  return null
                })()}
                {/* Calme - toujours utiliser formatCalmeCriterion pour le format correct */}
                {(() => {
                  // Vérifier si on a des données calme (formatted_data ou scores_detaille)
                  if (formattedData.calme || apartment.scores_detaille?.calme) {
                    const calmeData = formatCalmeCriterion(apartment)
                    if (calmeData && (calmeData.title !== 'Calme' || calmeData.description !== 'Non analysé')) {
                      return (
                        <Criterion 
                          name="Calme"
                          score={0}
                          tier="tier3"
                          customTitle={calmeData.title}
                          customDescription={calmeData.description}
                          isGray={true}
                        />
                      )
                    }
                  }
                  return null
                })()}
                {/* Pièce de vie - depuis scores_detaille si disponible */}
                {(() => {
                  if (apartment.scores_detaille?.large_piece_vie) {
                    const largePieceVieData = formatLargePieceVieCriterion(apartment)
                    if (largePieceVieData && (largePieceVieData.title !== 'Pièce de vie' || largePieceVieData.description !== 'Non analysé')) {
                      return (
                        <Criterion 
                          name="Pièce de vie"
                          score={0}
                          tier="tier3"
                          customTitle={largePieceVieData.title}
                          customDescription={largePieceVieData.description}
                          isGray={true}
                        />
                      )
                    }
                  }
                  return null
                })()}
              </>
            )
          }
          
          // Sinon, afficher depuis scores_detaille (comportement normal avec score)
          return hasScoresDetaille ? (
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
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const prixData = formatPrixCriterion(apartment)
                const prixScore = apartment.scores_detaille?.prix || {}
                return (
                  <Criterion 
                    name="Prix"
                    score={prixScore.score || 0}
                    tier={prixScore.tier || 'tier3'}
                    customTitle={prixData.title}
                    customDescription={prixData.description}
                    isGray={!alertCriteria}
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
                    indices={styleData.indices}
                    confidence={apartment.style_analysis?.style?.confidence}
                    isGray={!alertCriteria}
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
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {apartment.scores_detaille.cuisine && (() => {
                const cuisineData = formatCuisineCriterion(apartment)
                const cuisineScore = apartment.scores_detaille.cuisine || {}
                const cuisineScoreValue = cuisineScore.score !== undefined ? cuisineScore.score : (cuisineData.tier === 'tier1' ? 20 : cuisineData.tier === 'tier2' ? 10 : 0)
                
                return (
                  <Criterion 
                    name="Cuisine"
                    score={cuisineScoreValue}
                    tier={cuisineData.tier}
                    customTitle={cuisineData.title}
                    customDescription={cuisineData.description}
                    confidence={cuisineData.confidence}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const baignoireData = formatBaignoireCriterion(apartment)
                return (
                  <Criterion 
                    name="Baignoire"
                    score={baignoireData.score}
                    tier={baignoireData.tier}
                    customTitle={baignoireData.title}
                    customDescription={baignoireData.description}
                    confidence={baignoireData.confidence}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const calmeData = formatCalmeCriterion(apartment)
                return (
                  <Criterion 
                    name="Calme"
                    score={calmeData.score}
                    tier={calmeData.tier}
                    customTitle={calmeData.title}
                    customDescription={calmeData.description}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const largePieceVieData = formatLargePieceVieCriterion(apartment)
                return (
                  <Criterion 
                    name="Pièce de vie"
                    score={largePieceVieData.score}
                    tier={largePieceVieData.tier}
                    customTitle={largePieceVieData.title}
                    customDescription={largePieceVieData.description}
                    isGray={!alertCriteria}
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
  const metro = getMetroName(apartment)
  const mapInfo = apartment.map_info || {}
  const streets = mapInfo.streets || []
  
  // Format ALL apartments: title "Metro X", description "166 rue saint maur"
  const title = metro ? `Metro ${metro}` : 'Localisation'
  
  // Chercher une rue dans plusieurs sources
  let rue = null
  
  // Priorité 1: map_info.streets
  if (streets.length > 0) {
    rue = streets[0]
  } else {
    // Priorité 2: localisation_precise (si disponible)
    const localisationPrecise = apartment.localisation_precise || ''
    if (localisationPrecise) {
      // Format: "35 Rue Mélingue, 75019 Paris 19e" -> extraire "35 Rue Mélingue"
      if (localisationPrecise.includes(',')) {
        rue = localisationPrecise.split(',')[0].trim()
      } else {
        // Chercher un pattern de rue dans localisation_precise
        const rueMatch = localisationPrecise.match(/(\d+\s*(?:rue|Rue|RUE|avenue|Avenue|AVENUE|boulevard|Boulevard|BOULEVARD|place|Place|PLACE)[^,]*)/i)
        if (rueMatch) {
          rue = rueMatch[1].trim()
        }
      }
    }
    
    // Priorité 3: extraire depuis localisation (format "Metro X · 166 rue Saint Maur" ou similaire)
    if (!rue) {
      const localisation = apartment.localisation || ''
      // Chercher après "·" (séparateur) ou directement dans la string
      // Pattern amélioré pour capturer "35 Rue Mélingue" même avec espaces
      const rueMatch = localisation.match(/(\d+\s+(?:rue|avenue|boulevard|place|Rue|Avenue|Boulevard|Place)\s+[^·,]+)/i)
      if (rueMatch) {
        rue = rueMatch[1].trim()
      } else {
        // Fallback: chercher n'importe quel pattern avec numéro + type de rue
        const rueMatch2 = localisation.match(/(\d+\s*(?:rue|avenue|boulevard|place)[^·,]*)/i)
        if (rueMatch2) {
          rue = rueMatch2[1].trim()
        }
      }
    }
  }
  
  // Description: la rue en minuscules (retourner string vide si pas de rue, pas null)
  const description = rue ? rue.toLowerCase() : ''
  
  return {
    title,
    description,
    descriptionClass: null
  }
}

// Fonction pour obtenir le prix médian de l'arrondissement
function getArrondissementMedianPrice(postalCode) {
  if (!postalCode || !postalCode.startsWith('75')) {
    return null
  }
  
  // Mapping des prix médians par arrondissement (valeurs par défaut)
  const medianPrices = {
    '75001': 12000,
    '75002': 12000,
    '75003': 11000,
    '75004': 12000,
    '75005': 11000,
    '75006': 13000,
    '75007': 13000,
    '75008': 14000,
    '75009': 11000,
    '75010': 10500,
    '75011': 11000,
    '75012': 9500,
    '75013': 9000,
    '75014': 9500,
    '75015': 10000,
    '75016': 12000,
    '75017': 11000,
    '75018': 9500,
    '75019': 9500,
    '75020': 9000,
  }
  
  return medianPrices[postalCode] || null
}

// Fonction pour extraire le numéro d'arrondissement depuis le code postal
function getArrondissementNumber(postalCode) {
  if (!postalCode || !postalCode.startsWith('75')) {
    return null
  }
  const arrNum = postalCode.slice(-2)
  if (arrNum && !isNaN(arrNum) && parseInt(arrNum) <= 20) {
    return parseInt(arrNum)
  }
  return null
}

function formatPrixCriterion(apartment) {
  // Format ALL apartments: title "11,8k € /m2", description "Moyenne 11e: 11k€ /m2"
  // Pas besoin de vérifier le tier pour le titre dans cette vue
  
  // Calculer prix/m²
  let prixM2 = null
  const prixM2Str = apartment.prix_m2 || ''
  const surface = apartment.surface || ''
  const prix = apartment.prix || ''
  
  // Extraire depuis prix_m2
  if (prixM2Str && prixM2Str !== 'Prix/m² non trouvé') {
    const prixM2Match = prixM2Str.replace(/\s/g, '').match(/(\d+)/)
    if (prixM2Match) {
      prixM2 = parseInt(prixM2Match[1])
    }
  }
  
  // Sinon calculer depuis prix et surface
  if (!prixM2 && surface && prix) {
    const surfaceMatch = surface.match(/(\d+)/)
    const prixMatch = prix.replace(/\s/g, '').match(/(\d+)/)
    
    if (surfaceMatch && prixMatch) {
      const surfaceNum = parseInt(surfaceMatch[1])
      const prixNum = parseInt(prixMatch[1])
      
      if (surfaceNum > 0) {
        prixM2 = Math.floor(prixNum / surfaceNum)
      }
    }
  }
  
  if (!prixM2) {
    return {
      title: 'Prix',
      description: 'Non analysé'
    }
  }
  
  // Arrondir au 100€ près
  const prixM2Rounded = Math.round(prixM2 / 100) * 100
  
  // Récupérer le code postal
  let postalCode = apartment._api_data?.postal_code || ''
  if (!postalCode) {
    // Essayer depuis localisation
    const localisation = apartment.localisation || ''
    const postalMatch = localisation.match(/75\d{3}/)
    if (postalMatch) {
      postalCode = postalMatch[0]
    }
  }
  
  // Extraire l'arrondissement et le prix médian
  const arrondissementNum = getArrondissementNumber(postalCode)
  const medianPrice = getArrondissementMedianPrice(postalCode)
  
  // Format ALL apartments: title "11,8k € /m2", description "Moyenne 11e: 11k€ /m2"
  // Convertir prixM2Rounded en format "k" (ex: 11800 -> 11,8k)
  const prixM2K = (prixM2Rounded / 1000).toFixed(1).replace('.0', '').replace('.', ',')
  const title = `${prixM2K}k € /m2`
  
  // Description: "Moyenne 11e: 11k€ /m2"
  let description = ''
  if (medianPrice && arrondissementNum) {
    const medianK = (medianPrice / 1000).toFixed(0)
    description = `Moyenne ${arrondissementNum}e: ${medianK}k€ /m2`
  } else if (arrondissementNum) {
    description = `${arrondissementNum}e`
  }
  
  return {
    title,
    description
  }
}

function formatStyleCriterion(apartment) {
  const styleAnalysis = apartment.style_analysis || {}
  const styleData = styleAnalysis.style || {}
  const styleType = styleData.type || ''
  
  // Année de construction
  let anneeConstruction = null
  
  // 1. Vérifier dans caracteristiques.annee_construction (si objet)
  const caracteristiques = apartment.caracteristiques || {}
  if (typeof caracteristiques === 'object' && caracteristiques.annee_construction) {
    anneeConstruction = caracteristiques.annee_construction
  }
  
  // 2. Vérifier directement dans apartment.annee_construction
  if (!anneeConstruction) {
    anneeConstruction = apartment.annee_construction
  }
  
  // 3. Extraire depuis caracteristiques si c'est une string (format "Année: 1880")
  if (!anneeConstruction && typeof caracteristiques === 'string') {
    const caracteristiquesStr = caracteristiques
    // Pattern: "Année: 1880" ou "Année : 1880"
    const yearMatch = caracteristiquesStr.match(/année\s*:?\s*(\d{4})/i)
    if (yearMatch) {
      anneeConstruction = yearMatch[1]
    } else {
      // Pattern: "Construit en 1909" ou "construction 1909"
      const construitMatch = caracteristiquesStr.match(/(?:construit|construction)\s*(?:en|de)?\s*(\d{4})/i)
      if (construitMatch) {
        anneeConstruction = construitMatch[1]
      }
    }
  }
  
  // 4. Vérifier dans _api_data.features.year
  if (!anneeConstruction && apartment._api_data?.features?.year) {
    const yearValue = apartment._api_data.features.year
    if (yearValue && yearValue !== 'null' && yearValue !== null) {
      anneeConstruction = String(yearValue)
    }
  }
  
  // Titre: déterminé selon l'année de construction si disponible, sinon selon le style détecté
  let title = 'Style'
  
  // Si une année est trouvée, elle écrase le style initial
  if (anneeConstruction) {
    const year = parseInt(anneeConstruction)
    if (!isNaN(year)) {
      if (year < 1910) {
        title = 'Haussmanien'  // Format screenshot: sans "Style" devant
      } else if (year >= 1910 && year <= 1980) {
        // Calculer la décennie (ex: 1976 -> années 70)
        const decade = Math.floor(year / 10) * 10
        title = `Années ${decade.toString().slice(-2)}`
      } else if (year > 1980) {
        title = 'Moderne'
      }
    }
  } else {
    // Pas d'année trouvée, utiliser le style depuis formatted_data (backend) en priorité
    const formattedStyle = apartment.formatted_data?.style
    const mainValue = formattedStyle?.main_value
    
    if (mainValue && mainValue !== 'Non spécifié') {
      // Utiliser le style depuis formatted_data (créé par le backend)
      title = mainValue
    } else if (styleType && styleType !== 'autre' && styleType !== 'inconnu') {
      // Fallback: utiliser le style détecté par l'IA
      let styleName = styleType.charAt(0).toUpperCase() + styleType.slice(1)
      
      // Gérer les cas spéciaux
      if (styleType.includes('70') || styleType.toLowerCase().includes('seventies')) {
        styleName = "70s"
      } else if (styleType.toLowerCase().includes('haussmann')) {
        styleName = "Haussmannien"
      }
      
      title = styleName  // Format screenshot: sans "Style" devant
    }
  }
  
  // Extraire les indices du style séparément (comme pour l'exposition)
  let indices = null
  
  // Utiliser les indices depuis formatted_data en priorité
  let styleIndices = apartment.formatted_data?.style?.indices
  
  if (styleIndices && styleIndices !== 'Style expo cuisine et baignoire') {
    // Nettoyer les indices
    let indicesClean = styleIndices
      .replace(/^Style Indice:\n?/i, '')
      .replace(/^Style:\n?/i, '')
      .replace(/Style\s+(?:haussmannien|neuf|atypique|70s|autre|inconnu)[\s·,]*/gi, '')
      .replace(/\([^)]*construction[^)]*\)/gi, '')
      .trim()
    
    if (indicesClean && !indicesClean.includes('Non spécifié') && indicesClean.length > 0) {
      indices = indicesClean
    }
  }
  
  // Fallback: chercher dans style_analysis si formatted_data n'a pas d'indices
  if (!indices) {
    const details = styleData.details || ''
    const justification = styleData.justification || ''
    const textToSearch = `${details} ${justification}`.toLowerCase()
    
    const keywords = []
    if (textToSearch.includes('moulures') || textToSearch.includes('moldings')) {
      keywords.push('moulures')
    }
    if (textToSearch.includes('cheminée') || textToSearch.includes('fireplace')) {
      keywords.push('cheminée')
    }
    if (textToSearch.includes('parquet')) {
      keywords.push('parquet')
    }
    if (textToSearch.includes('balcon') && (textToSearch.includes('fer') || textToSearch.includes('forgé'))) {
      keywords.push('balcon fer forgé')
    }
    if (textToSearch.includes('éléments décoratifs') || textToSearch.includes('elements decoratifs')) {
      keywords.push('éléments décoratifs')
    }
    if (textToSearch.includes('hauteur sous plafond')) {
      keywords.push('hauteur sous plafond')
    }
    
    if (keywords.length > 0) {
      indices = keywords.join(', ')
    }
  }
  
  // Ajouter le préfixe "Indices:" si des indices sont présents
  if (indices) {
    indices = `Indices: ${indices}`
  }
  
  // Format ALL apartments: description "Construit en 1855" (si dispo) sinon null (les indices seront affichés séparément)
  let description = null
  if (anneeConstruction) {
    // Si année disponible, description = "Construit en XXXX"
    description = `Construit en ${anneeConstruction}`
  }
  // Sinon, description reste null et les indices seront affichés séparément
  
  return {
    title,
    description,
    indices
  }
}

function formatExpositionCriterion(apartment, etage) {
  // Utiliser les données formatées depuis le backend si disponibles
  let mainValue = 'Sombre'
  let indices = null
  let confidence = null
  
  // Récupérer le vis-à-vis depuis exposition.details.visavis_distance (priorité absolue)
  const exposition = apartment.exposition || {}
  const visavisDistance = exposition.details?.visavis_distance
  
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
    
    // Reconstruire systématiquement la description avec le format "1er étage · Vis a vis moyen (15m)"
    // Même si formatted_data.exposition.indices existe, on le reconstruit pour garantir le format
    const descriptionParts = []
    
    // Formater l'étage correctement (1er au lieu de 1e)
    if (etage) {
      let etageFormatted = etage
      // Convertir "1e étage" en "1er étage"
      if (etage.match(/^1e\s*étage$/i)) {
        etageFormatted = '1er étage'
      }
      descriptionParts.push(etageFormatted)
    }
    
    // Ajouter vis-à-vis si disponible (priorité: exposition.details.visavis_distance)
    const visavisCategory = exposition.details?.visavis_category
    const translateCategory = (cat) => {
      if (cat === 'good') return 'bon'
      if (cat === 'moyen') return 'moyen'
      if (cat === 'bad') return 'mauvais'
      return cat
    }
    
    if (visavisDistance !== null && visavisDistance !== undefined && visavisDistance !== '') {
      // Format screenshot: "Vis à vis 10m" (sans catégorie entre parenthèses)
      // Vérifier si les indices originaux contiennent "(upgrade >20m)" OU si vis-à-vis > 20m
      const hasUpgradeInfo = (indices && indices.includes('(upgrade >20m)')) || visavisDistance > 20
      let visavisText = `Vis à vis ${visavisDistance}m`
      if (hasUpgradeInfo) {
        visavisText += ' (upgrade >20m)'
      }
      descriptionParts.push(visavisText)
    } else {
      // Fallback: essayer d'extraire depuis les indices existants (préserver upgrade info si présente)
      if (indices) {
        const visavisMatch = indices.match(/vis[-\sà]?[aà][-\sà]?vis[^·]*?(\d+)\s*m[^·]*?(\(upgrade\s*>20m\))?/i)
        if (visavisMatch) {
          const extractedDistance = parseInt(visavisMatch[1], 10)
          const hasUpgradeInfo = visavisMatch[2] || extractedDistance > 20
          let visavisText = `Vis à vis ${extractedDistance}m`
          if (hasUpgradeInfo) {
            visavisText += ' (upgrade >20m)'
          }
          descriptionParts.push(visavisText)
        }
      }
    }
    
    // Utiliser la description reconstruite si on a des éléments, sinon garder les indices originaux
    if (descriptionParts.length > 0) {
      indices = descriptionParts.join(' · ')
    }
  } else {
    // Fallback: utiliser directement apartment.exposition si disponible
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
    
    // Construire systématiquement les indices au format "1er étage · Vis a vis moyen (15m)"
    const descriptionParts = []
    
    // Formater l'étage correctement (1er au lieu de 1e)
    if (etage) {
      let etageFormatted = etage
      // Convertir "1e étage" en "1er étage"
      if (etage.match(/^1e\s*étage$/i)) {
        etageFormatted = '1er étage'
      }
      descriptionParts.push(etageFormatted)
    }
    
    // Ajouter vis-à-vis si disponible (priorité: exposition.details.visavis_distance)
    const visavisCategory = exposition.details?.visavis_category
    const translateCategory = (cat) => {
      if (cat === 'good') return 'bon'
      if (cat === 'moyen') return 'moyen'
      if (cat === 'bad') return 'mauvais'
      return cat
    }
    
    if (visavisDistance !== null && visavisDistance !== undefined && visavisDistance !== '') {
      // Format screenshot: "Vis à vis 10m" (sans catégorie entre parenthèses)
      const hasUpgrade = visavisDistance > 20
      let visavisText = `Vis à vis ${visavisDistance}m`
      if (hasUpgrade) {
        visavisText += ' (upgrade >20m)'
      }
      descriptionParts.push(visavisText)
    }
    
    indices = descriptionParts.length > 0 ? descriptionParts.join(' · ') : null
    confidence = exposition.confidence || null
  }
  
  // Titre: "Lumineux" / "Luminosité normale" / "Sombre" (format du screenshot)
  let title = 'Exposition'
  if (mainValue === 'Lumineux') {
    title = 'Lumineux'
  } else if (mainValue === 'Luminosité moyenne') {
    title = 'Luminosité normale'
  } else {
    title = 'Sombre'
  }
  
  // Description: "1er étage · Vis a vis moyen (15m)" (format systématique)
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
    description = `Détectée sur photo ${photoNum}`
  } else {
    // Fallback: utiliser les indices depuis formatted_data
    const cuisineIndices = apartment.formatted_data?.cuisine?.indices
    if (cuisineIndices && cuisineIndices !== 'Style expo cuisine et baignoire') {
      // Extraire le numéro d'image depuis les indices
      const imageMatch = cuisineIndices.match(/image\s*(\d+)/i)
      if (imageMatch) {
        description = `Détectée sur photo ${imageMatch[1]}`
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
  // Utiliser les scores depuis scores_detaille.baignoire
  const scoresDetaille = apartment.scores_detaille || {}
  const baignoireScore = scoresDetaille.baignoire || {}
  
  // Si pas encore analysé, afficher "Non analysé"
  if (!baignoireScore || Object.keys(baignoireScore).length === 0) {
    return {
      title: 'Baignoire',
      description: 'Non analysé',
      tier: 'tier3',
      score: 0,
      confidence: null
    }
  }
  
  // PRIORITÉ: Utiliser formatted_data depuis le backend (comme pour cuisine)
  // Récupérer les indices depuis formatted_data (backend) en priorité
  let indices = apartment.formatted_data?.baignoire?.indices || null
  
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

function formatCalmeCriterion(apartment) {
  const scoresDetaille = apartment.scores_detaille || {}
  const calmeScore = scoresDetaille.calme || {}
  
  // Si pas encore analysé, afficher "Non analysé"
  if (!calmeScore || Object.keys(calmeScore).length === 0) {
    return {
      title: 'Calme',
      description: 'Non analysé',
      tier: 'tier3',
      score: 0
    }
  }
  
  const tier = calmeScore.tier || 'tier3'
  const justification = calmeScore.justification || ''
  
  // Titre selon le tier
  let title = 'Calme'
  if (tier === 'tier1') {
    title = 'Calme'
  } else if (tier === 'tier2') {
    title = 'Moyennement calme'
  } else {
    title = 'Animé'
  }
  
  // Description depuis la justification ou formatted_data
  let description = justification
  if (!description && apartment.formatted_data?.calme) {
    const calmeData = apartment.formatted_data.calme
    const indices = calmeData.indices || ''
    if (indices) {
      // Nettoyer les préfixes
      description = indices
        .replace(/^Calme Indice:\s*/i, '')
        .replace(/^Calme:\s*/i, '')
        .trim()
    }
  }
  
  if (!description) {
    description = 'Non spécifié'
  }
  
  return {
    title,
    description,
    tier,
    score: calmeScore.score || 0
  }
}

function formatLargePieceVieCriterion(apartment) {
  const scoresDetaille = apartment.scores_detaille || {}
  const largePieceVieScore = scoresDetaille.large_piece_vie || {}
  
  // Si pas encore analysé, afficher "Non analysé"
  if (!largePieceVieScore || Object.keys(largePieceVieScore).length === 0) {
    return {
      title: 'Pièce de vie',
      description: 'Non analysé',
      tier: 'tier3',
      score: 0
    }
  }
  
  const tier = largePieceVieScore.tier || 'tier3'
  const justification = largePieceVieScore.justification || ''
  const details = largePieceVieScore.details || {}
  
  // Titre selon le tier
  let title = 'Pièce de vie'
  if (tier === 'tier1') {
    title = 'Grande pièce de vie'
  } else if (tier === 'tier2') {
    title = 'Pièce de vie correcte'
  } else {
    title = 'Petite pièce de vie'
  }
  
  // Description depuis la justification ou les détails
  let description = justification
  if (!description && details.pourcentage_salon !== undefined) {
    const pourcentage = details.pourcentage_salon
    const salonSize = details.salon_size_estimate
    if (salonSize && pourcentage) {
      description = `${salonSize}m² (${pourcentage.toFixed(1)}% de la surface totale)`
    }
  }
  
  if (!description) {
    description = 'Non spécifié'
  }
  
  return {
    title,
    description,
    tier,
    score: largePieceVieScore.score || 0
  }
}

// Fonction pour formater les données manuelles (sans IA) pour les appartements sans données enrichies
function formatManualDataCriteria(apartment, etage) {
  const criteria = []
  
  // 1. Localisation (Metro + Adresse)
  const locData = formatLocalisation(apartment)
  if (locData.title || locData.description) {
    criteria.push({
      name: 'Localisation',
      title: locData.title || 'Localisation',
      description: locData.description || '',
      emoji: '📍'
    })
  }
  
  // 2. Prix par m²
  const prixData = formatPrixCriterion(apartment)
  if (prixData.title && prixData.description && prixData.description !== 'Non analysé') {
    criteria.push({
      name: 'Prix',
      title: prixData.title,
      description: prixData.description,
      emoji: '💰'
    })
  }
  
  // 3. Style architectural
  const styleData = formatStyleCriterion(apartment)
  if (styleData.title || styleData.description) {
    criteria.push({
      name: 'Style',
      title: styleData.title || 'Style',
      description: styleData.description || 'Non spécifié',
      emoji: '🔑',
      indices: styleData.indices
    })
  }
  
  // 4. Luminosité/Exposition
  // Calculer la luminosité en fonction de l'étage (logique du backend)
  let expoTitle = 'Luminosité normale' // Par défaut
  let expoDescription = etage || 'Non spécifié'
  
  // Extraire le numéro d'étage pour calculer la luminosité
  let etageNum = null
  if (etage) {
    // Extraire le numéro depuis "3e étage", "1er étage", "RDC", etc.
    const etageMatch = etage.match(/(\d+)(?:er?|e|ème?)/i)
    if (etageMatch) {
      etageNum = parseInt(etageMatch[1])
    } else if (etage.toLowerCase().includes('rdc') || etage.toLowerCase().includes('rez')) {
      etageNum = 0
    }
  }
  
  // Logique de classification selon l'étage (même que backend)
  // Sombre : < 3e étage (RDC, 1er, 2e)
  // Moyen : 3e-4e étage
  // Lumineux : > 4e étage (≥5e)
  if (etageNum !== null) {
    if (etageNum < 3) {
      expoTitle = 'Sombre'
    } else if (etageNum >= 3 && etageNum <= 4) {
      expoTitle = 'Luminosité normale'
    } else if (etageNum > 4) {
      expoTitle = 'Lumineux'
    }
  }
  
  // Essayer d'améliorer avec l'orientation si disponible (upgrade)
  const exposition = apartment.exposition || {}
  const expositionDir = exposition.exposition || ''
  if (expositionDir && etageNum !== null) {
    const expoNormalized = expositionDir.toLowerCase().replace(/[_\s-]/g, '')
    // Upgrade si Sud/Ouest mentionné
    if (expoNormalized === 'sud' || expoNormalized === 'sudouest' || expoNormalized === 'sudest') {
      if (expoTitle === 'Sombre') {
        expoTitle = 'Luminosité normale'
      } else if (expoTitle === 'Luminosité normale') {
        expoTitle = 'Lumineux'
      }
    } else if (expoNormalized === 'nord' || expoNormalized === 'nordouest' || expoNormalized === 'nordest') {
      // Downgrade si Nord
      if (expoTitle === 'Lumineux') {
        expoTitle = 'Luminosité normale'
      } else if (expoTitle === 'Luminosité normale') {
        expoTitle = 'Sombre'
      }
    }
  }
  
  // Fallback: utiliser style_analysis si disponible
  if (expoTitle === 'Luminosité normale' && etageNum === null) {
    const styleAnalysis = apartment.style_analysis || {}
    const luminositeData = styleAnalysis.luminosite || {}
    const luminositeType = luminositeData.type || ''
    if (luminositeType) {
      if (luminositeType.toLowerCase().includes('excellente')) {
        expoTitle = 'Lumineux'
      } else if (luminositeType.toLowerCase().includes('sombre')) {
        expoTitle = 'Sombre'
      }
    }
  }
  
  criteria.push({
    name: 'Exposition',
    title: expoTitle,
    description: expoDescription,
    emoji: '☀️'
  })
  
  // 5. Cuisine
  // Pour les données manuelles, utiliser un format simplifié
  let cuisineTitle = 'Cuisine'
  let cuisineDescription = 'non specifié'
  
  // Essayer d'extraire depuis les données brutes si disponibles
  const cuisineData = formatCuisineCriterion(apartment)
  if (cuisineData.title && cuisineData.title !== 'Cuisine' && cuisineData.description && cuisineData.description !== 'Non analysée') {
    cuisineTitle = cuisineData.title
    cuisineDescription = cuisineData.description
  } else {
    // Chercher dans style_analysis si disponible
    const styleAnalysis = apartment.style_analysis || {}
    const cuisineAnalysis = styleAnalysis.cuisine || {}
    if (cuisineAnalysis.ouverte !== undefined) {
      cuisineTitle = cuisineAnalysis.ouverte ? 'Cuisine ouverte' : 'Cuisine fermée'
      cuisineDescription = 'Détectée dans les données'
    }
  }
  
  criteria.push({
    name: 'Cuisine',
    title: cuisineTitle,
    description: cuisineDescription,
    emoji: '👨‍🍳'
  })
  
  // 6. Ascenseur
  const caracteristiques = apartment.caracteristiques || {}
  const description = apartment.description || ''
  const apiData = apartment._api_data || {}
  const features = apiData.features || {}
  
  let hasAscenseur = false
  let ascenseurDescription = 'Analyse manquante'
  
  // Vérifier dans caracteristiques
  if (typeof caracteristiques === 'object' && caracteristiques.ascenseur !== undefined) {
    hasAscenseur = caracteristiques.ascenseur === true || caracteristiques.ascenseur === 'Oui' || caracteristiques.ascenseur === 'oui'
    ascenseurDescription = hasAscenseur ? 'Ascenseur présent' : 'Pas d\'ascenseur'
  } else if (typeof caracteristiques === 'string' && caracteristiques.toLowerCase().includes('ascenseur')) {
    hasAscenseur = !caracteristiques.toLowerCase().includes('sans ascenseur')
    ascenseurDescription = hasAscenseur ? 'Ascenseur présent' : 'Pas d\'ascenseur'
  } else if (features.lift === 1) {
    hasAscenseur = true
    ascenseurDescription = 'Ascenseur présent'
  } else if (description.toLowerCase().includes('ascenseur')) {
    hasAscenseur = !description.toLowerCase().includes('sans ascenseur')
    ascenseurDescription = hasAscenseur ? 'Ascenseur présent' : 'Pas d\'ascenseur'
  }
  
  criteria.push({
    name: 'Ascenseur',
    title: hasAscenseur ? 'Ascenseur' : 'Pas d\'ascenseur',
    description: ascenseurDescription,
    emoji: '🛗'
  })
  
  // 7. Taille pièce de vie
  const largePieceVieData = formatLargePieceVieCriterion(apartment)
  criteria.push({
    name: 'Pièce de vie',
    title: 'Taille pièce de vie',
    description: largePieceVieData.description || 'Analyse manquante',
    emoji: '🛋️'
  })
  
  return criteria
}

// Mapping des critères vers leurs emojis
const CRITERION_EMOJIS = {
  'Localisation': '📍',
  'Prix': '💰',
  'Style': '🎨',
  'Exposition': '☀️',
  'Cuisine': '👨‍🍳',
  'Baignoire': '🛁',
  'Calme': '🔇',
  'Pièce de vie': '🛋️'
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
  'hauteur_plafond': 'Hauteur plafond',
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
  'hauteur_plafond': '📏',
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


