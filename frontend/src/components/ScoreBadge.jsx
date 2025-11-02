function ScoreBadge({ score, maxScore = 90 }) {
  const percentage = (score / maxScore) * 100
  let color = "#F85457" // Rouge par défaut
  
  if (percentage >= 80) {
    color = "#00966D" // Vert
  } else if (percentage >= 60) {
    color = "#F59E0B" // Jaune
  }
  
  // Formater le score pour l'affichage
  const displayScore = score === Math.floor(score) ? Math.floor(score) : score
  const displayStr = String(displayScore) === "00" ? "0" : String(displayScore)
  
  return (
    <div 
      className="score-badge-top" 
      style={{ background: color }}
    >
      {displayStr}
    </div>
  )
}

export default ScoreBadge

