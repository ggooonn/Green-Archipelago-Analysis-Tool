# -*- coding: utf-8 -*-
"""
GAC System Prototype의 핵심 데이터 처리 및 분석 모듈

이 파일은 config.py에서 정의된 설정을 바탕으로 GIS 데이터를 처리, 분석, 시뮬레이션하는
핵심 함수들을 포함합니다. 각 함수는 전체 워크플로우의 특정 단계를 책임집니다.
"""

import arcpy
import os
import random
import time
from collections import defaultdict
import traceback
from . import config  # config.py 파일에서 설정 변수들을 가져옴

# allocate_integer_counts 함수는 원본 코드와 동일하게 여기에 위치시킵니다.
def allocate_integer_counts(category_potentials, total_target_count):
    # ... (원본 코드의 allocate_integer_counts 함수 내용 전체를 여기에 붙여넣기) ...
    """Calculates integer allocation based on fractional potentials."""
    integer_counts = {cat: 0 for cat in category_potentials}; remainders = {}; current_total = 0; potential_sum = sum(category_potentials.values());
    if potential_sum <= 1e-9: print("  경고: 총 진화 잠재력이 0."); return integer_counts
    total_target_count = int(round(total_target_count))
    if total_target_count == 0: return integer_counts
    for category, potential in category_potentials.items():
        if potential_sum > 1e-9: scaled_potential = potential * (total_target_count / potential_sum)
        else: scaled_potential = 0
        integer_part = int(scaled_potential); remainder = scaled_potential - integer_part; integer_counts[category] = integer_part; remainders[category] = remainder; current_total += integer_part
    remaining_to_allocate = total_target_count - current_total; sorted_remainders = sorted(remainders.items(), key=lambda item: item[1], reverse=True)
    for i in range(remaining_to_allocate):
        if i < len(sorted_remainders): integer_counts[sorted_remainders[i][0]] += 1
        else: print(f"Warning: Allocation shortfall during remainder distribution."); break
    final_sum = sum(integer_counts.values())
    if final_sum != total_target_count:
        print(f"Warning: Allocation mismatch after remainder ({final_sum} vs {total_target_count}). Adjusting...")
        diff = total_target_count - final_sum
        if diff > 0:
            indices = list(range(len(sorted_remainders))); random.shuffle(indices); add_count = 0
            while add_count < diff and indices: idx = indices.pop(0); cat_to_add = sorted_remainders[idx][0]; integer_counts[cat_to_add] += 1; add_count += 1
            while add_count < diff: cat_to_add = random.choice(list(integer_counts.keys())); integer_counts[cat_to_add] += 1; add_count += 1
        elif diff < 0:
            sorted_remainders_asc = sorted(remainders.items(), key=lambda item: item[1]); indices = list(range(len(sorted_remainders_asc))); random.shuffle(indices)
            remove_count = 0; processed_indices = set()
            while remove_count < abs(diff) and len(processed_indices) < len(indices):
                found_idx_to_process = -1
                for idx in indices:
                    if idx not in processed_indices: found_idx_to_process = idx; break
                if found_idx_to_process == -1: break
                cat_to_remove = sorted_remainders_asc[found_idx_to_process][0]; processed_indices.add(found_idx_to_process)
                if integer_counts[cat_to_remove] > 0: integer_counts[cat_to_remove] -= 1; remove_count += 1
            while remove_count < abs(diff):
                possible_cats = [c for c, v in integer_counts.items() if v > 0]
                if not possible_cats: break
                cat_to_remove = random.choice(possible_cats); integer_counts[cat_to_remove] -= 1; remove_count += 1
        final_sum = sum(integer_counts.values())
        if final_sum != total_target_count: print(f"ERROR: Adjustment failed! Final sum still {final_sum}")
    return integer_counts


