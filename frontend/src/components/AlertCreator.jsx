import { useState, useRef, useMemo, useCallback } from 'react'
import React from 'react'
import './AlertCreator.css'

// Base de données des quartiers, arrondissements et métros de Paris
const PARIS_LOCATIONS = [
  // Arrondissements (tous les 20)
  'Paris 1er', 'Paris 2e', 'Paris 3e', 'Paris 4e', 'Paris 5e', 'Paris 6e', 'Paris 7e', 'Paris 8e',
  'Paris 9e', 'Paris 10e', 'Paris 11e', 'Paris 12e', 'Paris 13e', 'Paris 14e', 'Paris 15e', 'Paris 16e',
  'Paris 17e', 'Paris 18e', 'Paris 19e', 'Paris 20e',
  // Quartiers populaires
  'Belleville', 'Ménilmontant', 'Place de la Réunion', 'Alexandre Dumas', 'Philippe Auguste', 'Avron',
  'Buttes-Chaumont', 'Place des Fêtes', 'Pyrénées', 'Jourdain', 'Goncourt', 'Nation', 'Rue des Boulets',
  'Sorbier', 'Charonne', 'Père Lachaise', 'Gambetta', 'République', 'Bastille', 'Oberkampf',
  'Canal Saint-Martin', 'Hôtel de Ville', 'Le Marais', 'Saint-Germain-des-Prés',
  'Montmartre', 'Pigalle', 'Batignolles', 'Clichy', 'La Villette', 'Canal de l\'Ourcq',
  'Montparnasse', 'Trocadéro', 'Champs-Élysées', 'Opéra', 'Madeleine', 'Concorde',
  // Métros - Ligne 1 (La Défense - Château de Vincennes)
  'Métro La Défense', 'Métro Esplanade de la Défense', 'Métro Pont de Neuilly', 'Métro Les Sablons',
  'Métro Porte Maillot', 'Métro Argentine', 'Métro Charles de Gaulle - Étoile', 'Métro George V',
  'Métro Franklin D. Roosevelt', 'Métro Champs-Élysées - Clemenceau', 'Métro Concorde', 'Métro Tuileries',
  'Métro Palais Royal - Musée du Louvre', 'Métro Louvre - Rivoli', 'Métro Châtelet', 'Métro Hôtel de Ville',
  'Métro Saint-Paul', 'Métro Bastille', 'Métro Gare de Lyon', 'Métro Reuilly - Diderot',
  'Métro Nation', 'Métro Porte de Vincennes', 'Métro Saint-Mandé', 'Métro Bérault', 'Métro Château de Vincennes',
  // Métros - Ligne 2 (Porte Dauphine - Nation)
  'Métro Porte Dauphine', 'Métro Victor Hugo', 'Métro Charles de Gaulle - Étoile', 'Métro Ternes',
  'Métro Courcelles', 'Métro Monceau', 'Métro Villiers', 'Métro Rome', 'Métro Place de Clichy',
  'Métro Blanche', 'Métro Pigalle', 'Métro Anvers', 'Métro Barbès - Rochechouart', 'Métro La Chapelle',
  'Métro Stalingrad', 'Métro Jaurès', 'Métro Colonel Fabien', 'Métro Belleville', 'Métro Couronnes',
  'Métro Ménilmontant', 'Métro Père Lachaise', 'Métro Philippe Auguste', 'Métro Alexandre Dumas',
  'Métro Avron', 'Métro Nation',
  // Métros - Ligne 3 (Pont de Levallois - Gallieni)
  'Métro Pont de Levallois - Bécon', 'Métro Anatole France', 'Métro Louise Michel', 'Métro Porte de Champerret',
  'Métro Pereire', 'Métro Wagram', 'Métro Malesherbes', 'Métro Villiers', 'Métro Europe',
  'Métro Saint-Lazare', 'Métro Havre - Caumartin', 'Métro Opéra', 'Métro Quatre-Septembre',
  'Métro Bourse', 'Métro Sentier', 'Métro Réaumur - Sébastopol', 'Métro Arts et Métiers',
  'Métro Temple', 'Métro République', 'Métro Parmentier', 'Métro Rue Saint-Maur',
  'Métro Père Lachaise', 'Métro Gambetta', 'Métro Porte de Bagnolet', 'Métro Gallieni',
  // Métros - Ligne 3bis (Gambetta - Porte des Lilas)
  'Métro Porte des Lilas', 'Métro Saint-Fargeau', 'Métro Pelleport', 'Métro Gambetta',
  // Métros - Ligne 4 (Porte de Clignancourt - Mairie de Montrouge)
  'Métro Porte de Clignancourt', 'Métro Simplon', 'Métro Marcadet - Poissonniers', 'Métro Château Rouge',
  'Métro Barbès - Rochechouart', 'Métro Gare du Nord', 'Métro Gare de l\'Est', 'Métro Château d\'Eau',
  'Métro Strasbourg - Saint-Denis', 'Métro Réaumur - Sébastopol', 'Métro Étienne Marcel',
  'Métro Les Halles', 'Métro Châtelet', 'Métro Cité', 'Métro Saint-Michel', 'Métro Odéon',
  'Métro Saint-Germain-des-Prés', 'Métro Saint-Sulpice', 'Métro Saint-Placide', 'Métro Montparnasse - Bienvenüe',
  'Métro Vavin', 'Métro Raspail', 'Métro Denfert-Rochereau', 'Métro Mouton-Duvernet',
  'Métro Alésia', 'Métro Porte d\'Orléans', 'Métro Mairie de Montrouge',
  // Métros - Ligne 5 (Bobigny - Place d\'Italie)
  'Métro Bobigny - Pablo Picasso', 'Métro Bobigny - Pantin - Raymond Queneau', 'Métro Église de Pantin',
  'Métro Hoche', 'Métro Porte de Pantin', 'Métro Ourcq', 'Métro Laumière', 'Métro Jaurès',
  'Métro Stalingrad', 'Métro Gare du Nord', 'Métro Gare de l\'Est', 'Métro Jacques Bonsergent',
  'Métro République', 'Métro Oberkampf', 'Métro Richard-Lenoir', 'Métro Bréguet-Sabin',
  'Métro Bastille', 'Métro Quai de la Rapée', 'Métro Gare d\'Austerlitz', 'Métro Saint-Marcel',
  'Métro Campo Formio', 'Métro Place d\'Italie',
  // Métros - Ligne 6 (Charles de Gaulle - Étoile - Nation)
  'Métro Charles de Gaulle - Étoile', 'Métro Kléber', 'Métro Boissière', 'Métro Trocadéro',
  'Métro Passy', 'Métro Bir-Hakeim', 'Métro Dupleix', 'Métro La Motte-Picquet - Grenelle',
  'Métro Cambronne', 'Métro Sèvres - Lecourbe', 'Métro Pasteur', 'Métro Montparnasse - Bienvenüe',
  'Métro Edgar Quinet', 'Métro Raspail', 'Métro Denfert-Rochereau', 'Métro Saint-Jacques',
  'Métro Glacière', 'Métro Corvisart', 'Métro Place d\'Italie', 'Métro Nationale',
  'Métro Chevaleret', 'Métro Quai de la Gare', 'Métro Bercy', 'Métro Dugommier',
  'Métro Daumesnil', 'Métro Bel-Air', 'Métro Picpus', 'Métro Nation',
  // Métros - Ligne 7 (La Courneuve - Villejuif / Mairie d\'Ivry)
  'Métro La Courneuve - 8 Mai 1945', 'Métro Fort d\'Aubervilliers', 'Métro Aubervilliers - Pantin - Quatre Chemins',
  'Métro Porte de la Villette', 'Métro Corentin Cariou', 'Métro Crimée', 'Métro Riquet',
  'Métro Stalingrad', 'Métro Louis Blanc', 'Métro Château-Landon', 'Métro Gare de l\'Est',
  'Métro Poissonnière', 'Métro Cadet', 'Métro Le Peletier', 'Métro Chaussée d\'Antin - La Fayette',
  'Métro Opéra', 'Métro Pyramides', 'Métro Palais Royal - Musée du Louvre', 'Métro Pont Neuf',
  'Métro Châtelet', 'Métro Pont Marie', 'Métro Sully - Morland', 'Métro Jussieu',
  'Métro Place Monge', 'Métro Censier - Daubenton', 'Métro Les Gobelins', 'Métro Place d\'Italie',
  'Métro Tolbiac', 'Métro Maison Blanche', 'Métro Porte d\'Italie', 'Métro Porte de Choisy',
  'Métro Porte d\'Ivry', 'Métro Pierre et Marie Curie', 'Métro Mairie d\'Ivry',
  'Métro Le Kremlin-Bicêtre', 'Métro Villejuif - Louis Aragon', 'Métro Villejuif - Paul Vaillant-Couturier',
  // Métros - Ligne 7bis (Louis Blanc - Pré Saint-Gervais)
  'Métro Pré Saint-Gervais', 'Métro Place des Fêtes', 'Métro Buttes-Chaumont', 'Métro Botzaris',
  'Métro Danube', 'Métro Crimée', 'Métro Riquet', 'Métro Louis Blanc',
  // Métros - Ligne 8 (Balard - Pointe du Lac)
  'Métro Balard', 'Métro Lourmel', 'Métro Boucicaut', 'Métro Félix Faure',
  'Métro Commerce', 'Métro La Motte-Picquet - Grenelle', 'Métro École Militaire', 'Métro La Tour-Maubourg',
  'Métro Invalides', 'Métro Concorde', 'Métro Madeleine', 'Métro Opéra',
  'Métro Richelieu - Drouot', 'Métro Grands Boulevards', 'Métro Bonne Nouvelle', 'Métro Strasbourg - Saint-Denis',
  'Métro République', 'Métro Filles du Calvaire', 'Métro Saint-Sébastien - Froissart', 'Métro Chemin Vert',
  'Métro Bastille', 'Métro Ledru-Rollin', 'Métro Faidherbe - Chaligny', 'Métro Reuilly - Diderot',
  'Métro Montgallet', 'Métro Daumesnil', 'Métro Michel Bizot', 'Métro Porte Dorée',
  'Métro Porte de Charenton', 'Métro Liberté', 'Métro Charenton - Écoles', 'Métro École Vétérinaire de Maisons-Alfort',
  'Métro Maisons-Alfort - Stade', 'Métro Maisons-Alfort - Les Juilliottes', 'Métro Créteil - L\'Échat',
  'Métro Créteil - Université', 'Métro Créteil - Préfecture', 'Métro Pointe du Lac',
  // Métros - Ligne 9 (Pont de Sèvres - Mairie de Montreuil)
  'Métro Pont de Sèvres', 'Métro Billancourt', 'Métro Marcel Sembat', 'Métro Porte de Saint-Cloud',
  'Métro Exelmans', 'Métro Michel-Ange - Molitor', 'Métro Michel-Ange - Auteuil', 'Métro Jasmin',
  'Métro Ranelagh', 'Métro La Muette', 'Métro Rue de la Pompe', 'Métro Trocadéro',
  'Métro Iéna', 'Métro Alma - Marceau', 'Métro Franklin D. Roosevelt', 'Métro Saint-Philippe du Roule',
  'Métro Miromesnil', 'Métro Saint-Augustin', 'Métro Havre - Caumartin', 'Métro Chaussée d\'Antin - La Fayette',
  'Métro Richelieu - Drouot', 'Métro Grands Boulevards', 'Métro Bonne Nouvelle', 'Métro Strasbourg - Saint-Denis',
  'Métro République', 'Métro Oberkampf', 'Métro Saint-Ambroise', 'Métro Voltaire',
  'Métro Charonne', 'Métro Rue des Boulets', 'Métro Nation', 'Métro Buzenval',
  'Métro Maraîchers', 'Métro Porte de Montreuil', 'Métro Robespierre', 'Métro Croix de Chavaux',
  'Métro Mairie de Montreuil',
  // Métros - Ligne 10 (Boulogne - Gare d\'Austerlitz)
  'Métro Boulogne - Pont de Saint-Cloud', 'Métro Boulogne - Jean Jaurès', 'Métro Porte de Saint-Cloud',
  'Métro Michel-Ange - Molitor', 'Métro Chardon-Lagache', 'Métro Mirabeau', 'Métro Javel - André Citroën',
  'Métro Charles Michels', 'Métro Avenue Émile Zola', 'Métro La Motte-Picquet - Grenelle', 'Métro Ségur',
  'Métro Duroc', 'Métro Vaneau', 'Métro Sèvres - Babylone', 'Métro Mabillon',
  'Métro Odéon', 'Métro Cluny - La Sorbonne', 'Métro Maubert - Mutualité', 'Métro Cardinal Lemoine',
  'Métro Jussieu', 'Métro Gare d\'Austerlitz',
  // Métros - Ligne 11 (Châtelet - Mairie des Lilas)
  'Métro Châtelet', 'Métro Hôtel de Ville', 'Métro Rambuteau', 'Métro Arts et Métiers',
  'Métro République', 'Métro Goncourt', 'Métro Belleville', 'Métro Pyrénées',
  'Métro Jourdain', 'Métro Place des Fêtes', 'Métro Télégraphe', 'Métro Porte des Lilas',
  'Métro Mairie des Lilas',
  // Métros - Ligne 12 (Mairie d\'Issy - Front Populaire)
  'Métro Mairie d\'Issy', 'Métro Corentin Celton', 'Métro Porte de Versailles', 'Métro Convention',
  'Métro Vaugirard', 'Métro Volontaires', 'Métro Pasteur', 'Métro Falguière',
  'Métro Montparnasse - Bienvenüe', 'Métro Notre-Dame-des-Champs', 'Métro Rennes', 'Métro Sèvres - Babylone',
  'Métro Rue du Bac', 'Métro Solférino', 'Métro Assemblée Nationale', 'Métro Concorde',
  'Métro Madeleine', 'Métro Saint-Lazare', 'Métro Trinité - d\'Estienne d\'Orves', 'Métro Notre-Dame-de-Lorette',
  'Métro Saint-Georges', 'Métro Pigalle', 'Métro Abbesses', 'Métro Lamarck - Caulaincourt',
  'Métro Jules Joffrin', 'Métro Marcadet - Poissonniers', 'Métro Marx Dormoy', 'Métro Porte de la Chapelle',
  'Métro Front Populaire',
  // Métros - Ligne 13 (Châtillon - Montrouge / Saint-Denis - Asnières)
  'Métro Châtillon - Montrouge', 'Métro Malakoff - Plateau de Vanves', 'Métro Malakoff - Rue Étienne-Dolet',
  'Métro Porte de Vanves', 'Métro Plaisance', 'Métro Pernety', 'Métro Gaîté', 'Métro Montparnasse - Bienvenüe',
  'Métro Duroc', 'Métro Saint-François-Xavier', 'Métro Varenne', 'Métro Invalides',
  'Métro Champs-Élysées - Clemenceau', 'Métro Miromesnil', 'Métro Saint-Lazare', 'Métro Liège',
  'Métro Place de Clichy', 'Métro La Fourche', 'Métro Guy Môquet', 'Métro Porte de Saint-Ouen',
  'Métro Garibaldi', 'Métro Mairie de Saint-Ouen', 'Métro Carrefour Pleyel', 'Métro Saint-Denis - Porte de Paris',
  'Métro Basilique de Saint-Denis', 'Métro Saint-Denis - Université',
  'Métro Brochant', 'Métro Porte de Clichy', 'Métro Mairie de Clichy', 'Métro Asnières - Gennevilliers - Les Courtilles',
  'Métro Les Agnettes', 'Métro Gabriel Péri', 'Métro Mairie d\'Asnières',
  // Métros - Ligne 14 (Mairie de Saint-Ouen - Olympiades)
  'Métro Mairie de Saint-Ouen', 'Métro Porte de Clichy', 'Métro Pont Cardinet', 'Métro Saint-Lazare',
  'Métro Madeleine', 'Métro Pyramides', 'Métro Châtelet', 'Métro Gare de Lyon',
  'Métro Bercy', 'Métro Cour Saint-Émilion', 'Métro Bibliothèque François Mitterrand', 'Métro Olympiades'
]

