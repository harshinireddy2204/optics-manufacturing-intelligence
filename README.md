# Coherent Optics Manufacturing Data Intelligence Dashboard

**A portfolio project demonstrating end-to-end data analyst capabilities for optical transceiver manufacturing operations - modeled on Cisco/Acacia's 800G and 1.6T coherent pluggable production environment.**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-green)
![SPC](https://img.shields.io/badge/Six_Sigma-SPC/Cpk-orange)

**Live Demo**: https://optics-manufacturing-intelligence.streamlit.app/

---

## Why This Project Exists

Coherent optical transceivers - the modules that carry 800 Gbps and 1.6 Tbps over fiber - are among the most precision-intensive products in commercial electronics manufacturing. Each module combines a DSP ASIC fabricated at 4nm with silicon photonic components requiring sub-micron optical alignment, then undergoes multi-station automated testing covering optical power, bit error rate, extinction ratio, OSNR, TDECQ, and more.

At production scale, this generates millions of test records per month across heterogeneous systems. The data infrastructure challenge - keeping that data clean, reconciled, and actionable - is what makes manufacturing data analyst roles critical in this space.

This project simulates that environment end-to-end:

- **Realistic synthetic data** modeled on actual coherent transceiver test parameters and manufacturing process behavior
- **Data quality engine** that detects missing values, duplicates, malformed records, and naming inconsistencies
- **SPC analysis** with X-bar control charts, Cp/Cpk calculations, and process drift detection
- **Manufacturing line monitoring** with shift-level variability analysis and equipment tracking
- **SQL patterns** demonstrating production-ready query optimization for operational datasets

---

## Job Description Coverage Map

Every line item from the Product Line Data Analyst role is addressed:

| JD Requirement | Where It's Demonstrated |
|---|---|
| Data hygiene and reconciliation (missing, duplicate, malformed, inconsistent) | Tab 2: Data Quality Engine - 5 automated detection categories |
| Analyze test/manufacturing data for trends, anomalies, yield issues, deviations | Tab 3: SPC analysis, weekly yield trends, anomaly flagging |
| Monitor manufacturing-line data systems for quality, completeness, consistency | Tab 4: Cross-line comparison, shift variability, drift detection |
| Create recurring and ad hoc reports for engineering/operations/management | Tab 1: Executive summary with KPIs, heatmaps, volume trends |
| Develop/maintain/optimize SQL queries, views, stored procedures | Tab 5: 4 production-ready SQL patterns with optimization notes |
| ETL-style data extraction and transformation workflows | Tab 5: Python ETL pipeline class + data generation code |
| Python-based extraction, cleansing, transformation, validation | `data/generate_data.py` + ETL class in Tab 5 |
| SQL: joins, aggregations, CTEs, performance-conscious design | Tab 5: CTE pre-aggregation, window functions, covering indexes |
| SPC, Cp/Cpk, yield analysis | Tab 3: Full SPC control charts, Cp/Cpk by line, spec limit overlays |
| Pandas for data manipulation and analysis | Throughout - all data processing uses pandas |
| Data preparation for dashboards / BI tools | The entire Streamlit application |

---

## Domain Knowledge Demonstrated

### Coherent Optical Transceiver Parameters
- **Tx Optical Power (dBm)** - laser output intensity, critical for link budget
- **Rx Sensitivity (dBm)** - minimum detectable signal level
- **Pre-FEC BER** - bit error rate before forward error correction
- **OSNR (dB)** - optical signal-to-noise ratio
- **TDECQ (dB)** - Transmitter Dispersion Eye Closure for PAM4 (800G/1.6T specific)
- **Extinction Ratio (dB)** - signal contrast ratio
- **Wavelength Offset (pm)** - deviation from ITU grid (C-band tunable lasers)
- **DSP Lock Time (ms)** - coherent DSP acquisition time

### Manufacturing Process Context
- **Multi-station test flow**: Wafer Test → Optical Alignment → Module Parametric → Burn-In → Final Test
- **Process variations**: Line-to-line differences, shift effects, product complexity impact
- **Deliberate drift injection**: Simulates calibration drift on Line-A starting mid-March
- **Data quality issues**: Missing values, duplicate logging, serial number corruption, naming inconsistencies - the exact problems an ops data analyst resolves daily

### Product Lines Modeled
- **800G-ZR QSFP-DD** - Delphi DSP, metro DCI (highest volume)
- **800G-ZR+ OSFP** - Delphi DSP, extended reach
- **400G-ZR+ QSFP-DD** - Greylock DSP, sustaining production
- **1.6T-DR8 OSFP** - Kibo DSP, new product ramp (lowest yield, highest complexity)

---

## Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Dashboard | Streamlit |
| Visualization | Plotly (interactive charts) |
| Data Processing | pandas, NumPy |
| Statistical Analysis | SciPy (stats module) |
| SQL Patterns | T-SQL (SQL Server compatible) |
| Deployment | Streamlit Cloud / local |

---

## Project Structure

```
optics-ops-dashboard/
├── app.py                      # Main Streamlit dashboard (5 tabs)
├── data/
│   ├── generate_data.py        # Synthetic data generator
│   ├── optics_test_data.csv    # 60K+ test records
│   ├── equipment_registry.csv  # Test equipment metadata
│   ├── yield_targets.csv       # Yield targets by product/station
│   └── spec_limits.json        # Specification limits for all parameters
├── requirements.txt
└── README.md
```

---

## Running Locally

```bash
git clone https://github.com/harshinireddy2204/optics-manufacturing-intelligence.git
cd optics-manufacturing-intelligence
pip install -r requirements.txt
python data/generate_data.py    # Generate synthetic data
streamlit run app.py
```

---

## Key Findings from the Simulated Data

1. **Line-C-Lowell** shows consistently higher variability - expected for a newer production line still in ramp
2. **Night shift** has ~10% higher standard deviation across optical parameters - a known staffing/fatigue effect
3. **1.6T products** have the lowest yield (~90%) - expected given the tighter tolerances and newer manufacturing process
4. **Process drift on Line-A** starting mid-March - this is the type of issue SPC monitoring catches before it becomes a yield crisis
5. **Data quality score of ~97%** - the 3% gap is driven by duplicate logging, sensor glitches, and naming inconsistencies

---

## About

Built by **Harshini Reddy** as a portfolio project for the Cisco Optics Operations Product Line Data Analyst role. Combines domain knowledge in electronics and DSP (academic background), data engineering and SQL optimization (professional experience at Société Générale), and manufacturing analytics (Six Sigma methodology).

- **LinkedIn**: [linkedin.com/in/harshinireddy2204](https://linkedin.com/in/harshinireddy2204)
- **Portfolio**: [harshinireddy2204.github.io/portfolio](https://harshinireddy2204.github.io/portfolio)
- **GitHub**: [github.com/harshinireddy2204](https://github.com/harshinireddy2204)