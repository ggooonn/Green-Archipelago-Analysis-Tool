# -*- coding: utf-8 -*-
"""
Green Archipelago Consolidation (GAC) 시스템의 메인 실행 스크립트
"""

import arcpy
import os
import time
import traceback
import config
import processing

def main():
    """전체 시뮬레이션을 실행하는 메인 함수"""
    main_start_time = time.time()
    print("GAC 시스템 시뮬레이션을 시작합니다...")
    print("-" * 50)

    try:
        # --- 환경 설정 ---
        arcpy.env.workspace = config.OUTPUT_GDB
        arcpy.env.overwriteOutput = True
        
        # 스크래치 GDB 설정 (v37 원본 로직)
        if not arcpy.env.scratchGDB or not arcpy.Exists(arcpy.env.scratchGDB):
            scratch_folder = os.path.dirname(config.OUTPUT_GDB); scratch_gdb_name = "scratch.gdb"; default_scratch_gdb = os.path.join(scratch_folder, scratch_gdb_name)
            print(f"스크래치 GDB 설정/생성: {default_scratch_gdb}");
            if not arcpy.Exists(default_scratch_gdb):
                try: arcpy.management.CreateFileGDB(scratch_folder, scratch_gdb_name); print("스크래치 GDB 생성됨.")
                except Exception as e: print(f"스크래치 GDB 생성 실패: {e}"); default_scratch_gdb = arcpy.env.scratchGDB
            arcpy.env.scratchWorkspace = default_scratch_gdb
        else: arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
        print(f"임시 작업 공간: {arcpy.env.scratchWorkspace}")


        print("현재 ArcGIS Pro 프로젝트 및 활성 Map 로드 중...")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        active_map = aprx.activeMap
        if not active_map:
            raise Exception("활성된 Map이 없습니다.")

        # [수정됨] config 파일에서 레이어 이름을 가져와 로드합니다.
        lc_layer = active_map.listLayers(config.LC_LAYER_NAME)[0] if active_map.listLayers(config.LC_LAYER_NAME) else None
        gb_layer = active_map.listLayers(config.GB_LAYER_NAME)[0] if active_map.listLayers(config.GB_LAYER_NAME) else None
        island_layer = active_map.listLayers(config.ISLAND_LAYER_NAME)[0] if active_map.listLayers(config.ISLAND_LAYER_NAME) else None

        if not all([lc_layer, gb_layer, island_layer]):
            missing = [name for name, layer in zip([config.LC_LAYER_NAME, config.GB_LAYER_NAME, config.ISLAND_LAYER_NAME], [lc_layer, gb_layer, island_layer]) if not layer]
            raise Exception(f"필수 레이어를 Map에서 찾을 수 없습니다: {', '.join(missing)}. config.py의 레이어 이름을 확인하세요.")
        print("필수 Map 레이어 확인 완료.")

        # --- 단계 1 & 2 실행 ---
        source_nodes_path, all_source_ids = processing.prepare_source_greenbelt_nodes(lc_layer, gb_layer, island_layer)
        total_source_count = len(all_source_ids)
        if total_source_count == 0:
            print("경고: 단계 1 결과 유효한 원본 노드가 없습니다. 시뮬레이션이 '대체'를 수행하지 않을 수 있습니다.")

        island_nodes_path, prioritized_target_ids, total_replaceable_count = processing.prepare_target_island_nodes(lc_layer, island_layer)
        if total_replaceable_count == 0:
             print("경고: 단계 2 결과 대체 가능한 도시 노드가 없습니다. 시뮬레이션이 '철거' 또는 '대체'를 수행하지 않을 수 있습니다.")

        # --- 단계 3: 시나리오별 시뮬레이션 실행 ---
        previous_result_path = island_nodes_path
        processed_source_ids = set()
        previous_migration_ratio = 0.0
        previous_demolition_ratio = 0.0

        for i in range(len(config.SIMULATION_PHASES_MIGRATION)):
            current_migration_ratio = config.SIMULATION_PHASES_MIGRATION[i]
            current_demolition_ratio = config.SIMULATION_PHASES_DEMOLITION[i]
            phase_name = f"Phase_{i+1}_{int(current_migration_ratio*100)}pct"
            
            print(f"\n===== 시나리오 실행 중: {phase_name} ({current_migration_ratio*100}% 배치) =====")
            
            # processing 함수에 필요한 모든 파라미터를 딕셔너리로 묶어서 전달
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
            
            yearly_result_path, processed_source_ids = processing.execute_scenario_phase(**params)
            
            # 다음 루프를 위해 현재 결과 경로와 비율을 저장
            previous_result_path = yearly_result_path
            previous_migration_ratio = current_migration_ratio
            previous_demolition_ratio = current_demolition_ratio

        print("\n----- 모든 시뮬레이션이 성공적으로 완료되었습니다. -----")
        
        # (v37의 '섬 외부 그린벨트 내 목축 소스 노드 추출' 로직 추가)
        print("\n--- 섬 외부 그린벨트 내 목축 소스 노드 추출 중 ---")
        outer_grazing_source_nodes_fc = os.path.join(config.OUTPUT_GDB, "Result_Outer_Grazing_Source_Nodes")
        outer_grazing_candidate_categories = [cat for cat in config.EVOLVED_CATEGORIES if cat == "LS" or cat == "NGRASS_Grazing"]
        if outer_grazing_candidate_categories:
            quoted_grazing_evolved = [f"'{cat}'" for cat in outer_grazing_candidate_categories]
            where_outer_grazing = f"{config.FIELD_EVOLVED_CATEGORY} IN ({','.join(quoted_grazing_evolved)})"
            if arcpy.Exists(source_nodes_path):
                try:
                    if arcpy.Exists(outer_grazing_source_nodes_fc): arcpy.management.Delete(outer_grazing_source_nodes_fc)
                    arcpy.Select_analysis(source_nodes_path, outer_grazing_source_nodes_fc, where_outer_grazing)
                    print(f"  섬 외부 목축 소스 노드 저장: {outer_grazing_source_nodes_fc} ({arcpy.management.GetCount(outer_grazing_source_nodes_fc)}개)")
                except Exception as e_outer_grazing: print(f"  오류: 섬 외부 목축 소스 노드 추출 실패 - {e_outer_grazing}")
            else: print(f"  경고: 원본 소스 노드 파일({source_nodes_path})이 없어 섬 외부 목축 소스 추출 불가.")
        else: print("  경고: evolved_categories 목록에 목축 관련 유형(LS, NGRASS_Grazing)이 정의되지 않아 섬 외부 목축 소스 추출 불가.")


    except arcpy.ExecuteError:
        print(f"\n----- 치명적인 ArcGIS 오류가 발생했습니다 -----")
        print(arcpy.GetMessages(2))
        traceback.print_exc()
    except Exception as e:
        print(f"\n----- 치명적인 Python 오류가 발생했습니다 -----")
        print(f"오류 유형: {type(e).__name__}")
        print(f"오류 메시지: {e}")
        traceback.print_exc()
    finally:
        main_end_time = time.time()
        total_time = main_end_time - main_start_time
        print(f"\n총 실행 시간: {time.strftime('%H:%M:%S', time.gmtime(total_time))}")
        print("GAC 시스템 스크립트가 종료되었습니다.")

if __name__ == "__main__":
    main()