const CRITERIA_OPTIONS = [
  {
    id: 'haussmanien',
    name: 'Haussmanien',
    description: 'Si ça craque pas sous mes pas, j\'en veux pas',
    icon: '🔑'
  },
  {
    id: 'quartier',
    name: 'Quartier',
    description: 'Mes potes, mon café, ma vie',
    icon: '📍'
  },
  {
    id: 'prix',
    name: 'Prix',
    description: 'Je veux rester en bon termes avec mon banquier',
    icon: '💰'
  },
  {
    id: 'luminosite',
    name: 'Luminosité',
    description: 'Je veux bronzer dans mon salon, ou c\'est non',
    icon: '☀️'
  },
  {
    id: 'cuisine_ouverte',
    name: 'Cuisine ouverte',
    description: 'Pour surveiller le four et les potins.',
    icon: '👨‍🍳'
  },
  {
    id: 'ascenseur',
    name: 'Ascenseur',
    description: 'Parce que le cardio, c\'est pas tous les jours.',
    icon: '🛗'
  },
  {
    id: 'large_piece_vie',
    name: 'Large pièce de vie',
    description: 'Un salon qui a son propre code postal',
    icon: '🛋️'
  },
  {
    id: 'renove',
    name: 'Rénové',
    description: 'Je ne touche pas une perceuse',
    icon: '🔨'
  },
  {
    id: 'neuf',
    name: 'Neuf',
    description: 'J\'aime les murs droits et les prises qui fonctionnent',
    icon: '✨'
  }
]

