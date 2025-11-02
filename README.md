# 🏠 HomeScore - AI-Powered Apartment Scoring System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com)
[![Playwright](https://img.shields.io/badge/Playwright-Web%20Automation-orange.svg)](https://playwright.dev)

**HomeScore** is an intelligent AI-powered apartment scoring system designed to automatically analyze and evaluate apartment listings from Jinka alerts. It combines web scraping, computer vision, and AI to provide comprehensive apartment assessments with detailed scoring and visual reports.

## ✨ Key Features

### 🤖 AI-Powered Image Analysis
- **Visual Analysis** with OpenAI Vision API
- **Style Detection**: Haussmannian, 70s, modern architecture
- **Open Kitchen Detection**: Automatic identification from photos
- **Luminosity Assessment**: Natural lighting analysis
- **Bathtub Detection**: Visual + textual analysis

### 📊 Rule-Based Scoring
- **6 Evaluation Criteria**: Location (20-25 pts), Price (20 pts), Style (20 pts), Exposure (10 pts), Open Kitchen (10 pts), Bathtub (10 pts)
- **95-Point Scoring System** with tier-based classification (Good/Moyen/Bad)
- **Simple Rules**: Scoring based on structured data (no AI for final scoring)
- **Transparent Logic**: All scoring rules defined in `scoring_config.json`
- **No General Bonus/Malus**: Simplified scoring without general bonus/malus (score max: 95 pts with Place de la Réunion bonus)

### 🏠 Data Extraction
- **Automated Jinka Scraping** with Playwright browser automation
- **Complete Data Extraction**: Price, surface, location, features, photos
- **Smart Photo Download**: Up to 5 photos per apartment

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Playwright
- OpenAI API Key

### Installation
```bash
# Clone the repository
git clone https://github.com/maxouheil/HomeScore.git
cd HomeScore

# Install dependencies
pip install -r requirements.txt

# Install Playwright
playwright install

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration
Create a `.env` file with your credentials:
```env
JINKA_EMAIL=your_email@example.com
JINKA_PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
```

## 🎯 Usage

### Complete Workflow
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

## 📁 Project Structure (Simplified)

```
HomeScore/
├── homescore.py              ⭐ Orchestrateur central
├── scrape.py                 ⭐ Scraping + analyse IA images
├── scoring.py                ⭐ Calcul scores (règles simples)
├── generate_html.py          ⭐ Génération HTML unique
├── criteria/                 ⭐ Un fichier par critère
│   ├── __init__.py
│   ├── localisation.py       # Formatage "Metro · Quartier"
│   ├── prix.py               # Formatage "X / m² · Good/Moyen/Bad"
│   ├── style.py              # Formatage "Style (X% confiance) + indices"
│   ├── exposition.py         # Formatage "Lumineux/Moyen/Sombre (X% confiance)"
│   ├── cuisine.py            # Formatage "Ouverte/Semi/Fermée (X% confiance)"
│   └── baignoire.py          # Formatage "Oui/Non (X% confiance)"
├── scrape_jinka.py           # Scraper Jinka (utilisé par scrape.py)
├── analyze_apartment_style.py # Analyse IA images (utilisé par scrape.py)
├── extract_baignoire.py       # Détection baignoire (utilisé par criteria/baignoire.py)
├── extract_exposition.py      # Extraction exposition (utilisé par scrape_jinka.py)
├── data/
│   ├── scraped_apartments.json    # Source unique scrapée + analyses IA
│   └── scores.json                # Source unique scores calculés
└── output/
    └── homepage.html              # UN SEUL fichier HTML généré
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

## 📈 Roadmap

### Version 2.1
- [ ] Web interface for visualization
- [ ] Email notifications for new apartments
- [ ] CSV/Excel data export

### Version 2.2
- [ ] Integration with other real estate platforms
- [ ] REST API for external integration
- [ ] Monitoring dashboard

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Contact: souheil.medaghri@gmail.com

---

**HomeScore** - Transform your Jinka alerts into intelligent insights! 🏠✨
