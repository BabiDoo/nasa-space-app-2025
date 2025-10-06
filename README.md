# 🌌 ExoSeeker

[![Made with Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org/)  
[![Framework PyTorch](https://img.shields.io/badge/Framework-PyTorch-red?logo=pytorch)](https://pytorch.org/)  
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![NASA Data](https://img.shields.io/badge/Data-NASA%20Exoplanet%20Archive-orange)](https://exoplanetarchive.ipac.caltech.edu/)  

**ExoSeeker** is an **end-to-end Artificial Intelligence platform** designed to accelerate the discovery of **exoplanets**.  
It unifies heterogeneous datasets from NASA missions **Kepler, K2, and TESS**, applying **Explainable AI** for robust and transparent classifications.  

---

## 📖 Summary
ExoSeeker automates the classification of exoplanet candidates.  
We tested multiple models: **Decision Tree, KNN, Naive Bayes, Random Forest, LightGBM, and 1D-CNN**, prioritizing **F1-score** as the main metric.  

Key features:  
✅ Consolidates data from NASA catalogs  
✅ Balances and cleans datasets  
✅ Uses Explainable AI (SHAP + Grad-CAM)  
✅ Provides web interface for analysis & PDF reports  
✅ Open-source, reproducible, and globally accessible  

---

## 🔬 Project Details
ExoSeeker addresses one of astronomy’s greatest challenges:  
the exponential growth of exoplanet data that still requires time-consuming human validation.  

### 🛠️ Technical Highlights
- **Languages & Frameworks:** Python, PyTorch/Lightning, LightGBM  
- **Optimization:** Optuna (hyperparameter tuning)  
- **Web Stack:** FastAPI, Next.js, Plotly  
- **Data Storage:** PostgreSQL, Redis  
- **Reproducibility:** conda-lock environments, fixed seeds  

### ⚙️ How It Works
1. **Data Pipeline** → Ingests Kepler, K2, and TESS datasets.  
2. **Training** → Runs multiple ML models for robust classification.  
3. **Explainability** → SHAP + Grad-CAM show *why* a signal is labeled as a planet.  
4. **Interface** → Upload data, run analysis, view metrics, download PDF reports.  

---

## 🤖 Use of Artificial Intelligence
AI was the core of this project:  

- **Classification:** ML models detect planets vs. false positives.  
- **Evaluation:** Balanced datasets, hyperparameter tuning, F1-score optimization.  
- **Explainability:** SHAP & Grad-CAM for transparency.  
- **Integration:** Web interface connects models to user workflows.  

**Acknowledgment of AI Use**  
- All AI outputs are documented and labeled.  
- No NASA logos or branding were used.  
- Any illustrative AI-generated media includes watermarks.  

---

## 🛰️ NASA Data Sources
- [Kepler Objects of Interest (KOI)](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=cumulative)  
- [TESS Objects of Interest (TOI)](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=TOI)  
- [K2 Planets and Candidates](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=k2pandc)  

---

---

## 👩‍🚀 Team Members

| Name | Country | Role |
|------|---------------|---------|------|
| **Marina Corrêa Freitas** (Team Owner) | Brazil | Project Lead |
| **Luiza Arievilo** | Brazil | Research |
| **Márcia Saori Câmara Kishi**  | Brazil | Research & Design |
| **Jannaina Anita Sangaletti** | Brazil | Machine Learning & Data |
| **Samantha Nunes** | Brazil | Frontend & UX |
| **Barbara Lais Dorneles Martins** | Brazil | Backend & Integration |

---

✨ *ExoSeeker accelerates exoplanet discovery and makes science transparent, reliable, and open to all.*
