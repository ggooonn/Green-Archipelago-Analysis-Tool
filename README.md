# Green-Archipelago-Analysis-Tool (GAAT)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) ![ArcPy](https://img.shields.io/badge/ArcPy-ArcGIS%20Pro-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

> A GIS optimization tool that quantifies potential agricultural yield from greenbelt resources and determines optimal placement locations for equivalent smart farm facilities on brownfield sites using a custom Site Suitability Index (SSI).

---

## 1. Overview & The Challenge

This tool provides a quantitative methodology for the strategic deployment of smart farms within **South Korea's metropolitan greenbelts**. As urban areas expand, these greenbelts face increasing pressure, becoming fragmented "islands" of underutilized land. GAAT is designed to model a data-driven solution to this challenge by identifying optimal locations for high-efficiency agricultural facilities.

`![Image](https://github.com/user-attachments/assets/d6d8440c-3c9a-4697-b05f-6f863b6ad042)`
> *The challenge: Analyzing the fragmented and expanding urban "islands" within Siheung's greenbelt over time.*

---

## 2. Core Outputs & Visualizations

GAAT translates complex geospatial data into clear, actionable strategies. The following visuals demonstrate the key outputs using a sample district.

### 2.1. The "Why": Site Suitability Index (SSI) Distribution

The engine first identifies potential brownfield sites for redevelopment. It then calculates a **Site Suitability Index (SSI)** for each site based on factors like land value, centrality, and infrastructure proximity. This map visualizes the decision-making logic: **sites with higher scores (brighter areas) are prioritized for placement.**

> *Visualization of the Site Suitability Index. The algorithm prioritizes placing new facilities in the highest-scoring locations.*

### 2.2. The "How": Phased Deployment Simulation

GAAT simulates a gradual, phased deployment based on **production goals** (e.g., 50%, 80%, 100% of potential yield). This time-lapse demonstrates the strategic consolidation of production facilities over time, transforming the landscape according to the SSI logic.

`![Image](https://github.com/user-attachments/assets/a9657e1e-c05f-470f-adcf-005c74f35f66)`
> *Full simulation showing the phased deployment of new smart farm facilities onto prioritized brownfield sites.*

### 2.3. The "What": Demolition & Replacement Detail

This image provides a detailed before-and-after view of a specific area within the simulation, showing low-priority urban parcels being replaced by high-efficiency smart farm modules.

`![Image](https://github.com/user-attachments/assets/000c8ef6-6d7b-4fb2-a7ec-fb7ee7143442)``![Image](https://github.com/user-attachments/assets/a5691f6b-d515-4126-9011-5a14d66bc213)`
> *Detailed view: Initial state (left) and the final state after demolition and replacement (right).*

---

## 3. System Architecture & Methodology

GAAT is designed as the **Action Engine (Steps 2-4)** that operates on data classified by established **Step 1** processes (like ML-based `Crop Classification`). It answers the question: **"Given this land data, what is the optimal strategy for deploying new assets?"**

`[STEP 1: Classification/Labeling] -> [**STEP 2: Analysis Prep**] -> [**STEP 3: Scoring**] -> [**STEP 4: Simulation**]`

### Step 1: Input Data Specification (The Data Contract)

The engine ingests a polygon feature class adhering to the **South Korean Ministry of Environment's Land Cover Map** standards.

| Field Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `L3_CODE` | Text | Ministry of Environment's Level-3 (세분류) code. | `211` (논), `112` (주거지역) |

### Step 2:  Analysis Preparation

* **Node Conversion:** Converts input polygons into 'Digital Nodes'.
* **Data Modeling:** Assigns simulation-specific attributes (e.g., `NodeStatus`).

### Step 3:  Site Suitability Scoring

* **Resource Analysis (How many?):** Calculates the total potential for new modules using the **Land Conversion Efficiency (`CompressionFactor`)** model.
    $$ \text{Number of New Modules} = \sum_{i=1}^{n} \frac{1}{\text{CompressionFactor}_i} $$
* **Candidate Analysis (Where?):** Ranks replaceable urban nodes using the **Site Suitability Index (SSI)**.
    $$ \text{SSI} = (w_s \times S) + (w_c \times D_c^{-1}) + (w_i \times D_i^{-1}) $$

### Step 4:  Phased Deployment Simulation

The simulation runs on **data-driven production goals** (e.g., 50%, 80%, 100%) defined in the configuration file, providing a flexible tool for strategic planning.

---

## 4. Technologies Used

* **Core Language:** `Python`
* **Geospatial Analysis:** `ArcPy` (within ArcGIS Pro)
* **GIS Software:** `ArcGIS Pro`, `QGIS`

---

## 5. How to Use & Code Structure

### Code Structure

This repository maintains two versions of the script:

* **/scripts (Modular Version):** Split into `config.py`, `processing.py`, and `main.py` for easier development and debugging. *(Note: This version might require adjustments to run directly in the ArcGIS Pro Python window due to import methods.)*
* **/standalone/main_simulation.py (Standalone Version):** A single, consolidated script for stable execution directly within the ArcGIS Pro Python window. **Use this version for running the simulation.**

### Running the Simulation

1.  **Prerequisites:** An ArcGIS Pro environment with Python 3.
2.  **Clone Repository:**
    ```bash
    git clone [https://github.com/ggooonn/Green-Archipelago-Analysis-Tool.git](https://github.com/ggooonn/Green-Archipelago-Analysis-Tool.git)
    ```
3.  **Prepare Data:** Ensure the sample data (`/data/GAAT_Sample_Data.gpkg`) layers (`Sample_LandCover`, `Sample_GB_Boundary`, `Sample_Islands`) are loaded into your active ArcGIS Pro map.
4.  **Configure Script:** Open the standalone script (`/standalone/main_simulation.py`) in a text editor. Carefully review and modify the paths and layer names in the **USER CONFIGURATION** section at the top to match your environment and the loaded layer names.
5.  **Run Script:** Copy the entire content of the configured `/standalone/main_simulation.py` script and paste it into the ArcGIS Pro Python window, then press Enter to execute. Alternatively, save the modified script and run it from the Python window using `exec(open(r'C:\path\to\your\script\main_simulation.py').read())`.

---

## 6. Data Source

The sample dataset (`/data/GAAT_Sample_Data.gpkg`) is derived from the official **Land Cover Map (2020)** provided by the **Ministry of Environment, Republic of Korea (환경부)**. This original dataset is publicly available under the **Korea Open Government License (KOGL) Type 1**, permitting use and modification with proper attribution.
