import { useState } from 'react'
import ScoreBadge from './ScoreBadge'
import './Carousel.css'

function Carousel({ photos, carouselId, score, maxScore = 90 }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  
  if (!photos || photos.length === 0) {
    return (
      <div className="apartment-image-container">
        {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} />}
        <div className="apartment-image-placeholder">📷</div>
      </div>
    )
  }
  
  if (photos.length === 1) {
    return (
      <div className="apartment-image-container">
        {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} />}
        <div 
          className="apartment-image" 
          style={{ backgroundImage: `url(${photos[0]})` }}
        />
      </div>
    )
  }
  
  const nextSlide = (e) => {
    e.stopPropagation()
    setCurrentIndex((prev) => (prev + 1) % photos.length)
  }
  
  const prevSlide = (e) => {
    e.stopPropagation()
    setCurrentIndex((prev) => (prev - 1 + photos.length) % photos.length)
  }
  
  const goToSlide = (index, e) => {
    e.stopPropagation()
    setCurrentIndex(index)
  }
  
  return (
    <div className="apartment-image-container">
      {score !== undefined && <ScoreBadge score={score} maxScore={maxScore} />}
      <div className="carousel-container" data-carousel-id={carouselId}>
        <button 
          className="carousel-nav prev" 
          onClick={prevSlide}
        >
          ‹
        </button>
        <div className="carousel-track" style={{ transform: `translateX(-${currentIndex * 100}%)` }}>
          {photos.map((photo, index) => (
            <div key={index} className="carousel-slide">
              <img 
                src={photo} 
                alt={`Photo ${index + 1}`}
                onError={(e) => {
                  console.error('Erreur chargement image:', photo)
                  e.target.parentElement.style.display = 'none'
                }}
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
          {photos.map((_, index) => (
            <div
              key={index}
              className={`carousel-dot ${index === currentIndex ? 'active' : ''}`}
              onClick={(e) => goToSlide(index, e)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default Carousel

