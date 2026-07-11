# EMDB

Python scripts for interacting with the Electron Microscopy Data Bank (EMDB) via its REST search API, plus cross-database tools linking EMDB to RCSB PDB and AlphaFold DB. Developed as part of a self-directed study of EMDB/wwPDB data standards and the OneDep curation workflow.

---

## Scripts

### `list_emdb_depositions.py`
Queries the EMDB search API for all entries matching one or more author names and prints a consolidated table (EMD ID, method, resolution, deposition date, title). Exports results to CSV for reuse in other scripts or documents.

```
python list_emdb_depositions.py
```
Edit `AUTHOR_QUERIES` at the top of the script to search under different name variants.

### `career_emdb_deposition_timeline.py`
Generates a visual career timeline combining employment/education history with EMDB deposition dates, using the CSV output from `list_emdb_depositions.py`. Employment periods are drawn as colored bars; depositions are plotted as markers sized by resolution, with automatic jitter to separate dates that cluster closely together.

```
python career_emdb_deposition_timeline.py --csv emdb_depositions_porta.csv --out timeline.png
```
Edit the `EMPLOYMENT` list at the top of the script to update career history.

### `resolution_method_over_time.py`
Plots resolution (Å) over time across depositions, color-coded by project (auto-classified from title keywords), with an inverted y-axis so higher-resolution (lower Å) structures read as "higher" on the chart, plus an overall linear trend line.

```
python resolution_method_over_time.py --csv emdb_depositions_porta.csv --out trend.png
```
Edit `PROJECT_RULES` to adjust how titles are grouped into projects.

### `emdb_validation_report_analyzer.py`
Downloads and parses the wwPDB/EMDB validation report XML for a given entry, flexibly scanning the full XML tree for known QC metric keywords (Q-score, FSC/resolution, clashes, Ramachandran, rotamers, bond/angle RMS, B-factors, 3D-Strudel, EMRinger) rather than relying on hardcoded tag paths.

```
python emdb_validation_report_analyzer.py EMD-8548
python emdb_validation_report_analyzer.py EMD-8548 --raw   # dump all tag/attribute names for tuning
```

### `emdb_deposition_completeness_checker.py`
Checks a given EMD ID against a two-tier completeness checklist: Tier 1 covers fields verifiable via the EMDB search API (title, method, resolution, deposition date, status); Tier 2 lists fields that matter for real completeness but require manual review on the entry's web page (voxel spacing, microscope parameters, specimen prep, half-maps, contour level, etc.), since they aren't exposed by the lightweight search endpoint.

```
python emdb_deposition_completeness_checker.py EMD-25007
```

### `cross_database_search.py`
Given a UniProt accession or free-text protein name, queries RCSB PDB (experimental structures), EMDB (title text match), and AlphaFold DB (predicted models) and prints a combined summary of existing structural data for that target.

```
python cross_database_search.py P0DTC2
python cross_database_search.py "caveolin-1"
```

### `emdb_statistics_dashboard.py`
Pulls field-wide metadata for the full EMDB archive (or a date-limited subset) and generates three summary charts: depositions per year, structure determination method breakdown, and resolution distribution by year. Caches the raw pull to CSV for fast re-plotting.

```
python emdb_statistics_dashboard.py --since 2015
python emdb_statistics_dashboard.py --cache emdb_all_entries.csv   # re-plot from a saved pull


