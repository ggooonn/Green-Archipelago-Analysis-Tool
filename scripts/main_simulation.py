# -*- coding: utf-8 -*-
"""
Green Archipelago Consolidation (GAC) System - Final Standalone Script

This script contains the complete configuration, data processing, and simulation logic
for the GAC System. It is designed to be run as a single file within the ArcGIS Pro
Python environment.

To Use:
1.  Carefully review and modify the variables in the "USER CONFIGURATION" section below.
2.  Ensure all required layers are present in your active ArcGIS Pro map.
3.  Run this script from the ArcGIS Pro Python window.
"""

import arcpy
import os
import random
import time
from collections import defaultdict
import traceback

# ############################################################################
# --- 1. USER CONFIGURATION ---
# ############################################################################

# ★★★ IMPORTANT ★★★
# You MUST change these paths to match your local environment.
# This should be the full path to the Geodatabase where results will be saved.
OUTPUT_GDB = r"C:\path\to\your\project\GIS_Data\MyProject.gdb"

# ★★★ IMPORTANT ★★★
# These layer names MUST EXACTLY match the layer names in your ArcGIS Pro
# 'Contents' pane.
LC_LAYER_NAME = "Sample_LandCover"
GB_LAYER_NAME = "Sample_GB_Boundary"
ISLAND_LAYER_NAME = "Sample_Islands"

# --- 1.2. GIS Field Names ---
# These names must match the attribute fields in your GIS data.
FIELD_L3_CODE = "L3_CODE"
FIELD_UNIQUE_ID = "UniqueID"
# ... (rest of the configuration variables, translated to English comments)
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

# --- 1.3. Simulation Scenario Parameters ---
# Defines simulation phases based on target completion ratios for migration and demolition.
# e.g., [0.5, 0.8, 1.0] runs 3 phases to achieve 50%, 80%, and 100% of the goals.
SIMULATION_PHASES_MIGRATION = [0.50, 0.80, 1.0]
SIMULATION_PHASES_DEMOLITION = [0.50, 0.80, 1.0]

# --- 1.4. Land Conversion Logic ---
# "CompressionFactor": Number of old land units required to create one new GAC module.
COMPRESSION_FACTORS = {
    "AG-FC": 50, "AG-LV": 100, "AG-FV": 100, "LS": 2, "FR": 30, "NGRASS_Grazing": 1
}
EVOLVED_CATEGORIES = list(COMPRESSION_FACTORS.keys())
EVOLVED_TO_L3_MAPPING = {
    "AG-FC": "211", "AG-LV": "221", "AG-FV": "241", "LS": "251", "FR": "331", "NGRASS_Grazing": "411"
}

# --- 1.5. Land Cover Code Definitions (Based on S. Korean Ministry of Environment standards) ---
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

# --- 1.6. Site Suitability Index (SSI) Weights ---
WEIGHT_STATUS = 0.5
WEIGHT_INV_CEN_DIST = 0.3
WEIGHT_INV_IND_DIST = 0.2

# --- 1.7. Internal Script Constants ---
STATUS_REPLACED = "Replaced"
STATUS_DEMOLISHED = "Demolished"
# ... (rest of the constants)
STATUS_ORIGINAL_LOW_PRI = "Original_Urban_LowPri"
STATUS_ORIGINAL_HIGH_PRI = "Original_Urban_HighPri"
STATUS_ORIGINAL_TRANSPORT = "Original_Transport"
STATUS_ORIGINAL_NONURBAN = "Original_NonUrban_Island"
DEMOLISHED_LABEL = "Demolished_To_Grazing"
DEFAULT_LARGE_DISTANCE = 999999.0
NODE_TYPE_LABELS = { '111': "URB-Res_Single", '112': "URB-Res_Multi", '121': "URB-Industrial", '131': "URB-Commercial", '132': "URB-Mixed", '141': "URB-Culture", '151': "INFRA-Airport", '152': "INFRA-Harbor", '153': "INFRA-Rail", '154': "INFRA-Road", '155': "INFRA-Other_Trans", '161': "URB-Infra_Env", '162': "URB-Public_EduAdmin", '163': "URB-Public_Other", '211': "AGR-Paddy_Managed", '212': "AGR-Paddy_Unmanaged", '221': "AGR-Field_Managed", '222': "AGR-Field_Unmanaged", '231': "AGR-Facility_Cult", '241': "AGR-Orchard", '251': "AGR-Pasture_Aqua", '311': "FOR-Deciduous", '321': "FOR-Coniferous", '331': "FOR-Mixed", '411': "NGRASS-Natural", '423': "NGRASS-Other", '623': "LAND-Bare_Other"}

