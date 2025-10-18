# Green-Archipelago-Analysis-Tool

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) ![ArcPy](https://img.shields.io/badge/ArcPy-ArcGIS%20Pro-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## 1. Overview

This repository contains a GIS-based decision support tool for **strategic smart farm placement within South Korea's metropolitan greenbelts**. This system provides a quantitative methodology to analyze underutilized land and model a long-term deployment of high-efficiency smart farms, grounded in official national land cover standards.

The tool is designed to answer two critical questions for urban planners and policymakers:

1.  **Where** are the optimal locations to replace inefficient urban parcels with productive smart farms?
2.  **How much** agricultural value can be generated from existing greenbelt resources?

---

## 2. System Architecture & Methodology

This tool is designed as the core analytical engine (Steps 2-4) within a larger, **end-to-end geospatial data pipeline**.

The ultimate vision is a complete 1-4 pipeline where raw spatial imagery can be processed and fed directly into this analysis engine. The pipeline's modularity ensures that different labeling methods (manual, automated, or ML-based) can be used for Step 1, as long as the output conforms to the required data schema.

`[Raw Satellite Imagery] -> [STEP 1: Labeling] -> [**STEP 2: Analysis Prep**] -> [**STEP 3: Priority Scoring**] -> [**STEP 4: Simulation**] -> [Final Output]`

### Current Project Scope (Steps 2, 3, & 4)

Currently, this repository contains the robust implementation of **Steps 2, 3, and 4**.

It operates on the assumption that a standardized, pre-labeled land cover map (the output of Step 1) is provided as an input. This allows for a deep focus on the core optimization logic, scoring algorithms, and simulation engine.

### Step 1: Input Data Specification (The Data Contract)

For the 1-2-3-4 pipeline to be possible, the analysis engine requires the output of Step 1 to adhere to a specific **Data Schema**. This project's guidelines are based on the **official Land Cover Map classification system from the South Korean Ministry of Environment (환경부)**.

The required input polygon feature class must contain:

| Field Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `L3_CODE` | Text | Ministry of Environment's Level-3 (세분류) land cover code. | `211` (논), `311` (활엽수림), `112` (주거지역) |

As long as any labeling process (manual or automated) produces a shapefile or Gpkg with this standardized `L3_CODE` field, it can be directly consumed by this analysis engine.

---

### Step 2:  Analysis Preparation

* **Node Conversion:** Converts the input `L3_CODE` polygons into 'Digital Nodes'.
* **Data Modeling:** Assigns simulation-specific attributes (e.g., `NodeStatus`, `EvolvedCategory`) based on the standardized codes.

### Step 3:  Site Suitability Scoring

* **Resource Analysis (How many?):** Calculates the total potential for new smart farm modules using the **Land Conversion Efficiency (`CompressionFactor`)** model. This model quantifies the productive potential of existing greenbelt land to determine how many new smart farm modules can be built.

  $$\text{Number of New Modules} = \sum_{i=1}^{n} \frac{1}{\text{CompressionFactor}_i}$$

* **Candidate Analysis (Where?):** Ranks all replaceable urban nodes using the **Site Suitability Index (SSI)**. This index identifies where the new smart farms should be built by calculating a `ReplacePriority` score based on land value, centrality, and infrastructure proximity.

  $$\text{Site Suitability Index (SSI)} = (w_s \times S) + (w_c \times D_c^{-1}) + (w_i \times D_i^{-1})$$

### Step 4:  Phased Deployment Simulation

* **Iterative Execution:** Runs a multi-generational simulation (e.g., 2050, 2075, 2100) to model a realistic, gradual deployment.
* **Strategic Placement:** In each phase, the tool algorithmically deploys new modules to the highest-scoring sites (`SSI`) and removes low-scoring urban sites, modeling a data-driven optimization of the entire greenbelt.

---

## 3. Technologies Used

* **Core Language:** `Python`
* **Geospatial Analysis:** `ArcPy` (within ArcGIS Pro)
* **GIS Software:** `ArcGIS Pro`, `QGIS`

---

## 4. How to Use

1.  **Prerequisites:** An ArcGIS Pro environment with Python 3 and the `ArcPy` library.
2.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[ggooonn]/Green-Archipelago-Analysis-Tool.git
    ```
3.  **Configure:** Open `/scripts/config.py` and modify the file paths, layer names, and simulation parameters (`CompressionFactor`, weights, `L3_CODE` mappings, etc.).
4.  **Run Simulation:** Execute the main script from the ArcGIS Pro Python terminal.
    ```bash
    python scripts/main.py
    ```
5.  **Analyze Results:** The output feature classes for each phase will be saved in the configured Geodatabase, ready for spatial analysis and visualization.
