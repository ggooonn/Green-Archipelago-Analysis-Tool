#Green-Archipelago-Analysis-Tool

##1. Overview

This repository contains a GIS-based decision support tool for strategic smart farm placement within urban greenbelts. Faced with inefficiently managed greenbelt land, this tool provides a quantitative methodology to answer two critical questions:

Where are the optimal locations to replace underutilized urban parcels with high-efficiency smart farms?

How much productive value can be generated from the existing land resources?

The system analyzes geospatial data to model a long-term, phased deployment of smart farm modules, maximizing both spatial efficiency and agricultural output.

##2. Core Methodology

The tool's logic is built upon two key analytical models derived from the project's code: the Land Conversion Efficiency model and the Site Suitability Index.

###2.1. 토지 전환 효율 (Land Conversion Efficiency)

This model quantifies the productive potential of existing greenbelt land. It addresses the question: "How many new smart farm modules can we build?"

Each parcel of existing agricultural or forest land (Source Node) is assigned a CompressionFactor. This factor represents how many traditional land units are required to provide the resources for one modern, high-yield smart farm module. The total number of new modules that can be generated is calculated by the formula:

$$\text{Number of New Smart Farm Modules} = \sum_{i=1}^{n} \frac{1}{\text{CompressionFactor}_i}$$

Where:

n is the number of source land parcels being converted.

CompressionFactor is the land conversion ratio for each parcel i. A lower factor indicates higher efficiency (e.g., a fertile paddy field might have a lower factor than a sparse forest).

This calculation directly links the potential of the existing, low-density greenbelt to the creation of new, high-density agricultural infrastructure.

###2.2. 입지 적합도 지수 (Site Suitability Index)

This model identifies the best locations for the newly generated smart farms. It answers the question: "Where should we build them?"

The tool calculates a ReplacePriority score for every replaceable urban parcel (Target Node) within the greenbelt's urban "islands". This score serves as a Site Suitability Index, with higher scores indicating more optimal locations. The formula is:

$$\text{Site Suitability Index (SSI)} = (w_s \times S) + (w_c \times D_c^{-1}) + (w_i \times D_i^{-1})$$

Where:

SSI: The ReplacePriority score for a parcel.

S: Status Score, representing the parcel's current urban value. Low-value parcels (e.g., dilapidated single-family homes) receive a higher score for replacement.

$D_c^{-1}$: Inverse Distance to Center, prioritizing locations near the area's logistical core for efficient distribution and access.

$D_i^{-1}$: Inverse Distance to Industry, prioritizing locations near existing industrial zones to leverage infrastructure, utilities, and labor pools.

$w_s, w_c, w_i$: Weights, adjustable parameters to align the simulation with specific strategic goals (e.g., prioritizing logistical efficiency over land cost).

##3. Simulation Workflow

The tool executes a step-by-step simulation to model the deployment of smart farms over time.

Step 1: Resource Analysis (자원 분석)
The tool analyzes all non-urban parcels within the greenbelt to calculate the total potential for new smart farm modules based on the Land Conversion Efficiency model.

Step 2: Candidate Site Analysis (후보지 분석)
Simultaneously, it analyzes all urban parcels within the designated "islands" and calculates a Site Suitability Index (SSI) for each, creating a ranked list of optimal deployment locations.

Step 3: Phased Deployment Simulation (단계별 배치 시뮬레이션)
The simulation runs in phases (e.g., for years 2050, 2075, 2100). In each phase:

A portion of the total smart farm potential is "unlocked".

The tool places these new smart farm modules on the available sites with the highest SSI scores.

To make room and consolidate land use, urban sites with the lowest SSI scores are systematically demolished.

This workflow ensures that the deployment is not random, but a strategic process that continuously optimizes for the best available locations.

##4. Technologies Used

Core Language: Python

Geospatial Analysis: ArcPy (within ArcGIS Pro)

GIS Software: ArcGIS Pro, QGIS

##5. How to Use

Prerequisites: An ArcGIS Pro environment with Python 3 and the ArcPy library.

Clone the Repository:

git clone [https://github.com/](https://github.com/)[Your-Username]/Green-Archipelago-Analysis-Tool.git


Configure: Open /scripts/config.py and modify the file paths, layer names, and simulation parameters (CompressionFactor, weights, etc.).

Run Simulation: Execute the main script from the ArcGIS Pro Python terminal.

python scripts/main.py


Analyze Results: The output feature classes for each phase will be saved in the configured Geodatabase, ready for spatial analysis and visualization.
