# -*- coding: utf-8 -*-
"""
Configuration File for the GAC System Prototype

This file centralizes all user-configurable parameters for the simulation.
By modifying these variables, users can run different scenarios without
touching the core processing logic.
"""

# --- 1. ArcGIS Pro Project & Geodatabase Settings ---
# Full path to the output Geodatabase (GDB) where results will be stored.
OUTPUT_GDB = r"C:\path\to\your\project\GIS_Data\MyProject.gdb"

# Layer names as they appear in the ArcGIS Pro 'Contents' pane.
LC_LAYER_NAME = "Sample_LandCover"
GB_LAYER_NAME = "Sample_GB_Boundary"
ISLAND_LAYER_NAME = "Sample_Islands"

# --- 2. GIS Field Names ---
FIELD_L3_CODE = "L3_CODE"
FIELD_UNIQUE_ID = "UniqueID"
FIELD_NODE_STATUS = "NodeStatus"
FIELD_NODE_TYPE_LABEL = "NodeTypeLabel"
FIELD_ORIG_SOURCE_CODE = "OrigSourceL3Code"
FIELD_EVOLVED_CATEGORY = "EvolvedCategory"
FIELD_COMPRESSION_FACTOR = "CompressionFactor"
FIELD_REPLACEMENT_PRIORITY = "ReplacePriority"
FIELD_NEAR_CENTROID_DIST = "NearCenDist"
FIELD_NEAR_INDUSTRIAL_DIST = "NearIndDist"
FIELD_ISLAND_ID = "FinalLabel_ZoneSize"
FIELD_ISLAND_ID_IN_POLYGONS = "FinalLabel_ZoneSize"
FIELD_ORIG_POLY_FID = "ORIG_FID"
FIELD_IS_GRAZING = "IsGrazing"
FIELD_GRAZING_TYPE = "GrazingType"

# --- 3. Simulation Scenario Parameters ---
SIMULATION_PHASES_MIGRATION = [0.50, 0.80, 1.0]
SIMULATION_PHASES_DEMOLITION = [0.50, 0.80, 1.0]

# --- 4. Land Conversion Logic ---
COMPRESSION_FACTORS = {
    "AG-FC": 50, "AG-LV": 100, "AG-FV": 100, "LS": 2, "FR": 30, "NGRASS_Grazing": 1
}
EVOLVED_CATEGORIES = list(COMPRESSION_FACTORS.keys())
EVOLVED_TO_L3_MAPPING = {
    "AG-FC": "211", "AG-LV": "221", "AG-FV": "241", "LS": "251", "FR": "331", "NGRASS_Grazing": "411"
}

# --- 5. Land Cover Code Definitions (S. Korean Ministry of Environment) ---
SOURCE_L3_CODES = ['211', '212', '221', '222', '231', '241', '251', '311', '321', '331', '411', '423', '623']
LOW_PRIORITY_URBAN_CODES = ['111', '112', '141', '161', '162', '163']
HIGH_PRIORITY_URBAN_CODES = ['121', '131', '132']
REPLACEABLE_URBAN_L3_CODES = LOW_PRIORITY_URBAN_CODES + HIGH_PRIORITY_URBAN_CODES
INDUSTRIAL_L3_CODES = ['121']
TRANSPORT_L3_CODES = ['151', '152', '153', '154', '155']
FOREST_L3_CODES = ['311', '321', '331']
BASE_GRAZING_CODES = ['251', '411', '423', '623']
DEMOLISHED_L3_CODE = "411"
GRAZING_L3_CODES = list(set(BASE_GRAZING_CODES + [EVOLVED_TO_L3_MAPPING.get("LS"), EVOLVED_TO_L3_MAPPING.get("NGRASS_Grazing"), DEMOLISHED_L3_CODE]))
GRAZING_L3_CODES = [code for code in GRAZING_L3_CODES if code is not None]

# --- 6. Site Suitability Index (SSI) Weights ---
WEIGHT_STATUS = 0.5
WEIGHT_INV_CEN_DIST = 0.3
WEIGHT_INV_IND_DIST = 0.2

# --- 7. Internal Script Constants ---
STATUS_REPLACED = "Replaced"
STATUS_DEMOLISHED = "Demolished"
STATUS_ORIGINAL_LOW_PRI = "Original_Urban_LowPri"
STATUS_ORIGINAL_HIGH_PRI = "Original_Urban_HighPri"
STATUS_ORIGINAL_TRANSPORT = "Original_Transport"
STATUS_ORIGINAL_NONURBAN = "Original_NonUrban_Island"
DEMOLISHED_LABEL = "Demolished_To_Grazing"
DEFAULT_LARGE_DISTANCE = 999999.0
NODE_TYPE_LABELS = { '111': "URB-Res_Single", '112': "URB-Res_Multi", '121': "URB-Industrial", '131': "URB-Commercial", '132': "URB-Mixed", '141': "URB-Culture", '151': "INFRA-Airport", '152': "INFRA-Harbor", '153': "INFRA-Rail", '154': "INFRA-Road", '155': "INFRA-Other_Trans", '161': "URB-Infra_Env", '162': "URB-Public_EduAdmin", '163': "URB-Public_Other", '211': "AGR-Paddy_Managed", '212': "AGR-Paddy_Unmanaged", '221': "AGR-Field_Managed", '222': "AGR-Field_Unmanaged", '231': "AGR-Facility_Cult", '241': "AGR-Orchard", '251': "AGR-Pasture_Aqua", '311': "FOR-Deciduous", '321': "FOR-Coniferous", '331': "FOR-Mixed", '411': "NGRASS-Natural", '423': "NGRASS-Other", '623': "LAND-Bare_Other"}

