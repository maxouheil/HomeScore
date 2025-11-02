// Fonctions utilitaires pour calculer les scores

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
  
  return {
    mainValue
  }
}

/**
 * Calcule le mega score d'un appartement en utilisant la même logique que l'affichage
 */
export function calculateMegaScore(apartment) {
  let score = 0
  const scores = apartment.scores_detaille || {}
  
  // Localisation
  if (scores.localisation) {
    score += scores.localisation.score || 0
  }
  
  // Prix
  if (scores.prix) {
    score += scores.prix.score || 0
  }
  
  // Style
  if (scores.style) {
    score += scores.style.score || 0
  }
  
  // Exposition - utiliser le score corrigé selon le tier (même logique que l'affichage)
  if (scores.ensoleillement) {
    const etage = getEtage(apartment)
    const expoData = formatExpositionCriterion(apartment, etage)
    let tier = scores.ensoleillement.tier || 'tier3'
    
    // Vérifier la cohérence entre la valeur affichée et le tier
    if (expoData.mainValue === 'Lumineux' && tier !== 'tier1') {
      tier = 'tier1'
    } else if (expoData.mainValue === 'Luminosité moyenne' && tier !== 'tier2') {
      tier = 'tier2'
    } else if (expoData.mainValue === 'Sombre' && tier !== 'tier3') {
      tier = 'tier3'
    }
    
    // Calculer le score selon le tier
    const scoreFromTier = tier === 'tier1' ? 20 : tier === 'tier2' ? 10 : 0
    score += scoreFromTier
  }
  
  // Cuisine - utiliser le score corrigé selon le tier (même logique que l'affichage)
  if (scores.cuisine) {
    const cuisineValue = apartment.style_analysis?.cuisine?.ouverte ? 'Ouverte' : 'Fermée'
    let tier = scores.cuisine.tier || 'tier3'
    
    // Vérifier la cohérence entre la valeur affichée et le tier
    if (cuisineValue === 'Ouverte' && tier !== 'tier1') {
      tier = 'tier1'
    }
    if (cuisineValue === 'Fermée' && tier !== 'tier3') {
      tier = 'tier3'
    }
    
    // Calculer le score selon le tier
    const scoreFromTier = tier === 'tier1' ? 10 : tier === 'tier2' ? 5 : 0
    score += scoreFromTier
  }
  
  // Baignoire
  if (scores.baignoire) {
    score += scores.baignoire.score || 0
  }
  
  return Math.round(score * 10) / 10
}

