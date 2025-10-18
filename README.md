# Green-Archipelago-Analysis-Tool

## 1. Overview

This repository contains a GIS-based decision support tool for strategic smart farm placement within urban greenbelts. Faced with inefficiently managed greenbelt land, this tool provides a quantitative methodology to answer two critical questions:

Where are the optimal locations to replace underutilized urban parcels with high-efficiency smart farms?

How much productive value can be generated from the existing land resources?

The system analyzes geospatial data to model a long-term, phased deployment of smart farm modules, maximizing both spatial efficiency and agricultural output.

## 2. Core Methodology

The tool's logic is built upon two key analytical models derived from the project's code: the Land Conversion Efficiency model and the Site Suitability Index.

### 2.1. 토지 전환 효율 (Land Conversion Efficiency)

This model quantifies the productive potential of existing greenbelt land. It addresses the question: "How many new smart farm modules can we build?"

Each parcel of existing agricultural or forest land (Source Node) is assigned a CompressionFactor. This factor represents how many traditional land units are required to provide the resources for one modern, high-yield smart farm module. The total number of new modules that can be generated is calculated by the formula:

$$\text{Number of New Smart Farm Modules} = \sum_{i=1}^{n} \frac{1}{\text{CompressionFactor}_i}$$

Where:

n is the number of source land parcels being converted.

CompressionFactor is the land conversion ratio for each parcel i. A lower factor indicates higher efficiency (e.g., a fertile paddy field might have a lower factor than a sparse forest).

This calculation directly links the potential of the existing, low-density greenbelt to the creation of new, high-density agricultural infrastructure.

### 2.2. 입지 적합도 지수 (Site Suitability Index)

This model identifies the best locations for the newly generated smart farms. It answers the question: "Where should we build them?"

The tool calculates a ReplacePriority score for every replaceable urban parcel (Target Node) within the greenbelt's urban "islands". This score serves as a Site Suitability Index, with higher scores indicating more optimal locations. The formula is:

$$\text{Site Suitability Index (SSI)} = (w_s \times S) + (w_c \times D_c^{-1}) + (w_i \times D_i^{-1})$$

Where:

SSI: The ReplacePriority score for a parcel.

S: Status Score, representing the parcel's current urban value. Low-value parcels (e.g., dilapidated single-family homes) receive a higher score for replacement.

$D_c^{-1}$: Inverse Distance to Center, prioritizing locations near the area's logistical core for efficient distribution and access.

$D_i^{-1}$: Inverse Distance to Industry, prioritizing locations near existing industrial zones to leverage infrastructure, utilities, and labor pools.

$w_s, w_c, w_i$: Weights, adjustable parameters to align the simulation with specific strategic goals (e.g., prioritizing logistical efficiency over land cost).

## 3. System Architecture & Methodology

This tool is designed as the core analytical engine (Steps 2-4) within a larger, end-to-end geospatial data pipeline.



[Image of a data processing workflow diagram]


`[Raw Satellite Imagery] -> [STEP 1: Labeling] -> [**STEP 2: Analysis Prep**] -> [**STEP 3: Priority Scoring**] -> [**STEP 4: Simulation**] -> [Final Output]`

While this project focuses on the core optimization logic (Steps 2-4), it is designed to seamlessly integrate with a preceding imagery labeling module (Step 1).

---

### **Step 1: Spatial Imagery Labeling (Data Input Specification)**

This analytical engine assumes an input land cover map has been generated from raw spatial imagery (e.g., satellite or aerial photos). The tool is agnostic to the labeling method (manual or automated via Machine Learning), but it requires the input data to conform to a specific **Data Schema**.

The input must be a polygon feature class (e.g., `.gpkg` or `.shp`) with at least the following attribute field:

| Field Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `L3_CODE` | Text | A standardized land cover classification code. | `211`, `311`, `112` |

This modular design ensures that as long as the input data meets this simple schema, the core analysis can be run on data from any source.

---

### **Step 2: Analysis Preparation (Current Project Scope)**

Once the standardized land cover map is loaded, the tool begins its core process:
1.  **Node Conversion**: Converts each land parcel polygon into a 'Digital Node'.
2.  **Attribute Labeling**: Assigns simulation-specific labels to each node, such as `NodeStatus` and `EvolvedCategory`.

## 4. Technologies Used

Core Language: Python

Geospatial Analysis: ArcPy (within ArcGIS Pro)

GIS Software: ArcGIS Pro, QGIS

## 5. How to Use

Prerequisites: An ArcGIS Pro environment with Python 3 and the ArcPy library.

Clone the Repository:

git clone [https://github.com/](https://github.com/)[Your-Username]/Green-Archipelago-Analysis-Tool.git


Configure: Open /scripts/config.py and modify the file paths, layer names, and simulation parameters (CompressionFactor, weights, etc.).

Run Simulation: Execute the main script from the ArcGIS Pro Python terminal.

python scripts/main.py


Analyze Results: The output feature classes for each phase will be saved in the configured Geodatabase, ready for spatial analysis and visualization.
