# State Health Vulnerability Index

An exploratory project that compares Indian states and union territories using five selected health and living-condition indicators from the National Family Health Survey 5 (NFHS-5). It includes a Jupyter notebook for the original analysis and a Streamlit dashboard for exploring the results and looking up a state by name.

> The index is a custom, relative score for exploration. It is not an official government rating, clinical assessment, or measure of an individual's health.

## Project contents

```text
.
├── State_Health_Vulnerability_Index.ipynb  # Original analysis notebook
├── app.py                                  # Interactive Streamlit dashboard
├── requirements.txt                        # Dashboard dependencies
└── README.md
```

Add the supplied `State_Health_Vulnerability_Index.ipynb` to the repository root alongside these files. The notebook is kept separate from the website app.

## Data

The notebook and dashboard load the NFHS-5 state data CSV from:

<https://raw.githubusercontent.com/pratapvardhan/NFHS-5/master/NFHS-5-States.csv>

They require internet access to retrieve the file. The overall `India` row is excluded so the analysis compares states and union territories.

## Indicators and scoring

The project uses these five indicators:

| Indicator | Score direction | Weight |
| --- | --- | ---: |
| High or very high blood sugar | Increases vulnerability | 0.30 |
| Elevated blood pressure | Increases vulnerability | 0.30 |
| Health insurance | Reduces vulnerability | 0.15 |
| Clean fuel for cooking | Reduces vulnerability | 0.15 |
| Improved sanitation | Reduces vulnerability | 0.10 |

Rows are grouped by state and indicator and averaged. The original notebook averages any separate records present for a state/indicator, such as men's and women's records. Rows without all five indicators are excluded from the composite index.

```text
raw_score = 0.30 × High_Blood_Sugar
          + 0.30 × Hypertension
          − 0.15 × Health_Insurance
          − 0.15 × Clean_Fuel
          − 0.10 × Improved_Sanitation

index = 100 × (raw_score − minimum raw_score)
              / (maximum raw_score − minimum raw_score)
```

The index is min–max normalized across the included states/UTs and sorted from highest to lowest.

## Run the dashboard locally

Install Python, then open a terminal in the project folder and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The dashboard includes a report with the top-ten chart and correlation matrix, a state lookup, an all-states table with CSV download, and a methods explanation.

## Run the notebook

Install the notebook's packages:

```bash
python -m pip install pandas seaborn matplotlib
```

Open `State_Health_Vulnerability_Index.ipynb` in Jupyter Notebook or JupyterLab and run its code cell. It creates `heatmap.png` and `top10_states.png` in the notebook's current working directory.

## Deploy the dashboard

Push `app.py` and `requirements.txt` to a GitHub repository, then connect that repository to Streamlit Community Cloud. The deployed app also needs internet access to fetch the source CSV.

## Limitations

- The indicators and weights are chosen for this project and do not establish a validated or official measure of vulnerability.
- The min–max score is relative to the included states and source values; changes to either can change the index.
- Correlation shows association, not causation.
- Do not use the index alone for clinical decisions, resource allocation, or policy decisions.
