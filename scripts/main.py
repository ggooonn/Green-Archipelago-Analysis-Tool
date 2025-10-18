# -*- coding: utf-8 -*-
"""
Green Archipelago Consolidation (GAC) 시스템의 메인 실행 스크립트

이 스크립트는 전체 시뮬레이션 워크플로우를 조율합니다.
1. config.py에서 설정 파라미터를 로드합니다.
2. processing.py의 데이터 처리 함수들을 순서대로 호출합니다.
3. 각 시뮬레이션 단계 간의 데이터 흐름을 관리합니다.
4. 진행 상황과 최종 결과를 콘솔에 출력합니다.

ArcGIS Pro의 Python 환경에서 이 스크립트를 실행하여 시뮬레이션을 시작합니다.
"""

import arcpy
import time
import traceback
from . import config
from . import processing

def main():
    """전체 시뮬레이션을 실행하는 메인 함수"""
    main_start_time = time.time()
    print("GAC 시스템 시뮬레이션을 시작합니다...")
    print("-" * 50)

    try:
        # --- 환경 설정 ---
        arcpy.env.workspace = config.OUTPUT_GDB
        arcpy.env.overwriteOutput = True

        print("현재 ArcGIS Pro 프로젝트 및 활성 Map 로드 중...")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        active_map = aprx.activeMap
        if not active_map:
            raise Exception("활성된 Map이 없습니다.")

        lc_layer = active_map.listLayers(config.LC_LAYER_NAME)[0]
        gb_layer = active_map.listLayers(config.GB_LAYER_NAME)[0]
        island_layer = active_map.listLayers(config.ISLAND_LAYER_NAME)[0]

        if not all([lc_layer, gb_layer, island_layer]):
            raise Exception("필수 레이어 중 일부를 Map에서 찾을 수 없습니다.")
        print("필수 Map 레이어 확인 완료.")

        # --- 단계 1: 자원(Source) 노드 준비 ---
        source_nodes_path, all_source_ids = processing.prepare_source_greenbelt_nodes(
            lc_layer, gb_layer, island_layer
        )

        # --- 단계 2: 대상(Target) 노드 준비 및 우선순위 계산 ---
        island_nodes_path, prioritized_target_ids, total_replaceable_count = processing.prepare_target_island_nodes(
            lc_layer, island_layer
        )

        # --- 단계 3: 시나리오별 시뮬레이션 실행 ---
        previous_result_path = island_nodes_path
        processed_source_ids = set()
        sorted_years = sorted(config.SCENARIO_PHASES.values())

        for year in sorted_years:
            print(f"\n===== 시나리오 실행 중: {year}년 =====")

            # execute_scenario_phase 함수에 필요한 모든 인자를 전달합니다.
            # (kwargs 대신 명시적으로 전달하는 것이 더 명확할 수 있습니다.)
            yearly_result_path, processed_source_ids = processing.execute_scenario_phase(
                year=year,
                previous_year_result_path=previous_result_path,
                source_nodes_data_path=source_nodes_path,
                all_source_node_ids=all_source_ids,
                processed_source_node_ids=processed_source_ids,
                # ... 기타 필요한 파라미터들 ...
            )
            previous_result_path = yearly_result_path # 올해의 결과가 내년의 입력이 됨

        print("\n----- 모든 시뮬레이션이 성공적으로 완료되었습니다. -----")

    except arcpy.ExecuteError:
        print(f"\n-----致命적인 ArcGIS 오류가 발생했습니다-----")
        print(arcpy.GetMessages(2))
        traceback.print_exc()
    except Exception as e:
        print(f"\n-----致命적인 Python 오류가 발생했습니다-----")
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