def prepare_source_greenbelt_nodes(lc_map_layer, gb_map_layer, island_map_layer):
    """
    [단계 1] 시뮬레이션을 위한 '자원(Source)' 노드를 준비합니다.

    (Why) 이 함수가 필요한 이유:
    토지 전환의 '공급' 측면을 설정하는 첫 번째 단계입니다. 그린벨트 내에서
    고효율 'GAC 모듈'로 전환될 수 있는 모든 비도시 지역을 식별하고 정량화합니다.

    (Logic) 핵심 로직:
    1. 그린벨트 경계 내, 도시 '섬' 외부에 있는 모든 토지 피복 폴리곤을 선택합니다.
    2. 농경지, 산림 등 관련 유형만 남도록 필터링합니다.
    3. 각 폴리곤을 대표점('디지털 노드')으로 변환합니다.
    4. 원본 토지피복코드(L3_CODE)에 따라 'EvolvedCategory'를 할당합니다.
    5. config 파일의 'CompressionFactor' 값을 각 노드에 할당하여,
       신규 모듈 생성 잠재력을 정의합니다.

    반환값:
        tuple: (생성된 피처 클래스 경로, 모든 자원 노드의 고유 ID 리스트)
    """
    print("단계 1: 원본 그린벨트 노드 준비 시작...")
    # ... (원본 코드의 prepare_source_greenbelt_nodes 함수 내용 전체를 여기에 붙여넣기) ...
    # 중요: 함수 내부의 모든 설정 변수 이름을 config.변수명 으로 변경해야 합니다.
    # 예: output_gdb -> config.OUTPUT_GDB
    #     land_cover_code_field -> config.FIELD_L3_CODE
    #     compression_factors -> config.COMPRESSION_FACTORS
    pass # 실제 코드는 여기에 위치합니다


def prepare_target_island_nodes(lc_map_layer, island_poly_map_layer):
    """
    [단계 2] '대상(Target)' 노드를 준비하고 대체 우선순위를 계산합니다.

    (Why) 이 함수가 필요한 이유:
    토지 전환의 '수요' 측면을 설정합니다. 철거 및 대체 후보가 되는 모든
    도시 지역을 식별하고, 시뮬레이션이 논리적 결정을 내릴 수 있도록
    각 지역에 대한 우선순위 점수를 계산합니다.

    (Logic) 핵심 로직:
    1. '섬' 경계 내의 모든 토지 피복 폴리곤을 선택하여 '디지털 노드'로 변환합니다.
    2. 각 노드를 도시 유형(저밀도 주거, 상업 등)에 따라 분류합니다.
    3. 각 섬별로, 대체 가능한 모든 도시 노드에 대해 핵심 거리 값들을 계산합니다.
       (섬의 중심점까지의 거리, 가장 가까운 공업 지역까지의 거리)
    4. config 파일에 정의된 가중치를 사용하여 정규화된 'ReplacePriority'
       (입지 적합도 지수)를 계산합니다. 점수가 높을수록 신규 모듈에 더 적합한 위치입니다.

    반환값:
        tuple: (우선순위가 계산된 피처 클래스 경로, 우선순위 순으로 정렬된 ID 리스트, 총 대체 가능 노드 수)
    """
    print("단계 2: 대체 대상 섬 노드 준비 및 우선순위 계산 시작...")
    # ... (원본 코드의 prepare_target_island_nodes_no_sa 함수 내용 전체를 여기에 붙여넣기) ...
    # config.변수명 규칙은 동일하게 적용합니다.
    pass # 실제 코드는 여기에 위치합니다


def execute_scenario_phase(year, previous_year_result_path, source_nodes_data_path, **kwargs):
    """
    [단계 3] 특정 연도에 대한 단일 시뮬레이션 단계를 실행합니다.

    (Why) 이 함수가 필요한 이유:
    핵심 시뮬레이션 엔진입니다. 준비된 '공급'(자원 노드)과 '수요'(대상 노드)를
    가져와 시나리오의 이주 및 철거 비율에 따라 토지 전환을 실행합니다.

    (Logic) 핵심 로직 (증분 방식):
    1. 누적 이주 비율에 따라 현재 단계에서 처리할 신규 '자원' 노드 수를 계산합니다.
    2. 처리된 자원 노드의 'CompressionFactor'에 따라 생성될 신규 'GAC 모듈'의
       총 수와 유형을 결정합니다.
    3. 가장 높은 우선순위('ReplacePriority')를 가진 도시 노드를 신규 모듈로 대체합니다.
       이전 단계에서 철거된 부지도 대체 슬롯으로 활용될 수 있습니다.
    4. 누적 철거 비율을 맞추기 위해 추가로 철거해야 할 저순위 도시 노드 수를 계산하고,
       가장 낮은 우선순위를 가진 노드부터 철거하여 '초지'로 전환합니다.

    반환값:
        tuple: (해당 연도의 결과 피처 클래스 경로, 현재까지 처리된 모든 자원 노드 ID set)
    """
    print(f"단계 3 ({year}): 시나리오 실행 시작...")
    # ... (원본 코드의 execute_incremental_scenario_revised 함수 내용 전체를 여기에 붙여넣기) ...
    # config.변수명 규칙은 동일하게 적용합니다.
    pass # 실제 코드는 여기에 위치합니다