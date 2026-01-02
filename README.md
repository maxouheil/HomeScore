# 🏠 HomeScore - AI-Powered Apartment Scoring System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5-green.svg)](https://gemini.google.com)
[![Playwright](https://img.shields.io/badge/Playwright-Web%20Automation-orange.svg)](https://playwright.dev)

**HomeScore** is an intelligent AI-powered apartment scoring system designed to automatically analyze and evaluate apartment listings from Jinka alerts. It combines web scraping, computer vision, and AI to provide comprehensive apartment assessments with detailed scoring and visual reports.

## ✨ Key Features

### 🤖 AI-Powered Image Analysis

- **Visual Analysis** with Google Gemini API (migrated from OpenAI for 96% cost reduction)
- **Style Detection**: Haussmannian, 70s, modern architecture
- **Open Kitchen Detection**: Automatic identification from photos
- **Luminosity Assessment**: Natural lighting analysis
- **Bathtub Detection**: Visual + textual analysis
- **Ceiling Height Estimation**: Precise height measurement
- **Living Room Size Analysis**: Surface estimation with percentage calculation

### 📊 Rule-Based Scoring

- **6 Evaluation Criteria**: Location (20-25 pts), Price (20 pts), Style (20 pts), Exposure (20 pts), Open Kitchen (10 pts), Bathtub (10 pts)
- **105-Point Scoring System** with tier-based classification (Good/Moyen/Bad)
- **Simple Rules**: Scoring based on structured data (no AI for final scoring)
- **Transparent Logic**: All scoring rules defined in `scoring_config.json`
- **No General Bonus/Malus**: Simplified scoring without general bonus/malus (score max: 105 pts with Place de la Réunion bonus)

### 🏠 Data Extraction

- **Automated Jinka Scraping** with Playwright browser automation
- **Complete Data Extraction**: Price, surface, location, features, photos
- **Smart Photo Download**: Up to 5 photos per apartment

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+ and npm (for frontend)
- Playwright
- Google Gemini API Key (or OpenAI API Key for legacy support)

### Installation

```bash
# Clone the repository
git clone https://github.com/maxouheil/HomeScore.git
cd HomeScore

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright
playwright install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file with your credentials:

```env
JINKA_EMAIL=your_email@example.com
JINKA_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
# Optional: OpenAI API Key (for legacy support)
OPENAI_API_KEY=your_openai_api_key
```

## 🎯 Usage

### Development Mode (React Frontend + Backend API)

Start the development server with hot reload:

```bash
python dev.py
```

This will:

- Start the FastAPI backend on `http://localhost:8000`
- Start the React frontend on `http://localhost:5173`
- Open your browser automatically
- Watch for file changes and reload automatically

### Complete Workflow (Traditional)

```bash
# 1. Scrape apartments and analyze with AI (images)
python scrape.py <alert_url>

# 2. Calculate scores and generate HTML report
python homescore.py
```

### Individual Steps

```bash
# Scrape apartments
python scrape.py <alert_url>

# Calculate scores only
python -c "from scoring import score_all_apartments, load_scraped_apartments; import json; apartments = load_scraped_apartments(); scores = score_all_apartments(apartments); json.dump(scores, open('data/scores.json', 'w'), indent=2)"

# Generate HTML only
python generate_html.py
```

### New: Gemini-Based Analysis Tools

#### Analyze a Specific Apartment

```bash
python analyser_appartement.py 'titre ou ID' [url_photo1] [url_photo2] ...
```

Example:
```bash
python analyser_appartement.py '770k · Goncourt'
```

This performs a complete analysis with 6 steps:
1. Architectural style analysis
2. Bathtub detection
3. Open kitchen detection
4. Luminosity and vis-à-vis estimation
5. Ceiling height estimation
6. Living room size analysis with percentage

#### Search Apartments

```bash
python trouver_appartement.py
```

## 📁 Project Structure

```
HomeScore/
├── 🐍 Backend (Python)
│   ├── backend/
│   │   ├── main.py              # FastAPI server
│   │   ├── api/
│   │   │   └── apartments.py    # REST API endpoints
│   │   └── watch_service.py      # File watching + WebSocket
│   ├── homescore.py              # Orchestrateur central
│   ├── scrape.py                 # Scraping + analyse IA images
│   ├── scoring.py                # Calcul scores (règles simples)
│   ├── generate_scorecard_html.py # Génération HTML statique
│   ├── gemini_analyzer.py        # Module d'analyse avec Gemini API
│   ├── analyser_appartement.py   # Script d'analyse complète d'appartement
│   ├── trouver_appartement.py    # Script de recherche d'appartements
│   ├── criteria/                 # Un fichier par critère
│   │   ├── localisation.py
│   │   ├── prix.py
│   │   ├── style.py
│   │   ├── exposition.py
│   │   ├── cuisine.py
│   │   └── baignoire.py
│   └── data/
│       ├── scraped_apartments.json
│       └── scores/
│           └── all_apartments_scores.json
│
├── ⚛️ Frontend (React + Vite)
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx           # Main React component
│   │   │   ├── components/
│   │   │   │   ├── ApartmentCard.jsx
│   │   │   │   ├── Carousel.jsx
│   │   │   │   └── ScoreBadge.jsx
│   │   │   └── utils/
│   │   │       └── scoreUtils.js # Score calculation utilities
│   │   └── package.json
│
└── 📄 Scripts
    └── dev.py                    # Development server launcher
```

## 🎯 Scoring Criteria

The system evaluates apartments on 6 key criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Location** | 20pts | Preferred neighborhoods, metro proximity |
| **Price** | 20pts | Price per m² with customizable thresholds |
| **Style** | 20pts | Haussmannian architecture, modernity (from AI image analysis) |
| **Exposure** | 10pts | Orientation, luminosity (from AI image analysis) |
| **Open Kitchen** | 10pts | Presence and opening possibilities (from AI image analysis) |
| **Bathtub** | 10pts | Presence of bathtub (from AI image/text analysis) |

## 🔄 Data Flow

```
1. SCRAPING + AI ANALYSIS
   scrape.py
   ├─ scrape_jinka.py (scraping)
   ├─ analyze_apartment_style.py (AI images: style, cuisine, luminosité)
   └─ extract_exposition.py (exposition analysis)
   ↓
   data/scraped_apartments.json

2. SCORING (Rules-Based)
   scoring.py
   ├─ Uses scoring_config.json for rules
   ├─ Calculates scores from structured data
   └─ NO AI for scoring (only for image analysis)
   ↓
   data/scores.json

3. HTML GENERATION
   generate_html.py
   ├─ Uses criteria/*.py for formatting
   └─ Generates output/homepage.html
```

## 💰 Costs

### Google Gemini API (Current)

- **Gemini 2.5 Flash**: $0.000075 per image (free up to 15 requests/minute)
- **Gemini 2.5 Pro**: $0.001315 per image (for more precise analyses)

The system includes automatic rate limiting to respect free quotas.

**Cost Reduction**: Migration from OpenAI to Gemini resulted in 96% cost reduction.

### Legacy: OpenAI API

- **GPT-4 Vision**: ~$0.01-0.03 per image (legacy support available)

## 🎨 Output Format

Each criterion is displayed with:

- **Main Value**: Formatted according to criterion type
- **Confidence**: Percentage (when available from AI analysis)
- **Indices**: Supporting details (when available)

Examples:

- **LOCALISATION**: "Metro Ménilmontant · Belleville"
- **PRIX**: "11,500 / m² · Moyen"
- **STYLE**: "Haussmannien (85% confiance)" + "Indices: Moulures · cheminée · parquet"
- **EXPOSITION**: "Lumineux (90% confiance)" + "3e étage · pas de vis à vis"
- **CUISINE OUVERTE**: "Ouverte (95% confiance)" + "Analyse photo : Cuisine ouverte détectée"
- **BAIGNOIRE**: "Oui (80% confiance)" + "Analyse photo : Baignoire détectée"

## 🛠️ Development

### Architecture Principles

- **Separation of Concerns**: One file per criterion, one file per major function
- **AI Only for Images**: IA used only for image analysis (indices + confidence), not for scoring
- **Simple Rules**: Scoring uses simple rules from `scoring_config.json`
- **Single Source of Truth**: One JSON file per data type (`scraped_apartments.json`, `scores.json`)

### Adding a New Criterion

1. Create `criteria/new_criterion.py` with `format_new_criterion()` function
2. Add scoring logic in `scoring.py` (if needed)
3. Update `criteria/__init__.py` to export the function
4. Add to `criteria_mapping` in `generate_html.py`

## 🎨 Frontend Features

### Real-Time Updates

- **WebSocket Integration**: Automatic refresh when data files change
- **Hot Module Replacement**: Instant UI updates during development
- **Responsive Design**: 3-column grid layout, mobile-friendly

### Component Architecture

- **ApartmentCard**: Individual apartment display with all criteria
- **Carousel**: Image carousel with navigation dots
- **ScoreBadge**: Dynamic score badge with color coding
- **Smart Data Formatting**: Automatic extraction of prix, quartier, étage, prix/m²

## 📊 Progrès d'aujourd'hui (Today's Progress)

### ✅ Réalisations

- **Migration vers Gemini API** : Remplacement d'OpenAI par Google Gemini pour réduire les coûts de 96%
- **Module d'analyse complet** : Création du module `gemini_analyzer.py` avec :
  - Support de plusieurs modèles (Flash et Pro)
  - Rate limiting automatique
  - Gestion des images (URLs, fichiers locaux)
  - Parsing JSON automatique
  - Retry logic avec backoff exponentiel

- **Script d'analyse d'appartement** : Développement de `analyser_appartement.py` avec :
  - Recherche d'appartement par titre/ID
  - Analyse complète en 6 étapes :
    1. Analyse du style architectural
    2. Détection de baignoire
    3. Détection de cuisine ouverte
    4. Estimation de la luminosité et vis-à-vis
    5. Estimation de la hauteur de plafond
    6. Analyse de la pièce de vie avec pourcentage
  - Calcul automatique des coûts
  - Sauvegarde des résultats en JSON

- **Script de recherche** : Création de `trouver_appartement.py` pour rechercher des appartements avec système de scoring multi-critères

### 🔄 Améliorations techniques

- Gestion intelligente des chemins de photos (locaux et URLs)
- Support de multiples sources de données JSON
- Calcul précis du nombre d'images analysées pour l'estimation des coûts
- Gestion d'erreurs robuste avec retry automatique

## 📈 Roadmap

### Version 2.1 ✅

- [x] Web interface for visualization (React + Vite)
- [x] REST API for external integration (FastAPI)
- [x] Real-time updates via WebSocket
- [x] Migration to Gemini API for cost reduction
- [ ] Email notifications for new apartments
- [ ] CSV/Excel data export

### Version 2.2

- [ ] Integration with other real estate platforms
- [ ] Monitoring dashboard
- [ ] Advanced filtering and sorting
- [ ] Batch analysis tools

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 📝 Documentation Conventions

**⚠️ IMPORTANT**: When referencing project paths in Markdown files:

- ✅ **CORRECT**: `Cursor/homescore` (no space)
- ❌ **FORBIDDEN**: `Cursor /homescore` (with space)

Always use `Cursor/homescore` without space in all `.md` files. See `RÈGLE_CHEMINS_FICHIERS.md` for more details.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 📞 Support

For questions or issues:

- Open an issue on GitHub
- Contact: souheil.medaghri@gmail.com

---

**HomeScore** - Transform your Jinka alerts into intelligent insights! 🏠✨