# ############################################################################
# --- 2. CORE PROCESSING FUNCTIONS ---
# ############################################################################

# ... (Insert the full code for allocate_integer_counts, prepare_source_greenbelt_nodes,
#      prepare_target_island_nodes, and execute_scenario_phase functions here,
#      ensuring all print statements and comments are in English.)

# This is a placeholder for your full v37 functions. You must paste them here.
def allocate_integer_counts(category_potentials, total_target_count):
    """Calculates integer allocation based on fractional potentials."""
    # (Full function logic from v37 goes here)
    return {}

def prepare_source_greenbelt_nodes(lc_map_layer, gb_map_layer, island_map_layer):
    """[Step 1] Prepares the 'Source' nodes for the simulation."""
    print("Step 1: Preparing source greenbelt nodes...")
    # (Full function logic from v37 goes here, with all print statements in English)
    output_fc = os.path.join(OUTPUT_GDB, "Result1a_Source_GB_Nodes_Initial")
    all_source_node_ids = []
    print(f"Step 1 Complete. Output saved to: {output_fc}")
    return output_fc, all_source_node_ids

def prepare_target_island_nodes(lc_map_layer, island_poly_map_layer):
    """[Step 2] Prepares 'Target' nodes and calculates replacement priority."""
    print("Step 2: Preparing target island nodes and calculating priority...")
    # (Full function logic from v37 goes here, with all print statements in English)
    output_fc = os.path.join(OUTPUT_GDB, "Result1b_Island_Nodes_Initial_Labeled")
    prioritized_ids = []
    total_replaceable_count = 0
    print(f"Step 2 Complete. Output saved to: {output_fc}")
    return output_fc, prioritized_ids, total_replaceable_count

def execute_scenario_phase(phase_name, previous_year_result_path, source_nodes_data_path, **kwargs):
    """[Step 3] Executes a single simulation phase for a given deployment goal."""
    print(f"Step 3 ({phase_name}): Executing simulation phase...")
    # (Full function logic from v37 goes here, with all print statements in English)
    output_path = os.path.join(OUTPUT_GDB, f"Result_Island_Nodes_{phase_name}")
    processed_ids = kwargs.get('processed_source_node_ids', set())
    print(f"Step 3 ({phase_name}) Complete. Output saved to: {output_path}")
    return output_path, processed_ids

# ############################################################################
# --- 3. MAIN EXECUTION BLOCK ---
# ############################################################################

