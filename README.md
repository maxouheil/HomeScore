# 🏠 HomeScore - AI-Powered Apartment Scoring System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com)
[![Playwright](https://img.shields.io/badge/Playwright-Web%20Automation-orange.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**HomeScore** is an intelligent AI-powered apartment scoring system designed to automatically analyze and evaluate apartment listings from Jinka alerts. It combines web scraping, computer vision, and AI to provide comprehensive apartment assessments with detailed scoring and visual reports.

## ✨ Key Features

### 🤖 AI-Powered Scoring
- **6 Evaluation Criteria**: Location, Price, Style, Exposure, Open Kitchen, Floor
- **100-Point Scoring System** with tier-based classification (Excellent/Good/Average)
- **OpenAI Integration** for contextual analysis and score justification
- **Smart Exposure Analysis**: Textual + Photo analysis with Vision API

### 🏠 Data Extraction
- **Automated Jinka Scraping** with Playwright browser automation
- **Complete Data Extraction**: Price, surface, location, features, photos
- **Photo Download**: 3-4 photos per apartment stored locally
- **Metro Station Analysis**: Automatic extraction for location context

### 📸 Visual Analysis
- **Photo Analysis** with OpenAI Vision API
- **Style Detection**: Haussmannian, 70s, modern architecture
- **Open Kitchen Detection**: Automatic identification
- **Luminosity Assessment**: Natural lighting analysis

### 📊 Report Generation
- **Professional HTML Reports** with modern design
- **Two Styles**: Fitscore (3-column grid) and Original layout
- **Integrated Photos**: Apartment images in reports
- **Detailed Scores**: Justification for each criterion

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

### Quick Demo
```bash
python demo_final_complete.py
```

### Scrape Apartments
```bash
python scrape_jinka.py
```

### Batch Processing
```bash
python batch_scrape_known_urls.py
```

## 📁 Project Structure

```
HomeScore/
├── 📄 scrape_jinka.py              # Main Jinka scraper
├── 📄 score_appartement.py         # AI scoring module
├── 📄 generate_scorecard_html.py   # HTML report generator
├── 📄 extract_exposition.py        # Exposure analysis
├── 📄 analyze_apartment_style.py   # Photo analysis
├── 📄 batch_scrape_known_urls.py   # Batch processing
├── 📄 demo_final_complete.py       # Complete demonstration
├── 📁 data/                        # Scraped data
│   ├── 📁 appartements/            # Apartment JSON files
│   └── 📁 photos/                  # Downloaded photos
├── 📁 output/                      # Generated HTML reports
└── 📄 requirements.txt             # Python dependencies
```

## 🎯 Scoring Criteria

The system evaluates apartments on 6 key criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Location** | 20pts | Preferred neighborhoods, metro proximity |
| **Price** | 20pts | Price per m² with customizable thresholds |
| **Style** | 20pts | Haussmannian architecture, modernity |
| **Exposure** | 10pts | Orientation, luminosity, view quality |
| **Open Kitchen** | 10pts | Presence and opening possibilities |
| **Floor** | 10pts | Optimal height, elevator access |

## 📊 Current Performance

- **18 apartments** successfully processed
- **55 photos** downloaded and analyzed
- **Average score**: 77.2/100
- **Processing time**: ~2-3 minutes per apartment

### Sample Results
- **Apartment 1**: 90/100 (EXCELLENT) - Haussmannian, 4th floor, open kitchen
- **Apartment 2**: 85/100 (EXCELLENT) - Prime location, good price
- **Apartment 3**: 53/100 (AVERAGE) - Exposure and floor issues

## 🔧 Advanced Features

### Intelligent Exposure Analysis
- **Phase 1**: Textual analysis of descriptions
- **Phase 2**: Photo analysis with Vision API
- **Phase 3**: Contextual analysis (neighborhood, architecture)
- **Combination**: Final score based on all sources

### Tier System
- **Tier 1 (Excellent)**: 8-10 points
- **Tier 2 (Good)**: 6-7 points  
- **Tier 3 (Average/Problematic)**: 0-5 points

### Automation
- **Daily Scraping**: Automatic detection of new listings
- **Automatic Scoring**: AI evaluation of new apartments
- **Automatic Reports**: Daily HTML generation

## 🛠️ Development

### Testing
```bash
# Complete system test
python test_homescore.py

# Exposure extraction test
python test_exposition_complete.py

# Scoring test
python test_new_scoring.py
```

### Debugging
```bash
# Scraping debug
python debug_html.py

# Jinka connection test
python test_connection.py
```

## 📈 Roadmap

### Version 1.1
- [ ] Web interface for visualization
- [ ] Email notifications for new apartments
- [ ] CSV/Excel data export
- [ ] Advanced scoring filters

### Version 1.2
- [ ] Integration with other real estate platforms
- [ ] Machine Learning for score improvement
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

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=maxouheil/HomeScore&type=Date)](https://star-history.com/#maxouheil/HomeScore&Date)