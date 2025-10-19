# Green-Archipelago-Analysis-Tool (GAAT)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) ![ArcPy](https://img.shields.io/badge/ArcPy-ArcGIS%20Pro-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## 1. Overview 

The Green-Archipelago-Analysis-Tool (GAAT) is a GIS-based decision support tool for the **strategic placement of smart farms within South Korea's metropolitan greenbelts**. As urban areas expand, these greenbelts face increasing pressure, becoming fragmented "islands" of underutilized land. GAAT is designed to model a data-driven solution to this challenge.

![Image](https://github.com/user-attachments/assets/d6d8440c-3c9a-4697-b05f-6f863b6ad042)
> *The challenge: Analyzing the fragmented and expanding urban "islands" within Siheung's greenbelt over time.*

GAAT addresses two critical questions:
1.  **Where** are the optimal locations to replace inefficient urban parcels with productive facilities?
2.  **How much** agricultural value can be generated from existing greenbelt resources?

---

## 2. How to Use 

This tool is designed to run as a standalone script within the ArcGIS Pro Python environment.

1.  **Prerequisites:** An ArcGIS Pro environment with Python 3.
2.  **Download Script:** Use the `main_simulation.py` script located in the `/scripts` folder.
3.  **Prepare Data:** Ensure the required data layers (e.g., from `/data/GAAT_Sample_Data.gpkg`) are loaded into your active ArcGIS Pro map.
4.  **Configure Script:** Open `main_simulation.py` in a text editor. Carefully review and modify the paths and layer names in the **USER CONFIGURATION** section at the top to match your environment.
5.  **Run Script:** Copy the entire configured script content, paste it into the ArcGIS Pro Python window, and press Enter to execute.

---

## 3. System Architecture & Methodology 

GAAT functions as the **Action Engine (Steps 2-4)** operating on data classified by established **Step 1** processes (like ML-based `Crop Classification`).

`[STEP 1: Classification/Labeling] -> [STEP 2: Analysis Prep] -> [STEP 3: Scoring] -> [STEP 4: Simulation]`

![Image](https://github.com/user-attachments/assets/a9657e1e-c05f-470f-adcf-005c74f35f66)
> *Core Output: Phased deployment simulation based on production goals (e.g., 50%, 80%, 100%).*

### Step 1: Input Data Specification (Data Contract)
The engine ingests a polygon feature class adhering to the **South Korean Ministry of Environment's Land Cover Map** standards.

| Field Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `L3_CODE` | Text | Ministry of Environment's Level-3 (세분류) code. | `211` (논), `112` (주거지역) |

### Step 2: Analysis Preparation
* **Node Conversion:** Converts input polygons into 'Digital Nodes'.
* **Data Modeling:** Assigns simulation-specific attributes (e.g., `NodeStatus`).

### Step 3: Site Suitability Scoring (SSI)

* **Resource Analysis (How many?):** Calculates the total potential for new modules using the **Land Conversion Efficiency (`CompressionFactor`)** model.

$$
\text{Number of New Modules} = \sum_{i=1}^{n} \frac{1}{\text{CompressionFactor}_{i}}
$$

* **Candidate Analysis (Where?):** Ranks replaceable urban nodes using the **Site Suitability Index (SSI)**. The formula breaks down how the score is calculated, balancing land status, centrality, and infrastructure proximity with user-defined weights.

$$
\text{SSI} = (w_{\text{status}} \times \text{Score}_{\text{status}}) + (w_{\text{center}} \times \text{Score}_{\text{center}}) + (w_{\text{industry}} \times \text{Score}_{\text{industry}})
$$

*Where:*
$w$: User-defined weights from the configuration file (`WEIGHT_STATUS`, `WEIGHT_INV_CEN_DIST`, `WEIGHT_INV_IND_DIST`).

$\text{Score}_{\text{status}}$: A score based on the land's urban classification (High vs. Low priority).

$\text{Score}_{\text{center}}$: A normalized score based on the inverse distance to the island's center ($D_{c}^{-1}$).

$\text{Score}_{\text{industry}}$: A normalized score based on the inverse distance to the nearest industrial area ($D_{i}^{-1}$).

  
### Algorithmic Validation: Distance vs. Priority Score
The following charts analyze the relationship between the calculated SSI (`ReplacePriority`) and key distance factors. The low R² values suggest that while distance is a component, the priority score is influenced by a combination of factors, preventing simple distance-based bias.

<img width="1489" height="341" alt="Image" src="https://github.com/user-attachments/assets/81f1ae0a-4cb8-422d-9a15-6621cbb5034b" />
> *SSI vs. Distance from Island Center (R² ≈ 0.08)*

<img width="1489" height="341" alt="Image" src="https://github.com/user-attachments/assets/4dca4884-decd-4e45-8324-3801998f88ba" />
> *SSI vs. Distance from Industrial Area (R² ≈ 0.13)*

### Step 4: Phased Deployment Simulation
The simulation runs iteratively based on **data-driven production goals** (e.g., 50%, 80%, 100%), strategically placing new modules and removing low-scoring urban sites.

---

## 4. Visual Output Example 

**Demolition & Replacement Detail:**
This image provides a detailed before-and-after view of a specific area, showing low-priority urban parcels being replaced by high-efficiency smart farm modules.

![Image](https://github.com/user-attachments/assets/000c8ef6-6d7b-4fb2-a7ec-fb7ee7143442) ![Image](https://github.com/user-attachments/assets/a5691f6b-d515-4126-9011-5a14d66bc213)

> *Detailed view: Initial state (up) vs. final state after simulation (down).*

---

## 5. Technologies Used 

* **Core Language:** `Python`
* **Geospatial Analysis:** `ArcPy` (within ArcGIS Pro)
* **GIS Software:** `ArcGIS Pro`, `QGIS`

---

## 6. Data Source 

The sample dataset (`/data/GAAT_Sample_Data.gpkg`) is derived from the official **Land Cover Map (2020)** provided by the **Ministry of Environment, Republic of Korea (환경부)** (KOGL Type 1 license).

---

## 7. Further Work / Notes 

* **Integrate Step 1:** Future development could involve adding a module for automated land cover classification (Step 1) using Machine Learning directly from satellite imagery to create a full end-to-end pipeline.
* **Weight Tuning:** The low R² values in the validation charts suggest the current SSI weights (`w_s`, `w_c`, `w_i`) create a balanced score. However, further analysis and tuning based on specific policy goals could refine the model's performance and fairness characteristics.
* **Code Structure:** The modular code in the `/scripts` folder (`config.py`, `processing.py`, `main.py`) is intended for development. Further debugging is planned post-submission. The `main_simulation.py` script is a consolidated version optimized for direct execution.