function AlertCreator({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1) // 1 = sélection critères, 2 = paramètres généraux
  const [selectedCriteria, setSelectedCriteria] = useState([])
  const [draggedCriterion, setDraggedCriterion] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [isDraggingFromAvailable, setIsDraggingFromAvailable] = useState(false)
  const [dragOverAvailableIndex, setDragOverAvailableIndex] = useState(null)
  const wasDroppedInZoneRef = useRef(false)
  
  // Paramètres généraux
  const [alertName, setAlertName] = useState('')
  const [prixMin, setPrixMin] = useState(500000)
  const [prixMax, setPrixMax] = useState(800000)
  const [surfaceMin, setSurfaceMin] = useState(60)
  const [surfaceMax, setSurfaceMax] = useState(100)
  const [selectedPieces, setSelectedPieces] = useState([])
  const [selectedQuartiers, setSelectedQuartiers] = useState([])
  const [quartierInput, setQuartierInput] = useState('')
  const [quartierSuggestions, setQuartierSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Calculer les critères disponibles (non sélectionnés) - mémorisé pour éviter les re-renders
  const availableCriteria = useMemo(() => {
    return CRITERIA_OPTIONS.filter(
      criterion => !selectedCriteria.find(selected => selected.id === criterion.id)
    )
  }, [selectedCriteria])

  // Gérer le début du drag depuis la liste disponible
  const handleDragStart = (e, criterion) => {
    setDraggedCriterion(criterion)
    setIsDraggingFromAvailable(true)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', criterion.id)
  }

  // Gérer le drag depuis la zone de placement (réorganisation)
  const handleDragStartFromSelected = (e, index) => {
    const criterion = selectedCriteria[index]
    setDraggedCriterion(criterion)
    setIsDraggingFromAvailable(false)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', criterion.id)
  }

  // Gérer la fin du drag (pour nettoyer l'état si pas de drop)
  const handleDragEnd = (e) => {
    // Si on drag depuis la zone sélectionnée et qu'on n'a pas drop dans la zone, retirer le critère
    if (!isDraggingFromAvailable && draggedCriterion) {
      // Vérifier si le drop a été fait dans la zone (via un petit délai)
      setTimeout(() => {
        // Si on n'a pas drop dans la zone, retirer le critère
        if (!wasDroppedInZoneRef.current && draggedCriterion) {
          setSelectedCriteria(prev => prev.filter(c => c.id !== draggedCriterion.id))
        }
        // Réinitialiser les états
        setDraggedCriterion(null)
        setIsDraggingFromAvailable(false)
        setDragOverIndex(null)
        setDragOverAvailableIndex(null)
        wasDroppedInZoneRef.current = false
      }, 50)
    } else {
      // Réinitialiser les états
      setDraggedCriterion(null)
      setIsDraggingFromAvailable(false)
      setDragOverIndex(null)
      setDragOverAvailableIndex(null)
      wasDroppedInZoneRef.current = false
    }
  }

  // Gérer le drop dans la zone de placement
  const handleDropInZone = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const currentDragged = draggedCriterion
    if (!currentDragged) return

    wasDroppedInZoneRef.current = true

    // Si le critère est déjà sélectionné, on le réorganise
    const existingIndex = selectedCriteria.findIndex(c => c.id === currentDragged.id)
    
    if (existingIndex !== -1) {
      // Réorganisation: retirer de l'ancienne position
      const newSelected = selectedCriteria.filter(c => c.id !== currentDragged.id)
      
      // Insérer à la nouvelle position si dragOverIndex est défini et valide
      if (dragOverIndex !== null && dragOverIndex >= 0 && dragOverIndex <= newSelected.length) {
        newSelected.splice(dragOverIndex, 0, currentDragged)
      } else {
        // Sinon, ajouter à la fin
        newSelected.push(currentDragged)
      }
      
      setSelectedCriteria(newSelected)
    } else {
      // Nouveau critère: vérifier la limite de 4
      if (selectedCriteria.length < 4) {
        const newSelected = [...selectedCriteria]
        // Insérer à la position spécifiée si valide, sinon à la fin
        if (dragOverIndex !== null && dragOverIndex >= 0 && dragOverIndex <= newSelected.length) {
          newSelected.splice(dragOverIndex, 0, currentDragged)
        } else {
          newSelected.push(currentDragged)
        }
        setSelectedCriteria(newSelected)
      }
    }
    
    // Réinitialiser après le drop
    setTimeout(() => {
      setDraggedCriterion(null)
      setIsDraggingFromAvailable(false)
      setDragOverIndex(null)
      setDragOverAvailableIndex(null)
      wasDroppedInZoneRef.current = false
    }, 0)
  }

  // Gérer le drag over dans la zone de placement - optimisé pour réduire les re-renders
  const handleDragOverInZone = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
    // Si on est sur la zone vide, on peut accepter le drop
    if (selectedCriteria.length === 0) {
      setDragOverIndex(prev => prev !== 0 ? 0 : prev)
    }
  }, [selectedCriteria.length])

  // Gérer le drag over sur un élément de la zone (pour l'insertion) - optimisé
  const handleDragOverOnItem = useCallback((e, index) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
    // Déterminer si on insère avant ou après selon la position de la souris
    const rect = e.currentTarget.getBoundingClientRect()
    const mouseY = e.clientY
    const centerY = rect.top + rect.height / 2
    // Si la souris est dans la moitié supérieure, insérer avant, sinon après
    const insertIndex = mouseY < centerY ? index : index + 1
    // Ne mettre à jour que si l'index a changé
    setDragOverIndex(prev => prev !== insertIndex ? insertIndex : prev)
  }, [])

  // Gérer le drag leave
  const handleDragLeave = () => {
    setDragOverIndex(null)
  }

  // Gérer le drag over sur un élément de la liste disponible - optimisé
  const handleDragOverAvailableItem = useCallback((e, index) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
    // Déterminer si on insère avant ou après selon la position de la souris
    const rect = e.currentTarget.getBoundingClientRect()
    const mouseY = e.clientY
    const centerY = rect.top + rect.height / 2
    // Si la souris est dans la moitié supérieure, insérer avant, sinon après
    const insertIndex = mouseY < centerY ? index : index + 1
    // Ne mettre à jour que si l'index a changé
    setDragOverAvailableIndex(prev => prev !== insertIndex ? insertIndex : prev)
  }, [])

  // Gérer le drag leave de la liste disponible
  const handleDragLeaveAvailable = () => {
    setDragOverAvailableIndex(null)
  }

  // Gérer le drop dans la liste disponible (retirer un critère du top)
  const handleDropInAvailable = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!draggedCriterion || isDraggingFromAvailable) return
    
    // Retirer le critère de la liste sélectionnée
    setSelectedCriteria(prev => prev.filter(c => c.id !== draggedCriterion.id))
    
    // Réinitialiser
    setDraggedCriterion(null)
    setIsDraggingFromAvailable(false)
    setDragOverIndex(null)
    setDragOverAvailableIndex(null)
  }

  // Retirer un critère de la zone de placement
  const handleRemoveCriterion = (criterionId) => {
    setSelectedCriteria(selectedCriteria.filter(c => c.id !== criterionId))
  }

  // Gérer le drop en dehors de la zone (pour retirer un critère)
  const handleDropOutside = (e) => {
    if (!draggedCriterion || isDraggingFromAvailable) return
    
    // Si on drag depuis la zone sélectionnée et qu'on drop en dehors, retirer
    const existingIndex = selectedCriteria.findIndex(c => c.id === draggedCriterion.id)
    if (existingIndex !== -1) {
      setSelectedCriteria(prev => prev.filter(c => c.id !== draggedCriterion.id))
    }
    
    setDraggedCriterion(null)
    setIsDraggingFromAvailable(false)
    setDragOverIndex(null)
  }

  // Gérer le bouton Continuer
  const handleContinue = () => {
    if (selectedCriteria.length === 0) {
      return
    }
    
    // Passer à l'étape 2
    setStep(2)
  }

  // Gérer le retour à l'étape 1
  const handleBack = () => {
    setStep(1)
  }

  // Fonction pour obtenir le numéro de ligne d'une station de métro
  const getMetroLine = (stationName) => {
    const name = stationName.replace(/^Métro /, '')
    
    // Mapping des stations principales par ligne
    const lineMapping = {
      // Ligne 11
      'Jourdain': 11, 'Pyrénées': 11, 'Goncourt': 11, 'Place des Fêtes': 11,
      'Télégraphe': 11, 'Mairie des Lilas': 11, 'Rambuteau': 11,
      // Ligne 2
      'Belleville': 2, 'Ménilmontant': 2, 'Alexandre Dumas': 2, 'Philippe Auguste': 2, 'Avron': 2,
      'Couronnes': 2, 'Père Lachaise': 2, 'Porte Dauphine': 2, 'Nation': 2,
      // Ligne 4
      'Montparnasse - Bienvenüe': 4, 'Porte de Clignancourt': 4, 'Mairie de Montrouge': 4,
      // Ligne 6
      'Trocadéro': 6,
      // Ligne 12
      'Montparnasse - Bienvenüe': 12, 'Abbesses': 12, 'Pigalle': 12, 'Mairie d\'Issy': 12,
      // Ligne 13
      'Montparnasse - Bienvenüe': 13, 'Châtillon - Montrouge': 13,
      // Ligne 1
      'Châtelet': 1, 'Hôtel de Ville': 1, 'Bastille': 1,
      // Ligne 3
      'République': 3, 'Arts et Métiers': 3, 'Gambetta': 3,
      // Ligne 5
      'Oberkampf': 5, 'Place d\'Italie': 5,
      // Ligne 7
      'Jussieu': 7,
      // Ligne 8
      'Invalides': 8, 'Madeleine': 8,
      // Ligne 9
      'Charonne': 9, 'Rue des Boulets': 9, 'Mairie de Montreuil': 9,
      // Ligne 10
      'Gare d\'Austerlitz': 10,
      // Ligne 14
      'Gare de Lyon': 14, 'Bibliothèque François Mitterrand': 14
    }
    
    // Chercher dans le mapping
    if (lineMapping[name]) {
      return lineMapping[name]
    }
    
    // Si pas trouvé, chercher dans PARIS_LOCATIONS en parcourant les sections
    let currentLine = null
    for (const loc of PARIS_LOCATIONS) {
      if (loc.startsWith('// Métros - Ligne')) {
        if (loc.includes('Ligne 1')) currentLine = 1
        else if (loc.includes('Ligne 2')) currentLine = 2
        else if (loc.includes('Ligne 3') && loc.includes('3bis')) currentLine = '3bis'
        else if (loc.includes('Ligne 3')) currentLine = 3
        else if (loc.includes('Ligne 4')) currentLine = 4
        else if (loc.includes('Ligne 5')) currentLine = 5
        else if (loc.includes('Ligne 6')) currentLine = 6
        else if (loc.includes('Ligne 7') && loc.includes('7bis')) currentLine = '7bis'
        else if (loc.includes('Ligne 7')) currentLine = 7
        else if (loc.includes('Ligne 8')) currentLine = 8
        else if (loc.includes('Ligne 9')) currentLine = 9
        else if (loc.includes('Ligne 10')) currentLine = 10
        else if (loc.includes('Ligne 11')) currentLine = 11
        else if (loc.includes('Ligne 12')) currentLine = 12
        else if (loc.includes('Ligne 13')) currentLine = 13
        else if (loc.includes('Ligne 14')) currentLine = 14
      } else if (loc.startsWith('Métro ') && currentLine) {
        const stationNameInList = loc.replace(/^Métro /, '')
        if (stationNameInList === name) {
          return currentLine
        }
      }
    }
    
    return null
  }

  // Gérer l'ajout d'un quartier
  const handleAddQuartier = () => {
    const inputValue = quartierInput.trim()
    if (inputValue && !selectedQuartiers.some(q => q.value === inputValue || q.value === inputValue.replace(/^Métro /, ''))) {
      // Si c'est une station de métro, extraire le nom et la ligne
      if (inputValue.startsWith('Métro ')) {
        const stationName = inputValue.replace(/^Métro /, '')
        const line = getMetroLine(inputValue)
        setSelectedQuartiers([...selectedQuartiers, {
          value: inputValue,
          display: line ? `${stationName} (${line})` : stationName
        }])
      } else {
        // Pour les autres (arrondissements, quartiers), garder tel quel
        setSelectedQuartiers([...selectedQuartiers, {
          value: inputValue,
          display: inputValue
        }])
      }
      setQuartierInput('')
      setShowSuggestions(false)
    }
  }

  // Gérer les suggestions d'autocomplete (top 5)
  // Fonction pour normaliser les accents (enlever les accents pour la comparaison)
  const normalizeString = (str) => {
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Enlever les accents
  }

  const handleQuartierInputChange = (e) => {
    const value = e.target.value
    setQuartierInput(value)
    
    if (value.trim().length > 0) {
      // Filtrer les suggestions qui correspondent (sans tenir compte des accents)
      const normalizedValue = normalizeString(value)
      const matching = PARIS_LOCATIONS.filter(loc => normalizeString(loc).includes(normalizedValue))
      
      // Éviter les doublons : si on a "Alexandre Dumas" et "Métro Alexandre Dumas", garder seulement le métro
      const deduplicated = []
      const seenNames = new Set()
      
      for (const loc of matching) {
        if (loc.startsWith('Métro ')) {
          const stationName = loc.replace(/^Métro /, '')
          // Si on a déjà vu ce nom (sans "Métro"), on préfère la version métro
          if (seenNames.has(stationName)) {
            // Remplacer l'entrée précédente par celle du métro
            const index = deduplicated.findIndex(l => l.replace(/^Métro /, '') === stationName || l === stationName)
            if (index !== -1) {
              deduplicated[index] = loc
            }
          } else {
            deduplicated.push(loc)
            seenNames.add(stationName)
          }
        } else {
          // Pour les quartiers/arrondissements, vérifier qu'il n'y a pas de version métro
          if (!seenNames.has(loc)) {
            // Vérifier s'il existe une version "Métro X" dans les résultats
            const hasMetroVersion = matching.some(m => m.startsWith('Métro ') && m.replace(/^Métro /, '') === loc)
            if (!hasMetroVersion) {
              deduplicated.push(loc)
              seenNames.add(loc)
            }
          }
        }
      }
      
      const filtered = deduplicated
        .slice(0, 5) // Top 5 seulement
        .map(loc => {
          // Si c'est une station de métro, ajouter le numéro de ligne
          if (loc.startsWith('Métro ')) {
            const line = getMetroLine(loc)
            const stationName = loc.replace(/^Métro /, '') // Retirer "Métro "
            return {
              display: line ? `Ligne ${line}` : null, // Afficher juste "Ligne X" à droite
              value: loc, // Garder la valeur originale pour la sélection
              name: stationName // Nom sans "Métro " pour l'affichage à gauche
            }
          }
          return {
            display: null,
            value: loc,
            name: loc
          }
        })
      setQuartierSuggestions(filtered)
      setShowSuggestions(filtered.length > 0)
    } else {
      setQuartierSuggestions([])
      setShowSuggestions(false)
    }
  }

  // Sélectionner une suggestion
  const handleSelectSuggestion = (suggestion) => {
    // Si suggestion est un objet avec value, utiliser value, sinon utiliser directement
    const value = typeof suggestion === 'object' && suggestion.value ? suggestion.value : suggestion
    
    // Ajouter directement à la sélection
    if (value && !selectedQuartiers.some(q => q.value === value || q.value === value.replace(/^Métro /, ''))) {
      // Si c'est une station de métro, extraire le nom et la ligne
      if (value.startsWith('Métro ')) {
        const stationName = value.replace(/^Métro /, '')
        const line = getMetroLine(value)
        setSelectedQuartiers([...selectedQuartiers, {
          value: value,
          display: line ? `${stationName} (${line})` : stationName
        }])
      } else {
        // Pour les autres (arrondissements, quartiers), garder tel quel
        setSelectedQuartiers([...selectedQuartiers, {
          value: value,
          display: value
        }])
      }
      setQuartierInput('')
      setShowSuggestions(false)
    }
  }

  // Gérer la suppression d'un quartier
  const handleRemoveQuartier = (quartier) => {
    // Comparer par valeur pour les objets ou directement pour les strings
    setSelectedQuartiers(selectedQuartiers.filter(q => {
      if (typeof q === 'object' && typeof quartier === 'object') {
        return q.value !== quartier.value
      }
      return q !== quartier
    }))
  }

  // Gérer l'enregistrement
  const handleSave = async () => {
    // TODO: Implémenter la création de l'alerte
    if (onSuccess) {
      // Pour l'instant, on ferme juste
      onClose()
    }
  }

  // Gérer la fermeture
  const handleClose = () => {
    setStep(1)
    setSelectedCriteria([])
    setDraggedCriterion(null)
    setIsDraggingFromAvailable(false)
    setDragOverIndex(null)
    setDragOverAvailableIndex(null)
    setAlertName('')
    setPrixMin(500000)
    setPrixMax(800000)
    setSurfaceMin(60)
    setSurfaceMax(100)
    setSelectedPieces([])
    setSelectedQuartiers([])
    setQuartierInput('')
    setQuartierSuggestions([])
    setShowSuggestions(false)
    onClose()
  }

  // Vérifier si on doit afficher le placeholder
  const shouldShowPlaceholder = selectedCriteria.length === 0
  const showPlaceholderBelow = selectedCriteria.length > 0 && selectedCriteria.length < 4

  // Obtenir la couleur du badge selon le ranking
  const getBadgeColor = (index) => {
    // 1 et 2 : Jaune (#F59E0B du design system)
    // 3 et 4 : Gris (#9CA3AF du design system)
    if (index === 0 || index === 1) {
      return '#F59E0B' // Jaune
    } else {
      return '#9CA3AF' // Gris
    }
  }

  if (!isOpen) return null

  // Rendu de l'étape 2 : Paramètres généraux
  if (step === 2) {
    return (
      <>
        {/* Overlay */}
        <div className="alert-creator-overlay" onClick={handleClose} />
        
        {/* Sidebar */}
        <div className="alert-creator-sidebar">
          {/* Header */}
          <div className="alert-creator-header">
            <div className="alert-creator-header-content">
              <h2>Créer une alerte</h2>
              <p className="alert-creator-subtitle">
                Complétez vos critères
              </p>
            </div>
            <button className="btn-close" onClick={handleClose} aria-label="Fermer">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Critères sélectionnés en haut */}
          <div className="selected-criteria-summary">
            {selectedCriteria.map((criterion, index) => (
              <div key={criterion.id} className="criterion-summary-item">
                <div className="criterion-summary-circle">
                  <span className="criterion-summary-icon">{criterion.icon}</span>
                  <div 
                    className="criterion-summary-badge"
                    style={{ backgroundColor: getBadgeColor(index) }}
                  >
                    {index + 1}
                  </div>
                </div>
              </div>
            ))}
            {selectedCriteria.length < 4 && (
              <div className="criterion-summary-placeholder">
                <span>+</span>
              </div>
            )}
            {selectedCriteria.length > 0 && (
              <button
                className="criterion-summary-chevron"
                onClick={() => {
                  // Retourner à l'étape 1 pour modifier les critères
                  setStep(1)
                }}
                aria-label="Modifier les critères"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M6 4L10 8L6 12" stroke="#7B7F87" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
          </div>

          {/* Paramètres généraux */}
          <div className="alert-parameters">
            {/* Nom de l'alerte */}
            <div className="parameter-group">
              <label className="parameter-label">Nom de l'alerte</label>
              <input
                type="text"
                className="alert-name-input"
                placeholder="Ex: Appartements Belleville"
                value={alertName}
                onChange={(e) => setAlertName(e.target.value)}
              />
            </div>

            {/* Prix */}
            <div className="parameter-group">
              <label className="parameter-label">Prix</label>
              <div className="range-slider-container">
                <div className="range-slider">
                  <div className="range-slider-track" />
                  <div 
                    className="range-slider-active"
                    style={{
                      left: `${(prixMin / 2000000) * 100}%`,
                      width: `${((prixMax - prixMin) / 2000000) * 100}%`
                    }}
                  />
                  <input
                    type="range"
                    min="0"
                    max="2000000"
                    step="10000"
                    value={prixMin}
                    onChange={(e) => {
                      const newMin = parseInt(e.target.value)
                      if (newMin <= prixMax) {
                        setPrixMin(newMin)
                      }
                    }}
                    className="range-input range-input-min"
                  />
                  <input
                    type="range"
                    min="0"
                    max="2000000"
                    step="10000"
                    value={prixMax}
                    onChange={(e) => {
                      const newMax = parseInt(e.target.value)
                      if (newMax >= prixMin) {
                        setPrixMax(newMax)
                      }
                    }}
                    className="range-input range-input-max"
                  />
                </div>
                <div className="range-values">
                  <span>{prixMin.toLocaleString('fr-FR').replace(/\s/g, ',')}€</span>
                  <span>{prixMax.toLocaleString('fr-FR').replace(/\s/g, ',')}€</span>
                </div>
              </div>
            </div>

            {/* Quartier */}
            <div className="parameter-group">
              <label className="parameter-label">Quartier</label>
              <div className="quartier-input-wrapper">
                <div className="quartier-input-container">
                  <input
                    type="text"
                    className="quartier-input"
                    placeholder="Code postal, metro.."
                    value={quartierInput}
                    onChange={handleQuartierInputChange}
                    onFocus={() => {
                      if (quartierInput.trim().length > 0 && quartierSuggestions.length > 0) {
                        setShowSuggestions(true)
                      }
                    }}
                    onBlur={() => {
                      // Délai pour permettre le clic sur une suggestion
                      setTimeout(() => setShowSuggestions(false), 200)
                    }}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddQuartier()
                      }
                    }}
                  />
                  <button 
                    className="quartier-add-btn"
                    onClick={handleAddQuartier}
                    disabled={!quartierInput.trim()}
                  >
                    +
                  </button>
                </div>
                {showSuggestions && quartierSuggestions.length > 0 && (
                  <div className="quartier-suggestions">
                    {quartierSuggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="quartier-suggestion-item"
                        onClick={() => handleSelectSuggestion(suggestion)}
                      >
                        <span className="quartier-suggestion-name">{suggestion.name}</span>
                        {suggestion.display && (
                          <span className="quartier-suggestion-line">{suggestion.display}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {selectedQuartiers.length > 0 && (
                <div className="quartier-tags">
                  {selectedQuartiers.map((quartier, index) => (
                    <div key={index} className="quartier-tag">
                      <span>{typeof quartier === 'object' ? quartier.display : quartier}</span>
                      <button 
                        className="quartier-tag-remove"
                        onClick={() => handleRemoveQuartier(quartier)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Surface */}
            <div className="parameter-group">
              <label className="parameter-label">Surface</label>
              <div className="range-slider-container">
                <div className="range-slider">
                  <div className="range-slider-track" />
                  <div 
                    className="range-slider-active"
                    style={{
                      left: `${(surfaceMin / 200) * 100}%`,
                      width: `${((surfaceMax - surfaceMin) / 200) * 100}%`
                    }}
                  />
                  <input
                    type="range"
                    min="0"
                    max="200"
                    step="5"
                    value={surfaceMin}
                    onChange={(e) => {
                      const newMin = parseInt(e.target.value)
                      if (newMin <= surfaceMax) {
                        setSurfaceMin(newMin)
                      }
                    }}
                    className="range-input range-input-min"
                  />
                  <input
                    type="range"
                    min="0"
                    max="200"
                    step="5"
                    value={surfaceMax}
                    onChange={(e) => {
                      const newMax = parseInt(e.target.value)
                      if (newMax >= surfaceMin) {
                        setSurfaceMax(newMax)
                      }
                    }}
                    className="range-input range-input-max"
                  />
                </div>
                <div className="range-values">
                  <span>{surfaceMin} m²</span>
                  <span>{surfaceMax} m²</span>
                </div>
              </div>
            </div>

            {/* Pièces */}
            <div className="parameter-group">
              <label className="parameter-label">Pièces</label>
              <div className="pieces-selector">
                {[1, 2, 3, 4, '5+'].map((piece) => (
                  <button
                    key={piece}
                    className={`piece-btn ${selectedPieces.includes(piece) ? 'selected' : ''}`}
                    onClick={() => {
                      if (selectedPieces.includes(piece)) {
                        setSelectedPieces(selectedPieces.filter(p => p !== piece))
                      } else {
                        setSelectedPieces([...selectedPieces, piece])
                      }
                    }}
                  >
                    {piece}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="alert-creator-footer">
            <button className="btn-back" onClick={handleBack}>
              Retour
            </button>
            <button className="btn-save" onClick={handleSave}>
              Enregistrer
            </button>
          </div>
        </div>
      </>
    )
  }

  // Rendu de l'étape 1 : Sélection des critères
  return (
    <>
      {/* Overlay */}
      <div className="alert-creator-overlay" onClick={handleClose} />
      
      {/* Sidebar */}
      <div className="alert-creator-sidebar">
        {/* Header */}
        <div className="alert-creator-header">
          <div className="alert-creator-header-content">
            <h2>Créer une alerte</h2>
            <p className="alert-creator-subtitle">
              Classez vos critères par ordre d'importance
            </p>
          </div>
          <button className="btn-close" onClick={handleClose} aria-label="Fermer">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        {/* Zone de placement */}
        <div className="criteria-drop-zone">
          <div
            className={`drop-zone ${shouldShowPlaceholder && selectedCriteria.length === 0 ? 'empty' : 'has-items'} ${dragOverIndex === null && draggedCriterion ? 'drag-over' : ''}`}
            onDrop={handleDropInZone}
            onDragOver={handleDragOverInZone}
            onDragLeave={handleDragLeave}
            onDragEnd={handleDragEnd}
          >
            {selectedCriteria.length > 0 && (
              <div className="selected-criteria-list">
                {selectedCriteria.map((criterion, index) => (
                  <React.Fragment key={criterion.id}>
                    {/* Ligne d'insertion avant l'élément */}
                    {dragOverIndex === index && draggedCriterion && (
                      <div className="drop-indicator" />
                    )}
                    <div
                      className="selected-criterion-item"
                      draggable
                      onDragStart={(e) => handleDragStartFromSelected(e, index)}
                      onDragEnd={handleDragEnd}
                      onDragOver={(e) => handleDragOverOnItem(e, index)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        handleDropInZone(e)
                      }}
                    >
                    <div className="selected-criterion-content">
                      <span className="selected-criterion-icon">{criterion.icon}</span>
                      <div className="selected-criterion-info">
                        <span className="selected-criterion-name">{criterion.name}</span>
                        <span className="selected-criterion-description">{criterion.description}</span>
                      </div>
                    </div>
                    <div className="selected-criterion-actions">
                      <div 
                        className="selected-criterion-badge"
                        style={{ backgroundColor: getBadgeColor(index) }}
                      >
                        {index + 1}
                      </div>
                      <button
                        className="btn-remove-criterion-top"
                        onClick={() => handleRemoveCriterion(criterion.id)}
                        aria-label={`Retirer ${criterion.name}`}
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                    {/* Ligne d'insertion après le dernier élément */}
                    {index === selectedCriteria.length - 1 && dragOverIndex === selectedCriteria.length && draggedCriterion && (
                      <div className="drop-indicator" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}
            {showPlaceholderBelow && (
              <div className="drop-zone-placeholder-below">
                <p className="drop-zone-title">Placez vos critères ici</p>
                <p className="drop-zone-subtitle">Jusqu'à 4 critères</p>
              </div>
            )}
            {shouldShowPlaceholder && selectedCriteria.length === 0 && (
              <div className="drop-zone-placeholder">
                <p className="drop-zone-title">Placez vos critères ici</p>
                <p className="drop-zone-subtitle">Jusqu'à 4 critères</p>
              </div>
            )}
          </div>
        </div>

        {/* Ligne de séparation si critères sélectionnés */}
        {selectedCriteria.length > 0 && (
          <div className="criteria-separator" />
        )}

        {/* Liste des critères disponibles */}
        <div className="available-criteria-section">
          <div 
            className="available-criteria-list"
            onDragOver={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (!isDraggingFromAvailable && draggedCriterion) {
                e.dataTransfer.dropEffect = 'move'
              }
            }}
            onDragLeave={handleDragLeaveAvailable}
            onDrop={handleDropInAvailable}
          >
            {availableCriteria.map((criterion, index) => (
              <React.Fragment key={criterion.id}>
                {/* Ligne d'insertion avant l'élément */}
                {dragOverAvailableIndex === index && draggedCriterion && !isDraggingFromAvailable && (
                  <div className="drop-indicator" />
                )}
                <div
                  className="available-criterion-item"
                  draggable
                  onDragStart={(e) => handleDragStart(e, criterion)}
                  onDragEnd={handleDragEnd}
                  onDragOver={(e) => handleDragOverAvailableItem(e, index)}
                  onDragLeave={handleDragLeaveAvailable}
                >
                <div className="available-criterion-content">
                  <span className="available-criterion-icon">{criterion.icon}</span>
                  <div className="available-criterion-info">
                    <span className="available-criterion-name">{criterion.name}</span>
                    <span className="available-criterion-description">{criterion.description}</span>
                  </div>
                </div>
                <div className="drag-handle" aria-label="Glisser pour ajouter">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 4H10M6 8H10M6 12H10" stroke="#7B7F87" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
              </div>
                {/* Ligne d'insertion après le dernier élément */}
                {index === availableCriteria.length - 1 && dragOverAvailableIndex === availableCriteria.length && draggedCriterion && !isDraggingFromAvailable && (
                  <div className="drop-indicator" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Bouton Continuer */}
        <div className="alert-creator-footer">
          <button
            className="btn-continue"
            onClick={handleContinue}
            disabled={selectedCriteria.length === 0}
          >
            Continuer
          </button>
        </div>
      </div>
    </>
  )
}

export default AlertCreator
