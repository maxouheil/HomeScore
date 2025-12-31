import { useState, useMemo } from 'react'
import ScoreBadge from './ScoreBadge'
import './Carousel.css'

// Fonction pour formater la date au format "1er dec"
function formatPublicationDate(dateString) {
  if (!dateString) return null
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return null
    
    const day = date.getDate()
    const month = date.getMonth() // 0-11
    
    // Noms des mois en abrégé
    const monthNames = ['jan', 'fév', 'mar', 'avr', 'mai', 'jun', 'jul', 'aoû', 'sep', 'oct', 'nov', 'dec']
    const monthName = monthNames[month]
    
    // Formater le jour: "1er" pour le 1, sinon le nombre
    const dayFormatted = day === 1 ? '1er' : day.toString()
    
    return `${dayFormatted} ${monthName}`
  } catch (e) {
    return null
  }
}

function Carousel({ photos, carouselId, score, maxScore = 90, apartment = null, alertCriteria = null }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [failedImages, setFailedImages] = useState(new Set())
  
  // Formater la date de publication
  const publicationDate = useMemo(() => {
    if (!apartment) return null
    const dateStr = apartment.date_creation_annonce || apartment.scraped_at || null
    return formatPublicationDate(dateStr)
  }, [apartment])
  
  if (!photos || photos.length === 0) {
    return (
      <div className="apartment-image-container">
        {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />}
        {publicationDate && (
          <div className="publication-date-tag">{publicationDate}</div>
        )}
        <div className="apartment-image-placeholder">📷</div>
      </div>
    )
  }
  
  // Filtrer les photos qui ont échoué
  const validPhotos = photos.filter((_, index) => !failedImages.has(index))
  
  // Si toutes les images ont échoué, afficher le placeholder
  if (validPhotos.length === 0) {
    return (
      <div className="apartment-image-container">
        {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />}
        {publicationDate && (
          <div className="publication-date-tag">{publicationDate}</div>
        )}
        <div className="apartment-image-placeholder">📷</div>
      </div>
    )
  }
  
  if (validPhotos.length === 1) {
    return (
      <div className="apartment-image-container">
        {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />}
        {publicationDate && (
          <div className="publication-date-tag">{publicationDate}</div>
        )}
        <div 
          className="apartment-image" 
          style={{ backgroundImage: `url(${validPhotos[0]})` }}
        />
      </div>
    )
  }
  
  const nextSlide = (e) => {
    e.stopPropagation()
    // Trouver la prochaine image valide
    let nextIndex = (currentIndex + 1) % photos.length
    let attempts = 0
    while (failedImages.has(nextIndex) && attempts < photos.length) {
      nextIndex = (nextIndex + 1) % photos.length
      attempts++
    }
    if (!failedImages.has(nextIndex)) {
      setCurrentIndex(nextIndex)
    }
  }
  
  const prevSlide = (e) => {
    e.stopPropagation()
    // Trouver l'image valide précédente
    let prevIndex = (currentIndex - 1 + photos.length) % photos.length
    let attempts = 0
    while (failedImages.has(prevIndex) && attempts < photos.length) {
      prevIndex = (prevIndex - 1 + photos.length) % photos.length
      attempts++
    }
    if (!failedImages.has(prevIndex)) {
      setCurrentIndex(prevIndex)
    }
  }
  
  const goToSlide = (index, e) => {
    e.stopPropagation()
    if (!failedImages.has(index)) {
      setCurrentIndex(index)
    }
  }
  
  const handleImageError = (index) => {
    // Ajouter l'image à la liste des images échouées
    setFailedImages(prev => {
      const newSet = new Set([...prev, index])
      // Si c'est l'image actuelle qui échoue, passer à la suivante valide
      if (index === currentIndex) {
        let nextIndex = (index + 1) % photos.length
        let attempts = 0
        while (newSet.has(nextIndex) && attempts < photos.length) {
          nextIndex = (nextIndex + 1) % photos.length
          attempts++
        }
        if (!newSet.has(nextIndex)) {
          setTimeout(() => setCurrentIndex(nextIndex), 0)
        }
      }
      return newSet
    })
  }
  
  return (
    <div className="apartment-image-container">
      {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} apartment={apartment} alertCriteria={alertCriteria} />}
      {publicationDate && (
        <div className="publication-date-tag">{publicationDate}</div>
      )}
      <div className="carousel-container" data-carousel-id={carouselId}>
        <button 
          className="carousel-nav prev" 
          onClick={prevSlide}
        >
          ‹
        </button>
        <div className="carousel-track" style={{ transform: `translateX(-${currentIndex * 100}%)` }}>
          {photos.map((photo, index) => (
            <div key={index} className="carousel-slide" style={{ display: failedImages.has(index) ? 'none' : 'block' }}>
              <img 
                src={photo} 
                alt={`Photo ${index + 1}`}
                onError={() => {
                  handleImageError(index)
                }}
                loading="lazy"
              />
            </div>
          ))}
        </div>
        <button 
          className="carousel-nav next" 
          onClick={nextSlide}
        >
          ›
        </button>
        <div className="carousel-dots">
          {photos.map((_, index) => {
            if (failedImages.has(index)) return null
            return (
              <div
                key={index}
                className={`carousel-dot ${index === currentIndex ? 'active' : ''}`}
                onClick={(e) => goToSlide(index, e)}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default Carousel
