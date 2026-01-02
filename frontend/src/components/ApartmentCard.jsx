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

function ApartmentCard({ apartment, alertCriteria = null }) {
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
    // PRIORITÉ ABSOLUE: Si on a alert_criteria_scores, TOUJOURS utiliser le calcul local (sur 5)
    // C'est la source de vérité car elle contient les scores individuels à jour (1pt, 0.5pt, 0pt)
    if (calculatedAlertScore !== null && calculatedAlertScore !== undefined) {
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
        return round(total, 2)
      }
    }
    
    // Si on a alert_score, utiliser directement alert_score du backend (PRIORITÉ ABSOLUE)
    // Le backend renvoie maintenant toujours sur 5
    // Ne pas vérifier alertCriteria ici - si alert_score existe, c'est qu'on est dans une vue d'alerte
    if (apartment.alert_score !== undefined) {
      // Ancien système (sur 100), convertir en divisant par 20 si nécessaire
      if (apartment.alert_score > 5) {
        return round(apartment.alert_score / 20, 2)
      }
      return apartment.alert_score
    }
    
    // Si aucune alerte n'est sélectionnée (pas d'alertCriteria passé en prop), ne pas afficher de score
    // Sur la page d'accueil sans critères sélectionnés, les appartements ne doivent pas avoir de mega score
    if (!alertCriteria) {
      return undefined
    }
    
    // Sinon, utiliser megaScore (score standard) - SEULEMENT si ce n'est PAS une alerte
    // Si on est dans la vue Alertes, on ne devrait jamais arriver ici
    return megaScore
  }, [calculatedAlertScore, apartment.alert_score, apartment.alert_criteria_scores, apartment.alert_tier, apartment.id, megaScore, alertCriteria])
  
  // maxScore: 5 pour alert_score (si alert_criteria_scores, alert_tier ou alert_score présent), 90 pour megaScore
  const maxScore = useMemo(() => {
    // Si on a des critères d'alerte, un tier d'alerte, ou un alert_score, c'est une alerte (score sur 5)
    if (apartment.alert_criteria_scores || apartment.alert_tier || apartment.alert_score !== undefined) {
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
  
  // Extraire l'index de la photo détectée (cuisine ou baignoire) pour initialiser le Carousel
  const detectedPhotoIndex = useMemo(() => {
    // Chercher d'abord pour la cuisine
    let detectedPhotos = []
    
    // Source 1: scores_detaille.cuisine.details.photo_validation.photo_result.detected_photos
    const cuisineScore = apartment.scores_detaille?.cuisine || {}
    const cuisineDetails = cuisineScore.details || {}
    const cuisinePhotoValidation = cuisineDetails.photo_validation || {}
    const cuisinePhotoResult = cuisinePhotoValidation.photo_result || {}
    if (cuisinePhotoResult.detected_photos && Array.isArray(cuisinePhotoResult.detected_photos)) {
      detectedPhotos.push(...cuisinePhotoResult.detected_photos)
    }
    
    // Source 2: style_analysis.cuisine.detected_photos
    const styleCuisine = apartment.style_analysis?.cuisine || {}
    if (styleCuisine.detected_photos && Array.isArray(styleCuisine.detected_photos)) {
      detectedPhotos.push(...styleCuisine.detected_photos)
    }
    
    // Source 3: formatted_data.cuisine.detected_photos
    const cuisineFormatted = apartment.formatted_data?.cuisine || {}
    if (cuisineFormatted.detected_photos && Array.isArray(cuisineFormatted.detected_photos)) {
      detectedPhotos.push(...cuisineFormatted.detected_photos)
    }
    
    // Si pas de photo détectée pour la cuisine, chercher pour la baignoire
    if (detectedPhotos.length === 0) {
      const baignoireScore = apartment.scores_detaille?.baignoire || {}
      const baignoireDetails = baignoireScore.details || {}
      const baignoirePhotoValidation = baignoireDetails.photo_validation || {}
      const baignoirePhotoResult = baignoirePhotoValidation.photo_result || {}
      if (baignoirePhotoResult.detected_photos && Array.isArray(baignoirePhotoResult.detected_photos)) {
        detectedPhotos.push(...baignoirePhotoResult.detected_photos)
      }
      
      // Source 2: style_analysis.baignoire.detected_photos
      const styleBaignoire = apartment.style_analysis?.baignoire || {}
      if (styleBaignoire.detected_photos && Array.isArray(styleBaignoire.detected_photos)) {
        detectedPhotos.push(...styleBaignoire.detected_photos)
      }
      
      // Source 3: formatted_data.baignoire.detected_photos
      const baignoireFormatted = apartment.formatted_data?.baignoire || {}
      if (baignoireFormatted.detected_photos && Array.isArray(baignoireFormatted.detected_photos)) {
        detectedPhotos.push(...baignoireFormatted.detected_photos)
      }
      
      // Source 4: baignoire_data.detected_photos
      const baignoireData = apartment.baignoire_data || {}
      if (baignoireData.detected_photos && Array.isArray(baignoireData.detected_photos)) {
        detectedPhotos.push(...baignoireData.detected_photos)
      }
    }
    
    // Prendre le premier numéro unique
    const uniqueDetectedPhotos = [...new Set(detectedPhotos)]
    if (uniqueDetectedPhotos.length > 0) {
      let photoIndex = uniqueDetectedPhotos[0]
      
      // Normaliser: si c'est un index 0-based (0-19), utiliser tel quel
      // Si c'est un numéro 1-based (1-20), convertir en 0-based
      if (typeof photoIndex === 'number') {
        if (photoIndex >= 1 && photoIndex <= 20) {
          // Probablement 1-based, convertir en 0-based
          photoIndex = photoIndex - 1
        }
        // Si photoIndex est déjà 0-based (0-19), utiliser tel quel
        
        // S'assurer que l'index est valide par rapport au nombre de photos
        if (photoIndex >= 0 && photoIndex < photos.length) {
          return photoIndex
        }
      }
    }
    
    // Fallback: extraire le numéro de photo depuis les descriptions si detected_photos n'est pas disponible
    // Chercher dans les indices de la cuisine (réutiliser cuisineFormatted déclaré plus haut)
    const cuisineIndices = cuisineFormatted.indices || ''
    if (cuisineIndices) {
      const cuisineMatch = cuisineIndices.match(/photo\s*(\d+)|image\s*(\d+)/i)
      if (cuisineMatch) {
        const photoNum = parseInt(cuisineMatch[1] || cuisineMatch[2], 10)
        if (photoNum >= 1 && photoNum <= photos.length) {
          return photoNum - 1 // Convertir 1-based en 0-based
        }
      }
    }
    
    // Chercher dans les indices de la baignoire
    const baignoireFormattedFallback = apartment.formatted_data?.baignoire || {}
    const baignoireIndices = baignoireFormattedFallback.indices || ''
    if (baignoireIndices) {
      const baignoireMatch = baignoireIndices.match(/photo\s*(\d+)|image\s*(\d+)/i)
      if (baignoireMatch) {
        const photoNum = parseInt(baignoireMatch[1] || baignoireMatch[2], 10)
        if (photoNum >= 1 && photoNum <= photos.length) {
          return photoNum - 1 // Convertir 1-based en 0-based
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
        <div className="apartment-title">{apartmentInfoWithEtage.title}</div>
        <div className="apartment-subtitle">{apartmentInfoWithEtage.subtitle}</div>
        
        {/* Critères */}
        {(() => {
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
              'hauteur_plafond': { key: 'hauteur_plafond', name: 'Hauteur plafond', alertKeys: ['hauteur_plafond'], alwaysShow: true },
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
                    // Passer les indices pour l'affichage en bleu
                    customIndices = styleData.indices || null
                  } else if (alertCriterionName === 'luminosite') {
                    const expoData = formatExpositionCriterion(apartment, etage)
                    customTitle = expoData.title || displayName
                    customDescription = expoData.description || justification
                    // Passer les indices pour l'affichage en bleu
                    customIndices = expoData.indices || null
                  } else if (alertCriterionName === 'cuisine_ouverte') {
                    const cuisineData = formatCuisineCriterion(apartment)
                    customTitle = cuisineData.title || displayName
                    customDescription = cuisineData.description || justification
                    // Passer les indices pour l'affichage en bleu
                    customIndices = cuisineData.indices || null
                  } else if (alertCriterionName === 'baignoire') {
                    const baignoireData = formatBaignoireCriterion(apartment)
                    customTitle = baignoireData.title || displayName
                    customDescription = baignoireData.description || justification
                    // Passer les indices pour l'affichage en bleu
                    customIndices = baignoireData.indices || null
                  } else if (alertCriterionName === 'hauteur_plafond') {
                    const hauteurData = formatHauteurPlafondCriterion(apartment)
                    customTitle = hauteurData.title || displayName
                    customDescription = hauteurData.description || justification
                    // Passer les indices pour l'affichage en bleu
                    customIndices = hauteurData.indices || null
                  } else if (alertCriterionName === 'large_piece_vie') {
                    const largePieceVieData = formatLargePieceVieCriterion(apartment)
                    customTitle = largePieceVieData.title || displayName
                    customDescription = largePieceVieData.description || justification
                    // Passer les indices pour l'affichage en bleu
                    customIndices = largePieceVieData.indices || null
                  } else {
                    // Critères simples (ascenseur, renove)
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
                        indices={expoData.indices}
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
                        indices={cuisineData.indices}
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
                        indices={baignoireData.indices}
                        confidence={baignoireData.confidence}
                        isGray={true}
                        noBorderBottom={noBorderBottom}
                      />
                    )
                  } else if (key === 'hauteur_plafond') {
                    const hauteurData = formatHauteurPlafondCriterion(apartment)
                    return (
                      <Criterion
                        key={key}
                        name={name}
                        score={hauteurData.score}
                        tier={hauteurData.tier}
                        customTitle={hauteurData.title}
                        customDescription={hauteurData.description}
                        indices={hauteurData.indices}
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
                        indices={largePieceVieData.indices}
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
          return (
            <>
              {(() => {
                const locData = formatLocalisation(apartment)
                return (
                  <Criterion 
                    name="Localisation"
                    score={apartment.scores_detaille?.localisation?.score || 0}
                    tier={apartment.scores_detaille?.localisation?.tier || 'tier3'}
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
              {(() => {
                const styleData = formatStyleCriterion(apartment)
                return (
                  <Criterion 
                    name="Style"
                    score={apartment.scores_detaille?.style?.score || 0}
                    tier={apartment.scores_detaille?.style?.tier || 'tier3'}
                    customTitle={styleData.title}
                    customDescription={styleData.description}
                    indices={styleData.indices}
                    confidence={apartment.style_analysis?.style?.confidence}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const expoData = formatExpositionCriterion(apartment, etage)
                let tier = apartment.scores_detaille?.ensoleillement?.tier || 'tier3'
                
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
                    indices={expoData.indices}
                    confidence={expoData.confidence}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const cuisineData = formatCuisineCriterion(apartment)
                const cuisineScore = apartment.scores_detaille?.cuisine || {}
                const cuisineScoreValue = cuisineScore.score !== undefined ? cuisineScore.score : (cuisineData.tier === 'tier1' ? 20 : cuisineData.tier === 'tier2' ? 10 : 0)
                
                return (
                  <Criterion 
                    name="Cuisine"
                    score={cuisineScoreValue}
                    tier={cuisineData.tier}
                    customTitle={cuisineData.title}
                    customDescription={cuisineData.description}
                    indices={cuisineData.indices}
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
                    indices={baignoireData.indices}
                    confidence={baignoireData.confidence}
                    isGray={!alertCriteria}
                  />
                )
              })()}
              {(() => {
                const hauteurData = formatHauteurPlafondCriterion(apartment)
                return (
                  <Criterion 
                    name="Hauteur plafond"
                    score={hauteurData.score}
                    tier={hauteurData.tier}
                    customTitle={hauteurData.title}
                    customDescription={hauteurData.description}
                    indices={hauteurData.indices}
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
                    indices={largePieceVieData.indices}
                    isGray={!alertCriteria}
                  />
                )
              })()}
            </>
          )
        })()}
      </div>
    </div>
  )
}

// Fonctions de formatage des critères
function formatLocalisation(apartment) {
  const metro = getMetroName(apartment)
  const quartier = getQuartierName(apartment)
  const mapInfo = apartment.map_info || {}
  const streets = mapInfo.streets || []
  
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
  
  // Construire le titre: "Metro Goncourt" (ou "Metro Belleville" si pas de métro mais quartier disponible)
  const titleParts = []
  if (metro) {
    titleParts.push(`Metro ${metro}`)
  } else if (quartier) {
    titleParts.push(`Metro ${quartier}`)
  }
  
  const title = titleParts.length > 0 ? titleParts.join(' · ') : 'Localisation'
  
  // Description: adresse exacte
  const description = rue || 'adresse non trouvée'
  const descriptionClass = null
  
  return {
    title,
    description,
    descriptionClass
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
  console.log('[DEBUG] formatPrixCriterion CALLED for apt:', apartment.id);
  // #region agent log
  const logData = {location:'ApartmentCard.jsx:formatPrixCriterion_entry',message:'Prix debug - formatPrixCriterion entry',data:{aptId:apartment.id,hasCriteria:!!apartment.criteria?.prix,hasCriteriaDisplay:!!apartment.criteria?.prix?.display,hasCriteriaDescription:!!apartment.criteria?.prix?.display?.description,criteriaDescription:apartment.criteria?.prix?.display?.description},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
  fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch(()=>{});
  // #endregion
  
  // PRIORITÉ: Utiliser les données normalisées depuis le backend si disponibles
  if (apartment.criteria?.prix?.display?.description) {
    const normalizedData = apartment.criteria.prix.display;
    // #region agent log
    console.log('[DEBUG] formatPrixCriterion using normalized data:', {
      aptId: apartment.id,
      description: normalizedData.description,
      title: normalizedData.title
    });
    fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:formatPrixCriterion_using_normalized',message:'Prix debug - using normalized data',data:{aptId:apartment.id,description:normalizedData.description,title:normalizedData.title},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
    return {
      title: normalizedData.title || 'Prix',
      description: normalizedData.description
    };
  }
  
  // #region agent log
  console.log('[DEBUG] formatPrixCriterion NOT using normalized data:', {
    aptId: apartment.id,
    hasCriteria: !!apartment.criteria,
    hasCriteriaPrix: !!apartment.criteria?.prix,
    hasCriteriaPrixDisplay: !!apartment.criteria?.prix?.display,
    hasDescription: !!apartment.criteria?.prix?.display?.description
  });
  // #endregion
  
  // Vérifier si le prix a été analysé
  const prixScore = apartment.scores_detaille?.prix
  const tier = prixScore?.tier || 'tier3'
  
  // Si pas encore analysé, afficher "Non analysé"
  if (!prixScore) {
    return {
      title: 'Prix du marché',
      description: 'Non analysé'
    }
  }
  
  // Titre selon le tier
  let title = 'Prix'
  if (tier === 'tier1') {
    title = 'Prix en dessous du marché'
  } else if (tier === 'tier2') {
    title = 'Prix du marché'
  } else {
    title = 'Prix au dessus du marché'
  }
  
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
      title,
      description: 'Non analysé'
    }
  }
  
  // Arrondir au 100€ près
  const prixM2Rounded = Math.round(prixM2 / 100) * 100
  
  // Récupérer le code postal depuis plusieurs sources
  let postalCode = apartment._api_data?.postal_code || ''
  if (!postalCode) {
    // Essayer depuis localisation
    const localisation = apartment.localisation || ''
    const postalMatch = localisation.match(/75\d{3}/)
    if (postalMatch) {
      postalCode = postalMatch[0]
    }
  }
  // Essayer aussi depuis map_info si disponible
  if (!postalCode && apartment.map_info?.postal_code) {
    postalCode = apartment.map_info.postal_code
  }
  
  // S'assurer que le code postal est une string
  if (postalCode) {
    postalCode = String(postalCode)
  }
  
  // Extraire l'arrondissement et le prix médian
  const arrondissementNum = getArrondissementNumber(postalCode)
  const medianPrice = getArrondissementMedianPrice(postalCode)
  
  // Formater le prix/m² avec espaces pour les milliers
  const prixM2Formatted = prixM2Rounded.toLocaleString('fr-FR')
  
  // Formater le prix médian avec espaces pour les milliers
  const medianPriceFormatted = medianPrice ? medianPrice.toLocaleString('fr-FR') : null
  
  // Formater selon le format demandé: "20e : 12000€/m² · haut dessus du marché"
  // Construire la description du tier
  let tierDescription = ''
  if (tier === 'tier1') {
    tierDescription = 'en dessous du marché'
  } else if (tier === 'tier2') {
    tierDescription = 'du marché'
  } else {
    tierDescription = 'haut dessus du marché'
  }
  
  // Formater le prix sans espaces pour les milliers (format compact: 12000 au lieu de 12 000)
  const prixM2Compact = prixM2Rounded.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '')
  
  // Formater le prix médian en format compact
  const medianPriceCompact = medianPrice ? medianPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '') : null
  
  let description = ''
  if (arrondissementNum && medianPriceCompact) {
    description = `${arrondissementNum}e : ${prixM2Compact}€/m² (médian: ${medianPriceCompact}€/m²) · ${tierDescription}`
  } else if (arrondissementNum) {
    description = `${arrondissementNum}e : ${prixM2Compact}€/m² · ${tierDescription}`
  } else if (medianPriceCompact) {
    description = `${prixM2Compact}€/m² (médian: ${medianPriceCompact}€/m²) · ${tierDescription}`
  } else {
    description = `${prixM2Compact}€/m² · ${tierDescription}`
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
  
  // Description: "Construit en X (si date dispo) + indices (moulures · parquet..)"
  const descriptionParts = []
  
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
        title = 'Style Haussmannien'
      } else if (year >= 1910 && year <= 1980) {
        // Calculer la décennie (ex: 1976 -> années 70)
        const decade = Math.floor(year / 10) * 10
        title = `Style années ${decade.toString().slice(-2)}`
      } else if (year > 1980) {
        title = 'Style Moderne'
      }
    }
    // Description: juste "Construit en XXXX" quand l'année est disponible
    descriptionParts.push(`Construit en ${anneeConstruction}`)
  } else {
    // Pas d'année trouvée, utiliser le style détecté par l'IA
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
  }
  
  // Indices du style (moulures, cheminée, etc.)
  // Ne les ajouter QUE si aucune année n'a été trouvée
  // Déclarer keywords en dehors du bloc pour qu'il soit accessible partout
  const keywords = []
  if (!anneeConstruction) {
    const details = styleData.details || ''
    const justification = styleData.justification || ''
    const textToSearch = `${details} ${justification}`.toLowerCase()
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

  }
  
  const description = descriptionParts.length > 0 ? descriptionParts.join(' · ') : null
  
  // Extraire les indices séparément pour l'affichage en bleu
  // Si on a une année, pas d'indices séparés (tout est dans la description)
  // Sinon, les indices sont les éléments détectés (moulures, parquet, etc.)
  let indices = null
  if (!anneeConstruction) {
    // Utiliser les indices depuis formatted_data si disponibles
    let styleIndices = apartment.formatted_data?.style?.indices
    if (styleIndices && styleIndices !== 'Style expo cuisine et baignoire') {
      let indicesClean = styleIndices
        .replace(/^Style Indice:\n?/i, '')
        .replace(/^Style:\n?/i, '')
        .replace(/Style\s+(?:haussmannien|neuf|atypique|70s|autre|inconnu)[\s·,]*/gi, '')
        .replace(/\([^)]*construction[^)]*\)/gi, '')
        .trim()
      
      if (indicesClean && !indicesClean.includes('Non spécifié') && indicesClean.length > 0) {
        indices = indicesClean
      } else if (keywords.length > 0) {
        indices = keywords.join(' · ')
      }
    } else if (keywords.length > 0) {
      indices = keywords.join(' · ')
    }
  }
  
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
      if (visavisCategory) {
        const categoryFr = translateCategory(visavisCategory)
        descriptionParts.push(`Vis a vis ${categoryFr} (${visavisDistance}m)`)
      } else {
        descriptionParts.push(`Vis a vis ${visavisDistance}m`)
      }
    } else {
      // Fallback: essayer d'extraire depuis les indices existants
      if (indices) {
        const visavisMatch = indices.match(/vis[-\sà]?[aà][-\sà]?vis\s+(\d+)\s*m/i)
        if (visavisMatch) {
          descriptionParts.push(`Vis a vis ${visavisMatch[1]}m`)
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
      if (visavisCategory) {
        const categoryFr = translateCategory(visavisCategory)
        descriptionParts.push(`Vis a vis ${categoryFr} (${visavisDistance}m)`)
      } else {
        descriptionParts.push(`Vis a vis ${visavisDistance}m`)
      }
    }
    
    indices = descriptionParts.length > 0 ? descriptionParts.join(' · ') : null
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
  
  // Description: null (les indices sont affichés séparément en bleu)
  // Les indices contiennent "1er étage · Vis a vis moyen (15m)"
  return {
    title,
    description: null,
    indices,
    confidence
  }
}

function formatCuisineCriterion(apartment) {
  // PRIORITÉ: Utiliser formatted_data depuis le backend (données enrichies)
  const cuisineFormatted = apartment.formatted_data?.cuisine
  // #region agent log
  fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1491',message:'formatCuisineCriterion entry - checking formatted_data.cuisine',data:{apartment_id:apartment.id,cuisineFormatted:cuisineFormatted,has_main_value:!!cuisineFormatted?.main_value},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
  // #endregion
  if (cuisineFormatted && cuisineFormatted.main_value) {
    const mainValue = cuisineFormatted.main_value
    const isOuverte = mainValue === 'Ouverte' || mainValue === 'Cuisine ouverte'
    const tier = isOuverte ? 'tier1' : 'tier3'
    // Chercher detected_photos pour ajouter le numéro d'image aux indices
    let indices = cuisineFormatted.indices || null
    let detectedPhotos = cuisineFormatted.detected_photos
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1500',message:'Using formatted_data.cuisine - checking detected_photos',data:{apartment_id:apartment.id,mainValue:mainValue,detectedPhotos:detectedPhotos,indices:indices},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    // Si on a detected_photos, ajouter le numéro d'image aux indices
    if (detectedPhotos && Array.isArray(detectedPhotos) && detectedPhotos.length > 0) {
      const photoNum = detectedPhotos[0]
      if (isOuverte) {
        indices = `Cuisine ouverte détectée image ${photoNum}`
      } else {
        indices = `Cuisine fermée détectée image ${photoNum}`
      }
    }
    const confidence = cuisineFormatted.confidence || null
    
    return {
      title: isOuverte ? 'Cuisine ouverte' : 'Cuisine fermée',
      description: null,
      indices,
      tier,
      confidence
    }
  }
  
  // Fallback: Utiliser scores_detaille si formatted_data n'existe pas
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
  
  // Indices: "Cuisine fermée détectée image X" (affiché en bleu)
  let indices = null
  
  // Chercher les photos détectées depuis plusieurs sources
  let detectedPhotos = []
  
  // Source 1: photo_validation.photo_result.detected_photos
  if (photoValidation.photo_result?.detected_photos) {
    detectedPhotos = photoValidation.photo_result.detected_photos
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1564',message:'Found detected_photos in photo_validation.photo_result',data:{apartment_id:apartment.id,detectedPhotos:detectedPhotos,source:'photo_validation.photo_result'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
  }
  
  // Source 2: style_analysis.cuisine.detected_photos
  if (detectedPhotos.length === 0) {
    const styleCuisine = apartment.style_analysis?.cuisine || {}
    if (styleCuisine.detected_photos && Array.isArray(styleCuisine.detected_photos)) {
      detectedPhotos = styleCuisine.detected_photos
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1571',message:'Found detected_photos in style_analysis.cuisine',data:{apartment_id:apartment.id,detectedPhotos:detectedPhotos,source:'style_analysis.cuisine'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
    }
  }
  
  // Source 3: formatted_data.cuisine.detected_photos
  if (detectedPhotos.length === 0) {
    const cuisineFormatted = apartment.formatted_data?.cuisine || {}
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1577',message:'Checking formatted_data.cuisine.detected_photos',data:{apartment_id:apartment.id,cuisineFormatted:cuisineFormatted,detected_photos:cuisineFormatted.detected_photos,detected_photos_type:typeof cuisineFormatted.detected_photos,is_array:Array.isArray(cuisineFormatted.detected_photos)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    if (cuisineFormatted.detected_photos && Array.isArray(cuisineFormatted.detected_photos)) {
      detectedPhotos = cuisineFormatted.detected_photos
    }
  }
  
  // Source 4: extraire depuis formatted_data.cuisine.indices
  if (detectedPhotos.length === 0) {
    const cuisineIndices = apartment.formatted_data?.cuisine?.indices
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1585',message:'Extracting image number from indices',data:{apartment_id:apartment.id,cuisineIndices:cuisineIndices,imageMatch:cuisineIndices ? cuisineIndices.match(/image\s*(\d+)/i) : null},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    if (cuisineIndices && cuisineIndices !== 'Style expo cuisine et baignoire') {
      // Extraire le numéro d'image depuis les indices (format: "Cuisine ouverte détectée image 2")
      const imageMatch = cuisineIndices.match(/image\s*(\d+)/i)
      if (imageMatch) {
        detectedPhotos = [parseInt(imageMatch[1], 10)]
      }
    }
  }
  
  // #region agent log
  fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1595',message:'Final detectedPhotos check before setting indices',data:{apartment_id:apartment.id,detectedPhotos:detectedPhotos,detectedPhotos_length:detectedPhotos.length,cuisineOuverte:cuisineOuverte},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
  // #endregion
  if (detectedPhotos.length > 0) {
    const photoNum = detectedPhotos[0]
    if (cuisineOuverte) {
      indices = `Cuisine ouverte détectée image ${photoNum}`
    } else {
      indices = `Cuisine fermée détectée image ${photoNum}`
    }
  } else {
    // Fallback: utiliser les indices depuis formatted_data sans numéro d'image
    const cuisineIndices = apartment.formatted_data?.cuisine?.indices
    if (cuisineIndices && cuisineIndices !== 'Style expo cuisine et baignoire') {
      // Nettoyer le préfixe "Cuisine Indice:" et extraire le contenu
      let cleanedIndices = cuisineIndices
        .replace(/^Cuisine Indice:\s*/i, '')
        .replace(/^Cuisine:\s*/i, '')
        .trim()
      if (cleanedIndices) {
        indices = cleanedIndices
      }
    }
  }
  
  // Récupérer la confiance depuis cuisineDetails ou style_analysis
  const confidence = cuisineDetails.confidence || apartment.style_analysis?.cuisine?.confidence
  
  return {
    title,
    description: null,
    indices,
    tier,
    confidence
  }
}

function formatBaignoireCriterion(apartment) {
  // PRIORITÉ: Utiliser formatted_data depuis le backend (données enrichies)
  const baignoireFormatted = apartment.formatted_data?.baignoire
  if (baignoireFormatted && baignoireFormatted.main_value) {
    const mainValue = baignoireFormatted.main_value
    const hasBaignoire = mainValue === 'Oui' || mainValue === 'Baignoire'
    const tier = hasBaignoire ? 'tier1' : 'tier3'
    let indices = baignoireFormatted.indices || null
    let detectedPhotos = baignoireFormatted.detected_photos
    // Si on a detected_photos, ajouter le numéro d'image aux indices (comme pour cuisine)
    if (detectedPhotos && Array.isArray(detectedPhotos) && detectedPhotos.length > 0) {
      const photoNum = detectedPhotos[0]
      if (hasBaignoire) {
        indices = `Baignoire détectée image ${photoNum}`
      } else {
        indices = `Douche détectée image ${photoNum}`
      }
    }
    const confidence = baignoireFormatted.confidence || null
    
    let title = 'Baignoire'
    let description = null
    // Nettoyer les indices pour l'affichage en bleu
    if (indices && indices !== 'Style expo cuisine et baignoire') {
      let cleanedIndices = indices
        .replace(/^Baignoire Indice:\s*/i, '')
        .replace(/^Baignoire:\s*/i, '')
        .trim()
      if (cleanedIndices && !cleanedIndices.toLowerCase().includes('non spécifié')) {
        // Les indices seront affichés en bleu, pas besoin de description
        indices = cleanedIndices
      } else {
        indices = null
        description = 'info non disponible'
      }
    }
    
    return {
      title,
      description,
      indices,
      tier,
      score: hasBaignoire ? 20 : 0,
      confidence
    }
  }
  
  // Fallback: Utiliser scores_detaille si formatted_data n'existe pas
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
    indices = null
  } else {
    // Construire les indices avec distinction claire entre "information non disponible" et "trouvé dans image X"
    // Les résultats IA doivent être dans indices (affichés en bleu)
    if (!indices || indices === 'Style expo cuisine et baignoire') {
      if (photosAnalyzed && detectedPhotos.length > 0) {
        // Photos analysées et quelque chose détecté
        const photosStr = detectedPhotos.map(p => `image ${p}`).join(', ')
        if (photoHasBaignoire === true) {
          indices = `Baignoire détectée ${photosStr}`
        } else if (photoHasDouche === true) {
          indices = `Douche détectée ${photosStr}`
        } else {
          description = 'info non disponible'
          indices = null
        }
      } else if (photosAnalyzed) {
        // Photos analysées mais rien détecté
        description = 'info non disponible'
        indices = null
      } else {
        // Pas de photos analysées
        const justification = baignoireScore.justification || ''
        if (justification) {
          const justificationLower = justification.toLowerCase()
          if (justificationLower.includes('photo') || justificationLower.includes('détectée') || justificationLower.includes('analysée')) {
            if (hasBaignoire) {
              indices = 'Baignoire détectée'
            } else {
              indices = 'Douche détectée'
            }
          } else if (justificationLower.includes('description') || justificationLower.includes('caractéristiques')) {
            // Texte mentionné, pas un résultat IA, donc description
            if (hasBaignoire) {
              description = 'Baignoire mentionnée dans le texte'
            } else {
              description = 'Douche mentionnée dans le texte'
            }
            indices = null
          } else if (justification.length < 100) {
            description = justification
            indices = null
          } else {
            description = 'info non disponible'
            indices = null
          }
        } else {
          description = 'info non disponible'
          indices = null
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
        indices = null
      } else {
        // Si les indices contiennent "détectée" mais pas de numéro d'image, essayer d'ajouter les numéros
        if (cleanedIndices.includes('détectée') && !cleanedIndices.includes('image') && detectedPhotos.length > 0) {
          const photosStr = detectedPhotos.map(p => `image ${p}`).join(', ')
          if (cleanedIndices.includes('Baignoire')) {
            indices = `Baignoire détectée ${photosStr}`
          } else if (cleanedIndices.includes('Douche')) {
            indices = `Douche détectée ${photosStr}`
          } else {
            indices = cleanedIndices
          }
        } else {
          indices = cleanedIndices
        }
      }
    }
  }
  
  return {
    title,
    description,
    indices,
    tier,
    score,
    confidence: confidencePct
  }
}

function formatCalmeCriterion(apartment) {
  // PRIORITÉ: Utiliser formatted_data depuis le backend (données enrichies)
  const calmeFormatted = apartment.formatted_data?.calme
  if (calmeFormatted && calmeFormatted.main_value) {
    const mainValue = calmeFormatted.main_value
    let tier = 'tier3'
    let title = 'Calme'
    
    if (mainValue === 'Calme' || mainValue === 'Très calme') {
      tier = 'tier1'
      title = 'Calme'
    } else if (mainValue === 'Moyennement calme') {
      tier = 'tier2'
      title = 'Moyennement calme'
    } else {
      tier = 'tier3'
      title = 'Animé'
    }
    
    const indices = calmeFormatted.indices || ''
    let description = indices
      .replace(/^Calme Indice:\s*/i, '')
      .replace(/^Calme:\s*/i, '')
      .trim()
    
    if (!description) {
      description = 'Non spécifié'
    }
    
    return {
      title,
      description,
      tier,
      score: tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
    }
  }
  
  // Fallback: Utiliser scores_detaille si formatted_data n'existe pas
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
  // PRIORITÉ ABSOLUE: Utiliser les données normalisées depuis le backend si disponibles
  if (apartment.criteria?.piece_vie?.display?.indices) {
    let normalizedIndices = apartment.criteria.piece_vie.display.indices
    const normalizedTitle = apartment.criteria.piece_vie.display.title
    const normalizedTier = apartment.criteria.piece_vie.tier
    const normalizedScore = apartment.criteria.piece_vie.score || 0
    
    // Vérifier si le pourcentage est présent dans les indices normalisés
    const hasPourcentageInIndices = normalizedIndices && (
      normalizedIndices.includes('% de la surface totale') ||
      normalizedIndices.includes('% de l\'appartement')
    )
    
    // Si le pourcentage n'est pas présent, chercher dans scores_detaille comme fallback
    if (!hasPourcentageInIndices) {
      const scoresDetaille = apartment.scores_detaille || {}
      const largePieceVieScore = scoresDetaille.large_piece_vie || {}
      const details = largePieceVieScore.details || {}
      if (details.pourcentage_salon !== undefined && details.pourcentage_salon !== null) {
        const pourcentage = parseFloat(details.pourcentage_salon)
        if (!isNaN(pourcentage)) {
          // Ajouter le pourcentage aux indices existants ou le créer
          if (normalizedIndices && normalizedIndices.trim()) {
            normalizedIndices = `${normalizedIndices} · ${pourcentage.toFixed(1)}% de la surface totale de l'appartement`
          } else {
            normalizedIndices = `${pourcentage.toFixed(1)}% de la surface totale de l'appartement`
          }
        }
      }
    }
    return {
      title: normalizedTitle,
      description: apartment.criteria.piece_vie.display.description,
      indices: normalizedIndices,
      tier: normalizedTier,
      score: normalizedScore
    }
  }
  
  // PRIORITÉ 2: Utiliser formatted_data depuis le backend (données enrichies)
  const pieceVieFormatted = apartment.formatted_data?.piece_vie
  if (pieceVieFormatted && pieceVieFormatted.main_value) {
    const mainValue = pieceVieFormatted.main_value
    const indicesRaw = pieceVieFormatted.indices || ''
    // Nettoyer les indices (retirer préfixe et garder le contenu)
    let cleanedIndices = indicesRaw
      .replace(/^Pièce de vie Indice:\s*/i, '')
      .replace(/^Pièce de vie:\s*/i, '')
      .trim()
    // Utiliser le main_value comme titre (ex: "Grande pièce de vie")
    let title = mainValue
    
    // Extraire le pourcentage ou les m² depuis les indices pour les mettre dans indices (affichés en bleu)
    let indices = null
    let description = null
    
    // Chercher d'abord le pourcentage (% de la surface totale) dans les indices
    const pourcentageMatch = cleanedIndices.match(/(\d+[.,]?\d*)%\s*de\s*la\s*surface\s*totale/i)
    if (pourcentageMatch) {
      indices = `${pourcentageMatch[1]}% de la surface totale de l'appartement`
      // Garder la description complète aussi si elle contient plus d'infos
      if (cleanedIndices.length > pourcentageMatch[0].length + 10) {
        description = cleanedIndices
      }
    } else {
      // Fallback: chercher le pourcentage dans scores_detaille.large_piece_vie.details.pourcentage_salon
      const scoresDetaille = apartment.scores_detaille || {}
      const largePieceVieScore = scoresDetaille.large_piece_vie || {}
      const details = largePieceVieScore.details || {}
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1992',message:'Checking scores_detaille fallback',data:{aptId:apartment.id,pourcentageSalon:details.pourcentage_salon,detailsKeys:Object.keys(details)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
      if (details.pourcentage_salon !== undefined && details.pourcentage_salon !== null) {
        const pourcentage = parseFloat(details.pourcentage_salon)
        if (!isNaN(pourcentage)) {
          indices = `${pourcentage.toFixed(1)}% de la surface totale de l'appartement`
          // #region agent log
          fetch('http://127.0.0.1:7245/ingest/2c47b0d2-1884-4c79-97f0-cc01bf783507',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ApartmentCard.jsx:1999',message:'Found pourcentage in scores_detaille',data:{aptId:apartment.id,pourcentage,indices},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
          // #endregion
          // Si les indices nettoyés contiennent plus d'infos, les mettre dans description
          if (cleanedIndices && cleanedIndices.length > 50) {
            description = cleanedIndices
          }
        }
      }
      
      // Si toujours pas de pourcentage, chercher les m² dans les indices (ex: "28m²" ou "environ 28m²")
      if (!indices) {
        const m2Match = cleanedIndices.match(/(?:environ\s*)?(\d+[.,]?\d*)\s*m²/i)
        let tailleM2 = m2Match ? parseFloat(m2Match[1].replace(',', '.')) : null
        
        // Si pas trouvé dans les indices, chercher dans piece_vie.taille_m2
        if (!tailleM2) {
          const pieceVieData = apartment.piece_vie || {}
          tailleM2 = pieceVieData.taille_m2
        }
        
        // Si on a la taille en m², essayer de calculer le pourcentage depuis la surface totale
        if (tailleM2) {
          const surface = apartment.surface || ''
          const surfaceMatch = surface.match(/(\d+)/)
          if (surfaceMatch) {
            const surfaceTotale = parseFloat(surfaceMatch[1])
            if (surfaceTotale > 0) {
              const pourcentage = (tailleM2 / surfaceTotale * 100).toFixed(1)
              indices = `${pourcentage}% de la surface totale de l'appartement`
              // Si la description complète est longue, la mettre dans description
              if (cleanedIndices.length > 150) {
                description = cleanedIndices
              }
            } else if (m2Match) {
              // Pas de surface totale, afficher juste les m²
              indices = `${tailleM2.toFixed(0)}m²`
              if (cleanedIndices.length > 150) {
                description = cleanedIndices
              }
            }
          } else if (m2Match) {
            // Pas de surface totale, afficher juste les m²
            indices = `${tailleM2.toFixed(0)}m²`
            if (cleanedIndices.length > 150) {
              description = cleanedIndices
            }
          }
        }
        
        // Si toujours pas d'indices, utiliser les indices nettoyés
        if (!indices) {
          if (cleanedIndices && !cleanedIndices.toLowerCase().includes('non spécifié')) {
            if (cleanedIndices.length < 100) {
              // Version courte: mettre dans indices
              indices = cleanedIndices
            } else {
              // Version longue: mettre dans description
              description = cleanedIndices
            }
          } else {
            description = 'Non spécifié'
          }
        }
      }
    }
    
    // Si pas d'indices ni description, mettre "Non spécifié"
    if (!indices && !description) {
      description = 'Non spécifié'
    }
    
    // Récupérer le tier et le score depuis scores_detaille si disponible
    const scoresDetaille = apartment.scores_detaille || {}
    const largePieceVieScore = scoresDetaille.large_piece_vie || {}
    const tier = largePieceVieScore.tier || 'tier3'
    const score = largePieceVieScore.score || 0
    
    return {
      title,
      description,
      indices,
      tier,
      score
    }
  }
  
  // Fallback: Utiliser scores_detaille si formatted_data n'existe pas
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
  let description = null
  let indices = null
  
  // Les résultats IA (% de la surface totale) doivent être dans indices (affichés en bleu)
  if (details.pourcentage_salon !== undefined) {
    const pourcentage = details.pourcentage_salon
    if (pourcentage !== null && pourcentage !== undefined) {
      indices = `${pourcentage.toFixed(1)}% de la surface totale de l'appartement`
    }
  }
  
  // Si pas de pourcentage, utiliser formatted_data
  if (!indices && apartment.formatted_data?.piece_vie) {
    const pieceVieFormatted = apartment.formatted_data.piece_vie
    const pieceVieIndices = pieceVieFormatted.indices
    if (pieceVieIndices) {
      // Nettoyer le préfixe "Pièce de vie Indice:" si présent
      let cleanedIndices = pieceVieIndices
        .replace(/^Pièce de vie Indice:\s*/i, '')
        .replace(/^Pièce de vie:\s*/i, '')
        .trim()
      // Chercher le pourcentage dans les indices
      const pourcentageMatch = cleanedIndices.match(/(\d+[.,]?\d*)%\s*de\s*la\s*surface\s*totale/i)
      if (pourcentageMatch) {
        // S'assurer que "de l'appartement" est présent
        if (!cleanedIndices.includes('de l\'appartement')) {
          indices = `${pourcentageMatch[1]}% de la surface totale de l'appartement`
        } else {
          indices = cleanedIndices
        }
      } else {
        // Si pas de pourcentage mais qu'on a des indices, les utiliser quand même
        // (peut contenir la taille en m²)
        if (cleanedIndices && cleanedIndices !== 'Non spécifié') {
          indices = cleanedIndices
        }
      }
    }
  }
  
  // Fallback: chercher dans style_analysis.piece_vie directement
  if (!indices) {
    const styleAnalysis = apartment.style_analysis || {}
    const pieceVieStyle = styleAnalysis.piece_vie || {}
    const tailleM2 = pieceVieStyle.taille_m2
    const details = pieceVieStyle.details || {}
    const pourcentage = details.pourcentage_salon || details.pourcentage
    
    if (tailleM2 || pourcentage) {
      const indicesParts = []
      if (tailleM2) {
        try {
          indicesParts.push(`${parseFloat(tailleM2).toFixed(0)}m²`)
        } catch (e) {
          // Ignorer les erreurs de parsing
        }
      }
      if (pourcentage) {
        try {
          indicesParts.push(`${parseFloat(pourcentage).toFixed(1)}% de la surface totale de l'appartement`)
        } catch (e) {
          // Ignorer les erreurs de parsing
        }
      }
      if (indicesParts.length > 0) {
        indices = indicesParts.join(' · ')
      }
    }
  }
  
  // Si pas de résultats IA, utiliser la justification comme description (pas IA)
  if (!indices && justification) {
    description = justification
  } else if (!indices) {
    description = 'Non spécifié'
  }
  
  return {
    title,
    description,
    indices,
    tier,
    score: largePieceVieScore.score || 0
  }
}

function formatHauteurPlafondCriterion(apartment) {
  const scoresDetaille = apartment.scores_detaille || {}
  const hauteurScore = scoresDetaille.hauteur_plafond || {}
  
  // Extraire la hauteur depuis différentes sources (priorité: formatted_data > analyses > style_analysis > scores_detaille)
  let hauteurEstimee = null
  let tier = 'tier3'
  let justification = ''
  let hauteurFormatted = null
  
  // PRIORITÉ 1: Chercher dans formatted_data.hauteur_plafond (données enrichies)
  // Fallback: chercher aussi dans formatted_data.hauteur (ancien format)
  if (apartment.formatted_data?.hauteur_plafond) {
    hauteurFormatted = apartment.formatted_data.hauteur_plafond
  } else if (apartment.formatted_data?.hauteur) {
    // Support de l'ancien format pour compatibilité
    hauteurFormatted = apartment.formatted_data.hauteur
  }
  
  if (hauteurFormatted) {
    const indices = hauteurFormatted.indices || ''
    // Extraire la hauteur depuis les indices (ex: "Moyenne 2,70m") ou main_value (ex: "2,55m")
    let match = indices.match(/(\d+[.,]\d+)\s*m/i)
    if (!match && hauteurFormatted.main_value) {
      match = hauteurFormatted.main_value.match(/(\d+[.,]\d+)\s*m/i)
    }
    if (match) {
      hauteurEstimee = parseFloat(match[1].replace(',', '.'))
    }
  }
  
  // PRIORITÉ 2: Chercher dans analyses.hauteur_plafond
  if (!hauteurEstimee) {
    const analyses = apartment.analyses || {}
    const hauteurData = analyses.hauteur_plafond || {}
    hauteurEstimee = hauteurData.hauteur_estimee || hauteurData.hauteur_estimate
  }
  
  // PRIORITÉ 3: Chercher dans style_analysis.hauteur_plafond
  if (!hauteurEstimee) {
    const styleAnalysis = apartment.style_analysis || {}
    const hauteurStyle = styleAnalysis.hauteur_plafond || {}
    hauteurEstimee = hauteurStyle.value
    // Fallback: chercher dans style_analysis.style.hauteur_plafond_estimee
    if (!hauteurEstimee) {
      const styleData = styleAnalysis.style || {}
      hauteurEstimee = styleData.hauteur_plafond_estimee
    }
  }
  
  // PRIORITÉ 4: Chercher dans scores_detaille.hauteur_plafond (justification)
  if (!hauteurEstimee && hauteurScore && Object.keys(hauteurScore).length > 0) {
    tier = hauteurScore.tier || 'tier3'
    justification = hauteurScore.justification || ''
    if (justification) {
      // Chercher un pattern comme "2.80m" ou "2,80m" dans la justification
      const match = justification.match(/(\d+[.,]\d+)\s*m/i)
      if (match) {
        hauteurEstimee = parseFloat(match[1].replace(',', '.'))
      }
    }
  }
  
  // Si pas encore analysé, afficher "Non analysé"
  if (!hauteurEstimee && (!hauteurScore || Object.keys(hauteurScore).length === 0)) {
    return {
      title: 'Hauteur plafond',
      description: 'Non analysé',
      tier: 'tier3',
      score: 0
    }
  }
  
  // Si on a une hauteur mais pas de tier, le calculer depuis la hauteur
  if (hauteurEstimee && (!hauteurScore || Object.keys(hauteurScore).length === 0)) {
    if (hauteurEstimee >= 2.80) {
      tier = 'tier1'
    } else if (hauteurEstimee >= 2.50) {
      tier = 'tier2'
    } else {
      tier = 'tier3'
    }
  } else if (hauteurScore && Object.keys(hauteurScore).length > 0) {
    tier = hauteurScore.tier || 'tier3'
    justification = hauteurScore.justification || ''
  }
  
  // Titre selon le tier et la hauteur
  let title = 'Hauteur plafond'
  if (hauteurEstimee) {
    if (hauteurEstimee >= 2.80) {
      title = 'Belle hauteur plafond'
    } else {
      // Format avec virgule pour les décimales (format français)
      title = `${hauteurEstimee.toFixed(2).replace('.', ',')}m`
    }
  } else {
    if (tier === 'tier1') {
      title = 'Belle hauteur plafond'
    } else if (tier === 'tier2') {
      title = 'Hauteur plafond'
    } else {
      title = 'Hauteur plafond'
    }
  }
  
  // Description depuis la justification ou formatted_data
  let description = null
  let indices = null
  
  // PRIORITÉ: Utiliser formatted_data.hauteur_plafond ou hauteur (données enrichies du backend)
  // Les résultats IA doivent être dans indices (affichés en bleu)
  if (hauteurFormatted) {
    const hauteurIndices = hauteurFormatted.indices
    if (hauteurIndices) {
      // Nettoyer le préfixe "Hauteur Indice:" si présent
      let cleanedIndices = hauteurIndices.replace(/^Hauteur Indice:\s*/i, '').trim()
      if (cleanedIndices && cleanedIndices !== 'Non spécifié') {
        indices = cleanedIndices
      }
    }
    // Si pas d'indices mais qu'on a main_value, l'utiliser
    if (!indices && hauteurFormatted.main_value) {
      const mainValueMatch = hauteurFormatted.main_value.match(/(\d+[.,]\d+)\s*m/i)
      if (mainValueMatch) {
        indices = hauteurFormatted.main_value
      }
    }
  }
  
  // Fallback: utiliser la hauteur estimée si pas d'indices depuis formatted_data
  if (!indices && hauteurEstimee) {
    indices = `Hauteur moyenne ${hauteurEstimee.toFixed(2).replace('.', ',')}m`
  }
  
  // Si pas de hauteur estimée, utiliser la justification comme description (pas IA)
  if (!indices && justification) {
    description = justification
  } else if (!indices) {
    description = 'Non spécifié'
  }
  
  return {
    title,
    description,
    indices,
    tier,
    score: hauteurScore.score || 0
  }
}

// Mapping des critères vers leurs emojis
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
  
  // Classes pour la description (bleu si analyse IA, sinon utiliser descriptionClass)
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
            {description && (
              <div className={`criterion-description ${descriptionClassFinal}`}>
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
