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
            {apartment.scores_detaille.style && (() => {
              // Récupérer les indices depuis formatted_data (backend) ou utiliser fallback
              let styleIndices = apartment.formatted_data?.style?.indices
              
              // Si les indices viennent du backend mais sont null/undefined/vide, ne pas utiliser
              if (styleIndices === null || styleIndices === undefined || styleIndices === '') {
                styleIndices = null
              }
              
              // Fallback: chercher dans style_analysis si pas disponible depuis backend
              if (!styleIndices) {
                const styleAnalysis = apartment.style_analysis || {}
                const styleData = styleAnalysis.style || {}
                const details = styleData.details || ''
                const justification = styleData.justification || ''
                const styleType = styleData.type || ''
                
                // Chercher dans details et justification
                const textToSearch = `${details} ${justification}`.toLowerCase()
                
                // Déterminer les keywords selon le tier
                const tier = apartment.scores_detaille.style.tier || 'tier3'
                let keywords = []
                
                if (tier === 'tier1') {
                  // Ancien
                  keywords = ['moulures', 'cheminée', 'parquet', 'hauteur sous plafond', 'moldings', 'fireplace', 'balcon fer forgé', 'corniche', 'rosace']
                } else if (tier === 'tier2') {
                  // Atypique
                  keywords = ['loft', 'atypique', 'unique', 'original', 'espace ouvert', 'volume généreux', 'caractère unique', 'poutres', 'béton brut', 'entrepôt', 'atelier']
                } else {
                  // Neuf
                  keywords = ['moderne', 'contemporain', 'récent', 'terrasse', 'vue', 'carrelage', 'fenêtre moderne', 'balcon', 'ascenseur']
                }
                
                const foundKeywords = keywords.filter(kw => textToSearch.includes(kw.toLowerCase()))
                if (foundKeywords.length > 0) {
                  styleIndices = "Style Indice: " + foundKeywords.slice(0, 3).join(" · ")
                } else if (styleType && styleType !== 'autre' && styleType !== 'inconnu') {
                  // Utiliser le type de style comme indice
                  let styleName = styleType.charAt(0).toUpperCase() + styleType.slice(1)
                  if (styleType.includes('70') || styleType.toLowerCase().includes('seventies')) {
                    styleName = "Années 70"
                  }
                  styleIndices = "Style Indice: " + styleName
                }
              }
              
              // Filtrer le fallback "Style expo cuisine et baignoire" s'il apparaît encore
              if (styleIndices && styleIndices.includes('Style expo cuisine et baignoire')) {
                styleIndices = null
              }
              
              return (
                <Criterion 
                  name="Style"
                  score={apartment.scores_detaille.style.score || 0}
                  tier={apartment.scores_detaille.style.tier || 'tier3'}
                  value={formatStyleCriterion(apartment)}
                  indices={styleIndices}
                  confidence={apartment.style_analysis?.style?.confidence}
                />
              )
            })()}
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
                  confidence={expoData.confidence}
                />
              )
            })()}
            {apartment.scores_detaille.cuisine && (() => {
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
              
              // Si toujours None OU si conflit, vérifier le tier pour déduire (tier = résultat final après validation)
              if (cuisineOuverte === null || cuisineOuverte === undefined || validationStatus === 'conflict') {
                const tier = cuisineScore.tier || 'tier3'
                // tier1 = ouverte (10pts), tier3 = fermée (0pts)
                // En cas de conflit, le tier représente le résultat final après validation croisée
                cuisineOuverte = (tier === 'tier1')
              }
              
              const cuisineValue = cuisineOuverte ? 'Ouverte' : 'Fermée'
              let tier = cuisineScore.tier || 'tier3'
              
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
              
              // Récupérer les indices depuis formatted_data (backend) ou utiliser fallback
              const cuisineIndices = apartment.formatted_data?.cuisine?.indices || "Style expo cuisine et baignoire"
              
              // Récupérer la confiance depuis cuisineDetails ou style_analysis
              const confidence = cuisineDetails.confidence || apartment.style_analysis?.cuisine?.confidence
              
              return (
                <Criterion 
                  name="Cuisine"
                  score={scoreFromTier}
                  tier={tier}
                  value={cuisineValue}
                  indices={cuisineIndices}
                  confidence={confidence}
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
  // Utiliser les données formatées depuis le backend si disponibles
  if (apartment.formatted_data?.exposition) {
    return {
      mainValue: apartment.formatted_data.exposition.main_value || 'Sombre',
      indices: apartment.formatted_data.exposition.indices || null,
      confidence: apartment.formatted_data.exposition.confidence || null
    }
  }
  
  // Fallback: utiliser directement apartment.exposition si disponible
  const exposition = apartment.exposition || {}
  const expositionDir = exposition.exposition || ''
  
  // Classifier l'orientation pour déterminer mainValue
  let mainValue = 'Luminosité moyenne' // Par défaut
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
  
  // Construire les indices
  const indices = []
  if (etage) {
    indices.push(etage)
  }
  
  // Ajouter exposition directionnelle UNIQUEMENT si explicitement mentionnée dans le texte
  const expositionExplicite = exposition.exposition_explicite || false
  if (expositionExplicite && expositionDir && !['inconnue', 'inconnu', 'non spécifiée', 'none', 'null'].includes(expositionDir.toLowerCase())) {
    // Formater avec majuscules : "sud" -> "Sud", "sud-ouest" -> "Sud-Ouest"
    const formattedDir = expositionDir
      .replace(/_/g, '-')
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join('-')
    indices.push(`Exposé ${formattedDir}`)
  }
  
  // Ajouter brightness_value si disponible
  const brightnessValue = exposition.details?.brightness_value || exposition.details?.image_brightness
  if (brightnessValue !== null && brightnessValue !== undefined) {
    indices.push(`Luminosité ${brightnessValue.toFixed(1)}`)
  }
  
  return {
    mainValue,
    indices: indices.length > 0 ? indices.join(' · ') : null,
    confidence: exposition.confidence || null
  }
}

function formatBaignoireCriterion(apartment) {
  // PRIORITÉ: Utiliser formatted_data depuis le backend (comme pour cuisine)
  // Récupérer les indices depuis formatted_data (backend) en priorité
  let indices = apartment.formatted_data?.baignoire?.indices || null
  
  // Utiliser les scores depuis scores_detaille.baignoire
  const scoresDetaille = apartment.scores_detaille || {}
  const baignoireScore = scoresDetaille.baignoire || {}
  
  // Récupérer le score et le tier depuis scores_detaille
  const score = baignoireScore.score || 0
  const tier = baignoireScore.tier || 'tier3'
  
  // Chercher les données baignoire depuis différentes sources pour les détails
  const baignoireData = apartment.baignoire_data || apartment.baignoire || {}
  const hasBaignoire = baignoireData.has_baignoire || baignoireData.has_baignoire === true
  const confidence = baignoireData.confidence || baignoireScore.details?.confidence || 0
  
  // Valeur principale - utiliser formatted_data si disponible, sinon déduire depuis hasBaignoire
  let mainValue = apartment.formatted_data?.baignoire?.main_value
  if (!mainValue) {
    mainValue = hasBaignoire ? 'Oui' : 'Non'
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
  
  // Fallback sur justification si formatted_data n'est pas disponible
  if (!indices) {
    const justification = baignoireScore.justification || ''
    if (justification) {
      const justificationLower = justification.toLowerCase()
      if (justificationLower.includes('photo') || justificationLower.includes('détectée') || justificationLower.includes('analysée')) {
        if (hasBaignoire) {
          indices = 'Analyse photo : Baignoire détectée'
        } else {
          indices = 'Analyse photo : Douche détectée'
        }
      } else if (justificationLower.includes('description') || justificationLower.includes('caractéristiques')) {
        if (hasBaignoire) {
          indices = 'Baignoire mentionnée dans le texte'
        } else {
          indices = 'Douche mentionnée dans le texte'
        }
      } else if (justification.length < 100) {
        indices = justification
      }
    }
    
    // Dernier fallback
    if (!indices) {
      indices = 'Style expo cuisine et baignoire'
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
            <div className="criterion-sub-details">
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
              <span className="indices-text">
                {displayIndices
                  .replace(/^Style Indice: /, '')
                  .replace(/^Expo Indice: /, '')
                  .replace(/^Cuisine Indice: /, '')
                  .replace(/^Baignoire Indice: /, '')
                  .replace(/^Baignoire: /, '')}
              </span>
            </div>
          )}
        </div>
      </div>
      <span className={`criterion-score-badge ${badgeClass}`}>{score} pts</span>
    </div>
  )
}

export default ApartmentCard

