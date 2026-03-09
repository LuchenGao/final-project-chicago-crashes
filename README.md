# Final Project — Chicago Traffic Crashes & Enforcement Cameras (Group 23)

**Dashboard (Streamlit Community Cloud):** https://final-project-chicago-crashes-g9srdmczqbxunyfhgnttyg.streamlit.app/

> **Note (Streamlit “wake up”):** Streamlit Community Cloud apps can go to sleep after inactivity.  
> If you see a “waking up” / cold-start message, simply open the link and wait ~10–60 seconds, then refresh once.

## Team
- Luchen Gao (GitHub: `LuchenGao`)
- Sirui Mao (GitHub: `sirui0820`)
- Xinyi Liu （Github: `xinyiliu1`）

## Research questions
1. **Are red light and speed cameras placed in higher-risk (higher-crash) areas?**
2. **Do cameras help reduce crash counts and/or crash severity?**

## Repository structure 
```
.
├── README.md
├── requirements.txt
├── final_project.qmd                # writeup source (Quarto)
├── final_project.html               # knitted writeup (HTML)
├── final_project.pdf                # knitted writeup (PDF)
├── code/
│   ├── preprocessing.py             # builds derived datasets
│   └── ...                          # analysis / plotting scripts
├── data/
│   ├── raw-data/                    # original downloads (unmodified)
│   └── derived-data/                # outputs created by preprocessing.py
└── streamlit-app/
    ├── app.py                       # Streamlit entrypoint
    └── community_boundaries.py      # helper to load Chicago community areas
```

## Data sources (Chicago Data Portal)
All datasets are from the City of Chicago’s open data portal:
- **Traffic Crashes – Crashes** (large CSV; see download instructions below)
- **Boundaries – Community Areas**
- **Speed Camera Locations**
- **Red Light Camera Locations**

## Large file note (Traffic Crashes – Crashes)
GitHub has a 100MB file limit, so we **do not** store the full crash CSV in the repo.

**Download link (Google Drive):** https://drive.google.com/file/d/1VP1dcng906Av8EOnhA0mU3BvFT9uHPk8/view?usp=sharing

1. Download the crash CSV from the Drive link above (you may need access/permission).
2. Save it to this exact path (relative to repo root):
   ```
   data/raw-data/Traffic_Crashes_-_Crashes_20260224.csv
   ```
3. Do **not** rename the file (the code expects this filename).

All other (smaller) raw datasets are stored in `data/raw-data/`.

## Reproducibility: run locally
### 1) Install requirements
From the repo root:
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate  # Windows (PowerShell)
pip install -r requirements.txt
```

### 2) Put raw data in the right place
Ensure:
- `data/raw-data/Boundaries_-_Community_Areas_20260122.csv`
- `data/raw-data/Speed_Camera_Locations_20260222.csv`
- `data/raw-data/Red_Light_Camera_Locations_20260122.csv`
- `data/raw-data/Traffic_Crashes_-_Crashes_20260224.csv` (download via Drive)

### 3) Build derived data
From repo root:
```bash
python code/preprocessing.py
```
This should create:
```
data/derived-data/crashes_by_community_year_hour_type.csv
```

### 4) Run the Streamlit app
From repo root:
```bash
streamlit run streamlit-app/app.py
```

## Deployment
The dashboard is deployed on Streamlit Community Cloud using:
- **Branch:** `main`
- **Main file path:** `streamlit-app/app.py`


## Git / branches
During development we used multiple branches (per rubric) for feature work (e.g., dashboard deployment and camera overlays).  
The final submission lives on **`main`**.