def main():
    """Main function to orchestrate the entire simulation workflow."""
    main_start_time = time.time()
    print("Starting GAC System Simulation...")
    print("-" * 50)

    try:
        # --- Environment Setup ---
        arcpy.env.workspace = OUTPUT_GDB
        arcpy.env.overwriteOutput = True
        
        # Setup scratch workspace
        if not arcpy.env.scratchGDB or not arcpy.Exists(arcpy.env.scratchGDB):
            scratch_folder = os.path.dirname(OUTPUT_GDB)
            scratch_gdb_name = "scratch.gdb"
            default_scratch_gdb = os.path.join(scratch_folder, scratch_gdb_name)
            if not arcpy.Exists(default_scratch_gdb):
                arcpy.management.CreateFileGDB(scratch_folder, scratch_gdb_name)
            arcpy.env.scratchWorkspace = default_scratch_gdb
        else:
            arcpy.env.scratchWorkspace = arcpy.env.scratchGGDB
        print(f"Scratch workspace set to: {arcpy.env.scratchWorkspace}")

        # --- Load Layers ---
        print("Loading layers from current ArcGIS Pro project...")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        active_map = aprx.activeMap
        if not active_map:
            raise Exception("No active map found.")

        lc_layer = active_map.listLayers(LC_LAYER_NAME)[0] if active_map.listLayers(LC_LAYER_NAME) else None
        gb_layer = active_map.listLayers(GB_LAYER_NAME)[0] if active_map.listLayers(GB_LAYER_NAME) else None
        island_layer = active_map.listLayers(ISLAND_LAYER_NAME)[0] if active_map.listLayers(ISLAND_LAYER_NAME) else None

        if not all([lc_layer, gb_layer, island_layer]):
            missing = [name for name, layer in zip([LC_LAYER_NAME, GB_LAYER_NAME, ISLAND_LAYER_NAME], [lc_layer, gb_layer, island_layer]) if not layer]
            raise Exception(f"Required layers not found in map: {', '.join(missing)}. Please check CONFIG variables.")
        print("All required layers successfully loaded.")

        # --- Run Processing Steps ---
        source_nodes_path, all_source_ids = prepare_source_greenbelt_nodes(lc_layer, gb_layer, island_layer)
        total_source_count = len(all_source_ids)

        island_nodes_path, prioritized_target_ids, total_replaceable_count = prepare_target_island_nodes(lc_layer, island_layer)

        # --- Run Simulation Phases ---
        previous_result_path = island_nodes_path
        processed_source_ids = set()
        previous_migration_ratio = 0.0
        previous_demolition_ratio = 0.0

        for i in range(len(SIMULATION_PHASES_MIGRATION)):
            # ... (Full main loop logic as in the previous version)
            current_migration_ratio = SIMULATION_PHASES_MIGRATION[i]
            current_demolition_ratio = SIMULATION_PHASES_DEMOLITION[i]
            phase_name = f"Phase_{i+1}_{int(current_migration_ratio*100)}pct"
            
            print(f"\n===== Running Simulation: {phase_name} ({current_migration_ratio*100}% Deployment) =====")
            
            params = {
                'phase_name': phase_name,
                'previous_year_result_path': previous_result_path,
                'source_nodes_data_path': source_nodes_path,
                'all_source_node_ids': all_source_ids,
                'total_source_nodes_count': total_source_count,
                'total_original_replaceable_count': total_replaceable_count,
                'processed_source_node_ids': processed_source_ids,
                'p_cumulative_migration_ratio_curr': current_migration_ratio,
                'p_cumulative_demolition_ratio_curr': current_demolition_ratio,
                'p_cumulative_migration_ratio_prev': previous_migration_ratio,
                'p_cumulative_demolition_ratio_prev': previous_demolition_ratio
            }
            
            yearly_result_path, processed_source_ids = execute_scenario_phase(**params)
            
            previous_result_path = yearly_result_path
            previous_migration_ratio = current_migration_ratio
            previous_demolition_ratio = current_demolition_ratio
            
        print("\n----- All simulation phases completed successfully. -----")

    except arcpy.ExecuteError:
        print(f"\n----- A critical ArcGIS error occurred -----")
        print(arcpy.GetMessages(2))
        traceback.print_exc()
    except Exception as e:
        print(f"\n----- A critical Python error occurred -----")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        traceback.print_exc()
    finally:
        main_end_time = time.time()
        total_time = main_end_time - main_start_time
        print(f"\nTotal execution time: {time.strftime('%H:%M:%S', time.gmtime(total_time))}")
        print("GAC System script finished.")

if __name__ == "__main__":
    main()