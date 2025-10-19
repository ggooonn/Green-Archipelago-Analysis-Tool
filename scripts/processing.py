# -*- coding: utf-8 -*-
"""
GAC System Prototype의 핵심 데이터 처리 및 분석 모듈
"""
import arcpy
import os
import random
import time
from collections import defaultdict
import traceback
from . import config  # config.py 파일에서 설정 변수들을 가져옴

def allocate_integer_counts(category_potentials, total_target_count):
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
    """
    print("단계 1: 원본 그린벨트 노드 준비 시작..."); temp_items_step1 = []; source_nodes_initial_path = None; output_fc = os.path.join(config.OUTPUT_GDB, "Result1a_Source_GB_Nodes_Initial"); all_source_node_ids_local = []
    try:
        timestamp_step1 = int(time.time()); print("  1a. 영역 선택..."); gb_layer = arcpy.management.MakeFeatureLayer(gb_map_layer, f"gb_layer_{timestamp_step1}").getOutput(0); island_layer = arcpy.management.MakeFeatureLayer(island_map_layer, f"island_layer_{timestamp_step1}").getOutput(0); lc_layer = arcpy.management.MakeFeatureLayer(lc_map_layer, f"lc_layer_{timestamp_step1}").getOutput(0); temp_items_step1.extend([gb_layer, island_layer, lc_layer])
        arcpy.management.SelectLayerByLocation(lc_layer, "INTERSECT", gb_layer); arcpy.management.SelectLayerByLocation(lc_layer, "INTERSECT", island_layer, selection_type="REMOVE_FROM_SELECTION")
        source_gb_polygons_select_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_source_gb_select_{timestamp_step1}"); source_gb_polygons_select = arcpy.management.CopyFeatures(lc_layer, source_gb_polygons_select_path); temp_items_step1.append(source_gb_polygons_select_path); print(f"  선택된 폴리곤 수: {arcpy.management.GetCount(source_gb_polygons_select)}")
        if int(arcpy.management.GetCount(source_gb_polygons_select).getOutput(0)) == 0: raise Exception("그린벨트 내, 섬 외부 폴리곤 없음.")
        print(f"  1b. 원천 유형 필터링..."); field_delimited = arcpy.AddFieldDelimiters(source_gb_polygons_select_path, config.FIELD_L3_CODE); quoted_codes = [f"'{code}'" for code in config.SOURCE_L3_CODES]; where_clause = f"{field_delimited} IN ({','.join(quoted_codes)})"; print(f"  DEBUG: WHERE: {where_clause}")
        select_layer_for_attr = arcpy.management.MakeFeatureLayer(source_gb_polygons_select_path, f"select_attr_layer_{timestamp_step1}").getOutput(0); temp_items_step1.append(select_layer_for_attr); arcpy.management.SelectLayerByAttribute(select_layer_for_attr, "NEW_SELECTION", where_clause)
        source_gb_polygons_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_Source_GB_Polygons_{timestamp_step1}"); source_gb_polygons = arcpy.management.CopyFeatures(select_layer_for_attr, source_gb_polygons_path); temp_items_step1.append(source_gb_polygons_path); count_after_filter = arcpy.management.GetCount(source_gb_polygons).getOutput(0); print(f"  필터링 후 폴리곤 수: {count_after_filter}")
        if int(count_after_filter) == 0: raise Exception("필터링 후 남은 원본 그린벨트 폴리곤 없음.")
        print(f"  1c. 폴리곤을 노드로 변환..."); source_nodes_initial_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_Source_Nodes_Initial_{timestamp_step1}"); temp_items_step1.append(source_nodes_initial_path); result = arcpy.management.FeatureToPoint(source_gb_polygons, source_nodes_initial_path, "INSIDE");
        if not arcpy.Exists(source_nodes_initial_path): print(f"  오류: FeatureToPoint 실패"); raise arcpy.ExecuteError("FeatureToPoint failed")
        print(f"  FeatureToPoint 성공 확인."); node_count = arcpy.management.GetCount(source_nodes_initial_path).getOutput(0); print(f"  생성된 초기 노드 수: {node_count}")
        if int(node_count) == 0: raise Exception("FeatureToPoint 결과 노드 0개.")
        print(f"  1d. 필드 추가 및 계산..."); arcpy.management.AddField(source_nodes_initial_path, config.FIELD_UNIQUE_ID, "LONG"); arcpy.management.CalculateField(source_nodes_initial_path, config.FIELD_UNIQUE_ID, "!OBJECTID!", "PYTHON3"); arcpy.management.AddField(source_nodes_initial_path, config.FIELD_ORIG_SOURCE_CODE, "TEXT", field_length=10)
        field_names_step1 = [f.name for f in arcpy.ListFields(source_nodes_initial_path)]
        if config.FIELD_L3_CODE in field_names_step1: arcpy.management.CalculateField(source_nodes_initial_path, config.FIELD_ORIG_SOURCE_CODE, f"!{config.FIELD_L3_CODE}!", "PYTHON3")
        else: raise Exception(f"Critical error: {config.FIELD_L3_CODE} missing after FeatureToPoint in Step 1.")
        arcpy.management.AddField(source_nodes_initial_path, config.FIELD_EVOLVED_CATEGORY, "TEXT", field_length=50); arcpy.management.AddField(source_nodes_initial_path, config.FIELD_COMPRESSION_FACTOR, "LONG")
        fields_to_update = [config.FIELD_ORIG_SOURCE_CODE, config.FIELD_EVOLVED_CATEGORY, config.FIELD_COMPRESSION_FACTOR]; print(f"  DEBUG: Updating fields..."); updated_count = 0
        with arcpy.da.UpdateCursor(source_nodes_initial_path, fields_to_update) as cursor:
            for row in cursor:
                code_raw = row[0]; code = code_raw.strip() if code_raw else None; category = ""; factor = 0
                if code:
                    if code in ['211', '212']: category = "AG-FC"
                    elif code in ['221', '222']: category = "AG-LV" if random.random() < 0.7 else "AG-FC"
                    elif code == '241': category = "AG-FV"
                    elif code == '231': category = "AG-LV"
                    elif code == '251': category = "LS"
                    elif code in config.FOREST_L3_CODES: category = "FR"
                    elif code in ['411', '423', '623']: category = "NGRASS_Grazing"
                    else: print(f"      경고: 소스 코드 {code}에 대한 EvolvedCategory 규칙이 없습니다.")
                    if category:
                        factor = config.COMPRESSION_FACTORS.get(category, 1)
                        if category not in config.COMPRESSION_FACTORS:
                            print(f"      경고: compression_factors에 EvolvedCategory '{category}'에 대한 키가 없어 factor 기본값 1 사용됨. (소스 코드: {code})")
                    else: factor = 0
                if category and category in config.EVOLVED_CATEGORIES and factor > 0 :
                    row[1] = category; row[2] = factor; cursor.updateRow(row); updated_count += 1
                elif code and (not category or category not in config.EVOLVED_CATEGORIES or not (factor > 0)):
                    print(f"      경고: 소스 코드 {code}가 유효한 EvolvedCategory('{category}', evolved_list에 있음: {category in config.EVOLVED_CATEGORIES}) 또는 CompressionFactor('{factor}')를 할당받지 못했습니다.")
        print(f"  DEBUG: Cursor 종료. {updated_count}개 유효 업데이트.")
        invalid_where = f"({config.FIELD_EVOLVED_CATEGORY} = '' OR {config.FIELD_EVOLVED_CATEGORY} IS NULL) OR ({config.FIELD_COMPRESSION_FACTOR} <= 0 OR {config.FIELD_COMPRESSION_FACTOR} IS NULL)"
        print(f"  DEBUG: Checking for invalid nodes..."); temp_layer_for_delete_check = arcpy.management.MakeFeatureLayer(source_nodes_initial_path, f"delete_check_layer_{timestamp_step1}").getOutput(0); temp_items_step1.append(temp_layer_for_delete_check)
        arcpy.management.SelectLayerByAttribute(temp_layer_for_delete_check, "NEW_SELECTION", invalid_where); count_invalid = int(arcpy.management.GetCount(temp_layer_for_delete_check).getOutput(0))
        if count_invalid > 0: print(f"  경고: 유효하지 않은 노드 {count_invalid}개 삭제."); arcpy.management.DeleteFeatures(temp_layer_for_delete_check)
        else: print("  유효성 검사: 삭제할 노드 없음.")
        if arcpy.Exists(output_fc): arcpy.management.Delete(output_fc)
        arcpy.management.CopyFeatures(source_nodes_initial_path, output_fc); print(f"단계 1 완료. 저장: {output_fc}"); final_count = arcpy.management.GetCount(output_fc).getOutput(0); print(f"  최종 저장된 원본 노드 수: {final_count}")
        if int(final_count) == 0: print("  치명적 경고: 단계 1 결과 유효한 원본 노드가 없습니다.")
        all_source_node_ids_local = [row[0] for row in arcpy.da.SearchCursor(output_fc, [config.FIELD_UNIQUE_ID])]
        return output_fc, all_source_node_ids_local
    except arcpy.ExecuteError: print(f"ArcGIS Error in Step 1:\n{arcpy.GetMessages(2)}"); traceback.print_exc(); raise
    except Exception as e: print(f"Non-ArcGIS Error in Step 1: {e}"); traceback.print_exc(); raise
    finally:
        print("  단계 1 임시 데이터 정리...");
        for item in temp_items_step1:
            if item and arcpy.Exists(item):
                try: arcpy.management.Delete(item)
                except Exception as del_e: print(f"    임시 삭제 오류 무시 ({os.path.basename(str(item))}): {del_e}")

def prepare_target_island_nodes(lc_map_layer, island_poly_map_layer):
    """
    [단계 2] '대상(Target)' 노드를 준비하고 대체 우선순위를 계산합니다.
    """
    print("단계 2 (No SA): 대체 대상 섬 노드 준비 및 섬별 우선순위 계산 시작...")
    temp_items_step2 = []; output_initial_island_nodes = os.path.join(config.OUTPUT_GDB, "Result1b_Island_Nodes_Initial_Labeled")
    total_original_replaceable_count = 0; prioritized_target_node_ids_global = []
    near_tool_dist_field = "NEAR_DIST"
    try:
        timestamp_step2 = int(time.time()); print(f"  단계 2 시작 시간: {timestamp_step2}")
        quoted_ind_codes = [f"'{c}'" for c in config.INDUSTRIAL_L3_CODES]; where_clause_industrial = f"{config.FIELD_L3_CODE} IN ({','.join(quoted_ind_codes)})"
        where_clause_replaceable = f"({config.FIELD_NODE_STATUS} = '{config.STATUS_ORIGINAL_LOW_PRI}' OR {config.FIELD_NODE_STATUS} = '{config.STATUS_ORIGINAL_HIGH_PRI}')"
        print("  2a. 섬 폴리곤 레이어 준비..."); island_poly_desc = arcpy.Describe(island_poly_map_layer)
        if isinstance(island_poly_map_layer, str): island_poly_path = island_poly_map_layer
        elif hasattr(island_poly_map_layer, 'dataSource'): island_poly_path = island_poly_map_layer.dataSource
        else: raise TypeError("island_poly_map_layer 타입오류")
        if not arcpy.Exists(island_poly_path): raise ValueError(f"오류: 섬 폴리곤 경로 없음: {island_poly_path}")
        poly_fields = [f.name for f in arcpy.ListFields(island_poly_path)]; found_poly_id_field = False
        island_id_field_on_polys = config.FIELD_ISLAND_ID_IN_POLYGONS
        for fld_name in poly_fields:
            if fld_name.upper() == island_id_field_on_polys.upper(): island_id_field_on_polys = fld_name; found_poly_id_field = True; break
        if not found_poly_id_field: raise ValueError(f"오류: 섬 폴리곤 ID 필드 '{island_id_field_on_polys}' 없음.")
        print(f"    섬 폴리곤 ID 필드 '{island_id_field_on_polys}' 확인.")
        island_poly_layer_view = arcpy.management.MakeFeatureLayer(island_poly_path, f"island_polys_view_{timestamp_step2}"); temp_items_step2.append(island_poly_layer_view)
        print("  2b. 모든 섬 내부 토지피복 선택 및 노드 생성..."); lc_layer_view = arcpy.management.MakeFeatureLayer(lc_map_layer, f"lc_layer_s2_{timestamp_step2}"); temp_items_step2.append(lc_layer_view)
        arcpy.management.SelectLayerByLocation(lc_layer_view, "INTERSECT", island_poly_layer_view)
        count_lc_in_islands = int(arcpy.management.GetCount(lc_layer_view).getOutput(0))
        if count_lc_in_islands == 0: raise Exception("섬 내 토지피복 폴리곤 없음.")
        print(f"    섬 내부 토지피복 폴리곤 수: {count_lc_in_islands}")
        _internal_original_island_lc_polys_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_internal_orig_island_lc_polys_{timestamp_step2}"); temp_items_step2.append(_internal_original_island_lc_polys_path)
        arcpy.management.CopyFeatures(lc_layer_view, _internal_original_island_lc_polys_path)
        island_nodes_initial_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_Island_Nodes_Initial_{timestamp_step2}"); temp_items_step2.append(island_nodes_initial_path)
        arcpy.management.FeatureToPoint(_internal_original_island_lc_polys_path, island_nodes_initial_path, "INSIDE");
        node_count_initial = int(arcpy.management.GetCount(island_nodes_initial_path).getOutput(0))
        if node_count_initial == 0: raise Exception("섬 내부 노드 생성 실패.")
        print(f"    생성된 총 섬 노드 수: {node_count_initial}")
        if config.FIELD_ORIG_POLY_FID not in [f.name for f in arcpy.ListFields(island_nodes_initial_path)]: print(f"    경고: {config.FIELD_ORIG_POLY_FID} 필드 없음.")
        print("  2c. 초기 필드 추가 (UniqueID, Status, Label)...");
        if config.FIELD_UNIQUE_ID not in [f.name for f in arcpy.ListFields(island_nodes_initial_path)]: arcpy.management.AddField(island_nodes_initial_path, config.FIELD_UNIQUE_ID, "LONG")
        arcpy.management.CalculateField(island_nodes_initial_path, config.FIELD_UNIQUE_ID, "!OBJECTID!", "PYTHON3")
        node_fields_check_2c = [f.name for f in arcpy.ListFields(island_nodes_initial_path)]
        if config.FIELD_L3_CODE not in node_fields_check_2c: raise Exception(f"{config.FIELD_L3_CODE} field missing after FeatureToPoint.")
        field_obj_lc_code = arcpy.ListFields(island_nodes_initial_path, config.FIELD_L3_CODE)[0]
        if field_obj_lc_code.type != 'String': print(f"    경고: {config.FIELD_L3_CODE} 필드 타입이 String이 아님 (실제: {field_obj_lc_code.type}).")
        if config.FIELD_NODE_STATUS not in node_fields_check_2c: arcpy.management.AddField(island_nodes_initial_path, config.FIELD_NODE_STATUS, "TEXT", field_length=50)
        if config.FIELD_NODE_TYPE_LABEL not in node_fields_check_2c: arcpy.management.AddField(island_nodes_initial_path, config.FIELD_NODE_TYPE_LABEL, "TEXT", field_length=50)
        fields_to_update_status = [config.FIELD_L3_CODE, config.FIELD_NODE_STATUS, config.FIELD_NODE_TYPE_LABEL]; print(f"    노드 상태 및 라벨 계산 준비 중. 필드: {fields_to_update_status}")
        print("    노드 상태 및 라벨 계산 중 (UpdateCursor 진입 시도)..."); time.sleep(0.5)
        try:
            with arcpy.da.UpdateCursor(island_nodes_initial_path, fields_to_update_status) as cursor:
                print("      DEBUG: UpdateCursor 생성 성공. 루프 시작...")
                update_count_2c = 0
                for idx, row in enumerate(cursor):
                    try:
                        code_val = row[0]; code = code_val.strip() if isinstance(code_val, str) else (str(code_val) if code_val is not None else None)
                        current_status = config.STATUS_ORIGINAL_NONURBAN; current_label = config.NODE_TYPE_LABELS.get(code, f"Unknown_{code}")
                        if code in config.FOREST_L3_CODES: current_status = config.STATUS_ORIGINAL_NONURBAN; current_label = config.NODE_TYPE_LABELS.get(code, f"Forest_{code}")
                        elif code in config.LOW_PRIORITY_URBAN_CODES: current_status = config.STATUS_ORIGINAL_LOW_PRI
                        elif code in config.HIGH_PRIORITY_URBAN_CODES: current_status = config.STATUS_ORIGINAL_HIGH_PRI
                        elif code in config.TRANSPORT_L3_CODES: current_status = config.STATUS_ORIGINAL_TRANSPORT
                        row[1] = current_status; row[2] = current_label
                        if code in config.FOREST_L3_CODES: row[2] = config.NODE_TYPE_LABELS.get(code, f"Forest_{code}")
                        cursor.updateRow(row); update_count_2c += 1
                    except Exception as e_row: print(f"        오류 발생 행 {idx}, 값: {row}, 오류: {e_row}")
            print(f"    상태/라벨 업데이트 완료 ({update_count_2c}개 노드).")
        except arcpy.ExecuteError as e_cursor_arc: print(f"      ArcPy 오류 (UpdateCursor): {arcpy.GetMessages(2)}"); traceback.print_exc(); raise
        except Exception as e_cursor_gen: print(f"      일반 오류 (UpdateCursor): {e_cursor_gen}"); traceback.print_exc(); raise
        temp_replaceable_layer = arcpy.management.MakeFeatureLayer(island_nodes_initial_path, f"repl_count_layer_{timestamp_step2}", where_clause_replaceable)
        total_original_replaceable_count = int(arcpy.management.GetCount(temp_replaceable_layer).getOutput(0)); arcpy.management.Delete(temp_replaceable_layer)
        print(f"    초기 대체 가능 도시 노드 총 수 (Low+High, 임야 제외): {total_original_replaceable_count}")
        print(f"  2d. 각 노드에 섬 ID ({config.FIELD_ISLAND_ID}) 할당 (Spatial Join)...");
        poly_id_field_info_list = [f for f in arcpy.ListFields(island_poly_path) if f.name.upper() == island_id_field_on_polys.upper()]
        if not poly_id_field_info_list: raise ValueError(f"오류: 섬 폴리곤 ID 필드 '{island_id_field_on_polys}' 없음 (대소문자 확인 후).")
        poly_id_field_info = poly_id_field_info_list[0]
        target_field_type = "TEXT" if poly_id_field_info.type == 'String' else ("LONG" if poly_id_field_info.type in ['Integer', 'SmallInteger', 'OID'] else "DOUBLE")
        target_field_length = poly_id_field_info.length if target_field_type == "TEXT" else None
        if config.FIELD_ISLAND_ID not in [f.name for f in arcpy.ListFields(island_nodes_initial_path)]: arcpy.management.AddField(island_nodes_initial_path, config.FIELD_ISLAND_ID, target_field_type, field_length=target_field_length)
        joined_nodes_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_nodes_joined_{timestamp_step2}"); temp_items_step2.append(joined_nodes_path)
        join_field_in_polys = island_id_field_on_polys; field_mapping = arcpy.FieldMappings(); field_mapping.addTable(island_nodes_initial_path)
        target_fm_index = field_mapping.findFieldMapIndex(config.FIELD_ISLAND_ID)
        if target_fm_index == -1: raise Exception(f"Could not find FieldMap for target field: {config.FIELD_ISLAND_ID}")
        fm_target = field_mapping.getFieldMap(target_fm_index)
        join_table_fields = arcpy.ListFields(island_poly_layer_view); found_join_field = None
        for fld in join_table_fields:
            if fld.name.upper() == join_field_in_polys.upper(): found_join_field = fld.name; break
        if not found_join_field: raise ValueError(f"Join field '{join_field_in_polys}' not found.")
        fm_join = arcpy.FieldMap(); fm_join.addInputField(island_poly_layer_view, found_join_field)
        out_field = fm_target.outputField; out_field.name = config.FIELD_ISLAND_ID; out_field.aliasName = config.FIELD_ISLAND_ID; out_field.type = target_field_type
        if target_field_length: out_field.length = target_field_length
        fm_target.outputField = out_field; fm_target.mergeRule = "First"; fm_target.addInputField(island_poly_layer_view,found_join_field)
        field_mapping.replaceFieldMap(target_fm_index, fm_target)
        print("    Spatial Join 필드 매핑 설정 완료."); print("    Spatial Join 실행..."); arcpy.analysis.SpatialJoin(island_nodes_initial_path, island_poly_layer_view, joined_nodes_path, "JOIN_ONE_TO_ONE", "KEEP_ALL", field_mapping, "INTERSECT"); print("    Spatial Join 완료.")
        arcpy.management.Delete(island_nodes_initial_path)
        arcpy.management.Rename(joined_nodes_path, os.path.basename(island_nodes_initial_path))
        island_nodes_initial_path = os.path.join(arcpy.env.scratchWorkspace, os.path.basename(island_nodes_initial_path))
        print("    섬 ID 포함 노드 레이어 업데이트 완료.")
        if config.FIELD_ORIG_POLY_FID not in [f.name for f in arcpy.ListFields(island_nodes_initial_path)]: print(f"    경고: Spatial Join 후 {config.FIELD_ORIG_POLY_FID} 필드 유실.")
        null_id_where = f"{config.FIELD_ISLAND_ID} IS NULL OR {config.FIELD_ISLAND_ID} = ''" if target_field_type == 'TEXT' else f"{config.FIELD_ISLAND_ID} IS NULL"
        null_count = int(arcpy.management.GetCount(arcpy.management.MakeFeatureLayer(island_nodes_initial_path, f"null_id_check_{timestamp_step2}", null_id_where)).getOutput(0))
        if null_count > 0: print(f"    경고: {null_count}개 노드에 섬 ID 할당 안됨.")
        print("  2e. 섬별 우선순위 계산 (거리:중심, 거리:공업)...");
        arcpy.management.AddField(island_nodes_initial_path, config.FIELD_NEAR_CENTROID_DIST, "DOUBLE"); arcpy.management.AddField(island_nodes_initial_path, config.FIELD_NEAR_INDUSTRIAL_DIST, "DOUBLE"); arcpy.management.AddField(island_nodes_initial_path, config.FIELD_REPLACEMENT_PRIORITY, "DOUBLE")
        arcpy.management.CalculateField(island_nodes_initial_path, config.FIELD_NEAR_CENTROID_DIST, str(config.DEFAULT_LARGE_DISTANCE)); arcpy.management.CalculateField(island_nodes_initial_path, config.FIELD_NEAR_INDUSTRIAL_DIST, str(config.DEFAULT_LARGE_DISTANCE)); arcpy.management.CalculateField(island_nodes_initial_path, config.FIELD_REPLACEMENT_PRIORITY, "-1.0")
        unique_island_ids_where = f"{config.FIELD_ISLAND_ID} IS NOT NULL AND {config.FIELD_ISLAND_ID} <> ''" if target_field_type == 'TEXT' else f"{config.FIELD_ISLAND_ID} IS NOT NULL"
        print(f"    Unique island ID를 위한 커서 생성 시도: {island_nodes_initial_path}, 필드: {config.FIELD_ISLAND_ID}, 조건: {unique_island_ids_where}")
        unique_island_ids_cursor = arcpy.da.SearchCursor(island_nodes_initial_path, [config.FIELD_ISLAND_ID], where_clause=unique_island_ids_where)
        unique_island_ids = sorted(list(set(row[0] for row in unique_island_ids_cursor))); del unique_island_ids_cursor
        print(f"    처리할 고유 섬 ID 개수: {len(unique_island_ids)}")
        processed_island_count = 0
        for current_island_id in unique_island_ids:
            processed_island_count += 1; print(f"\n      --- 섬 ID: {current_island_id} 처리 중 ({processed_island_count}/{len(unique_island_ids)}) ---"); island_temp_items = []
            if isinstance(current_island_id, str): escaped_island_id = current_island_id.replace("'", "''"); where_island = f"{config.FIELD_ISLAND_ID} = '{escaped_island_id}'"; where_poly_island = f"{island_id_field_on_polys} = '{escaped_island_id}'"
            else: where_island = f"{config.FIELD_ISLAND_ID} = {current_island_id}"; where_poly_island = f"{island_id_field_on_polys} = {current_island_id}"
            where_clause_for_island_priority_nodes = f"({where_island}) AND ({where_clause_replaceable})"
            print(f"        현재 섬 우선순위 계산 대상 노드 선택 조건: {where_clause_for_island_priority_nodes}")
            current_priority_calc_nodes_view = arcpy.management.MakeFeatureLayer(island_nodes_initial_path, f"nodes_priocalc_current_{timestamp_step2}", where_clause_for_island_priority_nodes); island_temp_items.append(current_priority_calc_nodes_view)
            node_count_for_priority = int(arcpy.management.GetCount(current_priority_calc_nodes_view).getOutput(0))
            if node_count_for_priority == 0: print(f"        경고: 섬 ID {current_island_id}에 우선순위 계산 대상 노드 없음."); continue
            print("        2e-1. 섬 중심까지 거리 계산..."); current_poly_view = arcpy.management.MakeFeatureLayer(island_poly_layer_view, f"poly_current_{timestamp_step2}", where_poly_island); island_temp_items.append(current_poly_view)
            if int(arcpy.management.GetCount(current_poly_view).getOutput(0)) == 0: print(f"    경고: ID '{current_island_id}' 폴리곤 없음."); continue
            centroid_path = os.path.join(arcpy.env.scratchWorkspace, f"temp_centroid_{timestamp_step2}"); island_temp_items.append(centroid_path)
            try:
                arcpy.management.FeatureToPoint(current_poly_view, centroid_path, "INSIDE")
                arcpy.analysis.Near(current_priority_calc_nodes_view, centroid_path, method='PLANAR')
                arcpy.management.CalculateField(current_priority_calc_nodes_view, config.FIELD_NEAR_CENTROID_DIST, f"!{near_tool_dist_field}!"); print(f"          중심점 거리 계산 완료.")
            except Exception as near_err: print(f"        오류: 중심점 Near/계산 실패: {near_err}.")
            print("        2e-2. 가장 가까운 공업지역까지 거리 계산...");
            where_clause_island_industrial = f"({where_island}) AND ({where_clause_industrial})"
            current_ind_nodes_view = arcpy.management.MakeFeatureLayer(island_nodes_initial_path, f"ind_nodes_current_{timestamp_step2}", where_clause_island_industrial); island_temp_items.append(current_ind_nodes_view)
            ind_node_count = int(arcpy.management.GetCount(current_ind_nodes_view).getOutput(0))
            if ind_node_count > 0:
                try: arcpy.analysis.Near(current_priority_calc_nodes_view, current_ind_nodes_view, method='PLANAR'); arcpy.management.CalculateField(current_priority_calc_nodes_view, config.FIELD_NEAR_INDUSTRIAL_DIST, f"!{near_tool_dist_field}!"); print(f"          공업지역 거리 계산 완료.")
                except Exception as near_ind_err: print(f"        오류: 공업지역 Near/계산 실패: {near_ind_err}.")
            else: print(f"          이 섬에 공업 노드가 없어 거리 계산 생략.")
            print("        2e-3. 우선순위 점수 계산 (섬 내 정규화)...")
            min_cen_d, max_cen_d, min_ind_d, max_ind_d = float('inf'), 0, float('inf'), 0; has_valid_cen_dist = False; has_valid_ind_dist = False
            try:
                fields_for_norm = [config.FIELD_NEAR_CENTROID_DIST, config.FIELD_NEAR_INDUSTRIAL_DIST]
                print(f"          정규화 커서 대상 노드 수: {arcpy.management.GetCount(current_priority_calc_nodes_view)}")
                with arcpy.da.SearchCursor(current_priority_calc_nodes_view, fields_for_norm) as norm_cursor:
                    for idx, row in enumerate(norm_cursor):
                        cen_dist = row[0] if row[0] is not None and row[0] < config.DEFAULT_LARGE_DISTANCE else None; ind_dist = row[1] if row[1] is not None and row[1] < config.DEFAULT_LARGE_DISTANCE else None
                        if cen_dist is not None: has_valid_cen_dist = True; min_cen_d = min(min_cen_d, cen_dist); max_cen_d = max(max_cen_d, cen_dist)
                        if ind_dist is not None: has_valid_ind_dist = True; min_ind_d = min(min_ind_d, ind_dist); max_ind_d = max(max_ind_d, ind_dist)
            except Exception as read_err: print(f"        오류: 정규화 거리 값 읽기 실패: {read_err}.")
            print(f"          정규화 범위 - 중심거리: {'{:.2f}'.format(min_cen_d) if has_valid_cen_dist else 'N/A'} ~ {'{:.2f}'.format(max_cen_d) if has_valid_cen_dist else 'N/A'}, 공업거리: {'{:.2f}'.format(min_ind_d) if has_valid_ind_dist else 'N/A'} ~ {'{:.2f}'.format(max_ind_d) if has_valid_ind_dist else 'N/A'}")
            fields_for_priority = [config.FIELD_NODE_STATUS, config.FIELD_NEAR_CENTROID_DIST, config.FIELD_NEAR_INDUSTRIAL_DIST, config.FIELD_REPLACEMENT_PRIORITY]; update_count_pri = 0
            try:
                current_fields_main_layer = [f.name for f in arcpy.ListFields(island_nodes_initial_path)];
                if not all(f in current_fields_main_layer for f in fields_for_priority): raise Exception(f"Priority fields missing in main layer")
                print(f"          우선순위 업데이트 커서 대상 노드 수: {arcpy.management.GetCount(current_priority_calc_nodes_view)}")
                with arcpy.da.UpdateCursor(current_priority_calc_nodes_view, fields_for_priority) as pri_cursor:
                    for idx, row in enumerate(pri_cursor):
                        status, cen_dist_raw, ind_dist_raw, _ = row; cen_dist = cen_dist_raw if cen_dist_raw is not None and cen_dist_raw < config.DEFAULT_LARGE_DISTANCE else None; ind_dist = ind_dist_raw if ind_dist_raw is not None and ind_dist_raw < config.DEFAULT_LARGE_DISTANCE else None
                        norm_inv_cen_dist = 0.5
                        if has_valid_cen_dist and cen_dist is not None:
                            if (max_cen_d - min_cen_d) > 1e-6: norm_inv_cen_dist = 1.0 - ((cen_dist - min_cen_d) / (max_cen_d - min_cen_d))
                            norm_inv_cen_dist = max(0.0, min(1.0, norm_inv_cen_dist))
                        norm_inv_ind_dist = 0.0
                        if has_valid_ind_dist and ind_dist is not None:
                            if (max_ind_d - min_ind_d) > 1e-6: norm_inv_ind_dist = 1.0 - ((ind_dist - min_ind_d) / (max_ind_d - min_ind_d))
                            else: norm_inv_ind_dist = 0.5
                            norm_inv_ind_dist = max(0.0, min(1.0, norm_inv_ind_dist))
                        status_score = 1.0 if status == config.STATUS_ORIGINAL_HIGH_PRI else 0.1
                        final_score = (config.WEIGHT_STATUS * status_score) + (config.WEIGHT_INV_CEN_DIST * norm_inv_cen_dist) + (config.WEIGHT_INV_IND_DIST * norm_inv_ind_dist)
                        row[3] = final_score; pri_cursor.updateRow(row); update_count_pri += 1
                print(f"          우선순위 점수 계산/업데이트 완료 ({update_count_pri}개 노드).")
            except Exception as pri_err: print(f"        오류: 우선순위 점수 계산 UpdateCursor 실패: {pri_err}")
            print("        섬별 임시 데이터 정리...");
            for item in island_temp_items:
                if item and arcpy.Exists(item):
                    try: arcpy.management.Delete(item)
                    except Exception as del_e_island: print(f"          섬별 임시 삭제 오류 무시: {del_e_island}")

        print("\n  2f. 전역 우선순위 목록 생성 및 최종 결과 저장...")
        with arcpy.da.SearchCursor(island_nodes_initial_path, [config.FIELD_UNIQUE_ID], where_clause=where_clause_replaceable, sql_clause=(None, f"ORDER BY {config.FIELD_REPLACEMENT_PRIORITY} DESC")) as cursor:
            prioritized_target_node_ids_global = [row[0] for row in cursor]
        print(f"    전역 우선순위 정렬 완료. 대상 ID 수: {len(prioritized_target_node_ids_global)}")
        island_nodes_with_priority_path = output_initial_island_nodes
        if arcpy.Exists(island_nodes_with_priority_path): arcpy.management.Delete(island_nodes_with_priority_path)
        arcpy.management.CopyFeatures(island_nodes_initial_path, island_nodes_with_priority_path)
        print(f"단계 2 (No SA) 완료. 포인트 결과 저장: {island_nodes_with_priority_path}")
        return island_nodes_with_priority_path, prioritized_target_node_ids_global, total_original_replaceable_count

    except arcpy.ExecuteError: print(f"ArcGIS Error in Step 2 (No SA):\n{arcpy.GetMessages(2)}"); traceback.print_exc(); raise
    except Exception as e: print(f"Non-ArcGIS Error in Step 2 (No SA): {e}"); traceback.print_exc(); raise
    finally:
        print("  단계 2 전체 임시 데이터 정리...");
        for item in temp_items_step2:
            if item and arcpy.Exists(item):
                try: arcpy.management.Delete(item)
                except Exception as del_e: print(f"    임시 삭제 오류 무시 ({os.path.basename(str(item))}): {del_e}")


def execute_scenario_phase(phase_name, previous_year_result_path, source_nodes_data_path, **kwargs):
    """
    [단계 3] 특정 단계(Phase)에 대한 시뮬레이션을 실행합니다.
    (v37의 'execute_incremental_scenario_revised' 함수를 기반으로 함)
    """
    print(f"단계 3 ({phase_name}): 시나리오 실행 시작 (대체 우선, 대체 대상 확대, 증분 누적)...")
    
    # kwargs에서 필요한 모든 파라미터 추출
    all_source_node_ids = kwargs.get('all_source_node_ids', [])
    total_source_nodes_count = kwargs.get('total_source_nodes_count', 0)
    total_original_replaceable_count = kwargs.get('total_original_replaceable_count', 0)
    processed_source_node_ids = kwargs.get('processed_source_node_ids', set())
    p_cumulative_migration_ratio_curr = kwargs.get('p_cumulative_migration_ratio_curr', 0.0)
    p_cumulative_demolition_ratio_curr = kwargs.get('p_cumulative_demolition_ratio_curr', 0.0)
    p_cumulative_migration_ratio_prev = kwargs.get('p_cumulative_migration_ratio_prev', 0.0)
    p_cumulative_demolition_ratio_prev = kwargs.get('p_cumulative_demolition_ratio_prev', 0.0)

    output_path = None; temp_items_step3 = []; newly_demolished_ids = set(); newly_replaced_ids = set()
    try:
        timestamp_step3 = int(time.time())
        if not previous_year_result_path or not arcpy.Exists(previous_year_result_path): raise ValueError(f"이전 결과 파일 없음: {previous_year_result_path}")
        if not source_nodes_data_path or not arcpy.Exists(source_nodes_data_path): raise ValueError(f"소스 노드 파일 없음: {source_nodes_data_path}")
        
        # [수정됨] 결과 파일 이름에 phase_name 사용
        output_layer_name = f"Result_Island_Nodes_{phase_name}"; 
        output_path = os.path.join(config.OUTPUT_GDB, output_layer_name)
        
        # 임시 작업 레이어는 scratch GDB에 생성
        temp_output_path = os.path.join(arcpy.env.scratchWorkspace, f"Temp_{output_layer_name}_{timestamp_step3}")
        temp_items_step3.append(temp_output_path)

        if arcpy.Exists(temp_output_path): arcpy.management.Delete(temp_output_path)
        arcpy.management.CopyFeatures(previous_year_result_path, temp_output_path); print(f"  {phase_name} 임시 작업 레이어 생성: {temp_output_path}")
        if not arcpy.Exists(temp_output_path): raise Exception(f"임시 작업 파일 생성 확인 실패: {temp_output_path}")
        time.sleep(0.5)
        
        current_fields_step3 = [f.name for f in arcpy.ListFields(temp_output_path)]
        if config.FIELD_REPLACEMENT_PRIORITY not in current_fields_step3: print(f"  경고: 우선순위 필드({config.FIELD_REPLACEMENT_PRIORITY}) 없음. 임의 정렬 사용됨."); order_by_field_dem = config.FIELD_UNIQUE_ID; order_by_field_rep = config.FIELD_UNIQUE_ID
        else: order_by_field_dem = config.FIELD_REPLACEMENT_PRIORITY; order_by_field_rep = config.FIELD_REPLACEMENT_PRIORITY; print(f"  우선순위 필드({config.FIELD_REPLACEMENT_PRIORITY}) 확인됨.")
        
        status_check_field_delim = arcpy.AddFieldDelimiters(temp_output_path, config.FIELD_NODE_STATUS)
        node_type_label_field_delim_for_sql = arcpy.AddFieldDelimiters(temp_output_path, config.FIELD_NODE_TYPE_LABEL)

        # === 3A. Incremental Replacement First ===
        print(f"  --- 3A. {phase_name} 대체 작업 (증분 적용) ---")
        target_source_cumulative = round(total_source_nodes_count * p_cumulative_migration_ratio_curr)
        num_source_processed_prev = len(processed_source_node_ids); num_source_to_process_this_step = max(0, target_source_cumulative - num_source_processed_prev)
        print(f"    누적 처리 원본 목표 {target_source_cumulative}개, 이전 처리 {num_source_processed_prev}개, 이번 단계 처리 {num_source_to_process_this_step}개")
        num_evolved_nodes_this_step = 0; evolved_category_counts_this_step = {}; selected_new_source_oids = []
        if num_source_to_process_this_step > 0 and total_source_nodes_count > 0 :
            available_source_ids = [id_val for id_val in all_source_node_ids if id_val not in processed_source_node_ids]
            if num_source_to_process_this_step > len(available_source_ids): print(f"    경고: 처리할 새 원본 노드 부족."); num_source_to_process_this_step = len(available_source_ids)
            if num_source_to_process_this_step > 0:
                selected_new_source_oids = random.sample(available_source_ids, num_source_to_process_this_step); selected_oids_str = ','.join(map(str, selected_new_source_oids)); print(f"    신규 원본 노드 ID {len(selected_new_source_oids)}개 선정.")
                fields_to_read_source = [config.FIELD_EVOLVED_CATEGORY, config.FIELD_COMPRESSION_FACTOR, config.FIELD_UNIQUE_ID, config.FIELD_ORIG_SOURCE_CODE];
                where_clause_select_new = f"{config.FIELD_UNIQUE_ID} IN ({selected_oids_str})" if selected_oids_str else "1=0"
                total_evolved_potential_this_step = 0.0; evolved_category_potential_this_step = defaultdict(float);
                print(f"      소스 노드 정보 읽기 시작 (선택된 {len(selected_new_source_oids)}개 대상)...")
                try:
                    with arcpy.da.SearchCursor(source_nodes_data_path, fields_to_read_source, where_clause=where_clause_select_new) as cursor:
                        for row_idx, row_data in enumerate(cursor):
                            category, factor, src_id, orig_l3 = row_data[0], row_data[1], row_data[2], row_data[3]
                            if category in config.EVOLVED_CATEGORIES and factor is not None and factor > 0 :
                                potential_contribution = 1.0 / factor; total_evolved_potential_this_step += potential_contribution; evolved_category_potential_this_step[category] += potential_contribution
                            else: print(f"        -> 제외됨: Category ('{category}') in p_list ({category in config.EVOLVED_CATEGORIES})? Factor ('{factor}') > 0 ({factor is not None and factor > 0})?")
                except Exception as src_read_err: print(f"    오류: 신규 원본 노드 정보 읽기 실패: {src_read_err}"); total_evolved_potential_this_step = 0
                num_evolved_nodes_this_step = round(total_evolved_potential_this_step); print(f"    생성될 총 진화 노드 수: {num_evolved_nodes_this_step}")
                if num_evolved_nodes_this_step > 0: evolved_category_counts_this_step = allocate_integer_counts(evolved_category_potential_this_step, num_evolved_nodes_this_step); print(f"    카테고리별 할당량: {dict(evolved_category_counts_this_step)}")
                else: evolved_category_counts_this_step = {}
            else: print("    처리할 신규 원본 노드 없음.")
        elif total_source_nodes_count == 0: print("    원본 노드 없어 대체 작업 생략.")
        else: print("  이번 단계 추가 처리 원본 노드 없음.")

        where_available_for_replacement_new = (
            f"({status_check_field_delim} = '{config.STATUS_ORIGINAL_LOW_PRI}' OR "
            f"{status_check_field_delim} = '{config.STATUS_ORIGINAL_HIGH_PRI}' OR "
            f"{node_type_label_field_delim_for_sql} = '{config.DEMOLISHED_LABEL}')"
        )
        print(f"    대체 대상 슬롯 검색 조건: {where_available_for_replacement_new}")
        available_slots_for_replace_layer = arcpy.management.MakeFeatureLayer(temp_output_path, f"available_slots_repl_{timestamp_step3}").getOutput(0); temp_items_step3.append(available_slots_for_replace_layer)
        arcpy.management.SelectLayerByAttribute(available_slots_for_replace_layer, "NEW_SELECTION", where_available_for_replacement_new)
        current_replaceable_slots_count = int(arcpy.management.GetCount(available_slots_for_replace_layer).getOutput(0))
        print(f"    현재 대체 가능한 슬롯 수 (Original Urban + Demolished_To_Grazing): {current_replaceable_slots_count}")

        num_nodes_to_replace_this_scenario = min(num_evolved_nodes_this_step, current_replaceable_slots_count); print(f"    이번 단계 최종 대체될 섬 노드 수 = {num_nodes_to_replace_this_scenario}")
        if num_nodes_to_replace_this_scenario > 0:
            available_slot_ids_ordered_by_priority = []; sql_clause_rep = (None, f"ORDER BY {order_by_field_rep} DESC"); print(f"        대체 대상 선정 SearchCursor (정렬: {order_by_field_rep} DESC)...")
            try:
                with arcpy.da.SearchCursor(available_slots_for_replace_layer, [config.FIELD_UNIQUE_ID, order_by_field_rep], sql_clause=sql_clause_rep) as cursor: [available_slot_ids_ordered_by_priority.append(row[0]) for row in cursor]; print(f"        정렬된 가용 슬롯 ID {len(available_slot_ids_ordered_by_priority)}개 확인.")
            except Exception as e_rep_srch: print(f"        오류: 대체 대상 슬롯 검색 실패 - {e_rep_srch}"); available_slot_ids_ordered_by_priority = []
            target_ids_to_replace = available_slot_ids_ordered_by_priority[:num_nodes_to_replace_this_scenario]; target_ids_str = ','.join(map(str, target_ids_to_replace)); print(f"        대체 대상 슬롯 ID {len(target_ids_to_replace)}개 선정.")
            if target_ids_str and evolved_category_counts_this_step:
                print("    대체 작업 수행..."); updates_dict = {}; processed_indices_target = 0;
                temp_category_counts = evolved_category_counts_this_step.copy(); target_id_index = 0;
                category_keys_ordered = list(temp_category_counts.keys()); random.shuffle(category_keys_ordered); assigned_count = 0
                while assigned_count < num_nodes_to_replace_this_scenario and target_id_index < len(target_ids_to_replace):
                    assigned_this_target = False
                    for category in category_keys_ordered:
                        if temp_category_counts.get(category, 0) > 0: current_target_id = target_ids_to_replace[target_id_index]; updates_dict[current_target_id] = category; temp_category_counts[category] -= 1; target_id_index += 1; assigned_count += 1; assigned_this_target = True; category_keys_ordered.append(category_keys_ordered.pop(0)); break
                    if not assigned_this_target: print(f"Warning: Ran out of categories to assign."); break
                if assigned_count != num_nodes_to_replace_this_scenario: print(f"Warning: Category assignment count mismatch.")
                update_count_actual = 0; fields_to_update_replace = [config.FIELD_UNIQUE_ID, config.FIELD_NODE_TYPE_LABEL, config.FIELD_NODE_STATUS]; where_clause_replace = f"{config.FIELD_UNIQUE_ID} IN ({target_ids_str})"
                print(f"        UpdateCursor 실행...");
                try:
                    time.sleep(0.5);
                    with arcpy.da.UpdateCursor(temp_output_path, fields_to_update_replace, where_clause=where_clause_replace) as cursor:
                        for row in cursor:
                            current_id = row[0];
                            if current_id in updates_dict:
                                new_label = updates_dict[current_id]
                                if row[2] in [config.STATUS_ORIGINAL_LOW_PRI, config.STATUS_ORIGINAL_HIGH_PRI] or row[1] == config.DEMOLISHED_LABEL:
                                    row[1] = new_label; row[2] = config.STATUS_REPLACED; cursor.updateRow(row); update_count_actual += 1
                    print(f"    {update_count_actual}개 노드 상태 '{config.STATUS_REPLACED}' 업데이트 완료."); newly_replaced_ids = set(target_ids_to_replace)
                except Exception as update_err: print(f"    오류: 대체 UpdateCursor 실패 - {update_err}"); raise
            elif not target_ids_str: print("    대체 대상 ID 없음.")
            elif not evolved_category_counts_this_step: print("    대체할 카테고리 없음.")
        else: print("    이번 단계 대체 작업 없음.")
        processed_source_node_ids.update(selected_new_source_oids)
        time.sleep(0.5)

        # === 3B. Incremental Demolition (After Replacement) ===
        print(f"  --- 3B. {phase_name} 철거 작업 (대체 후 잔여 대상) ---")
        target_demolished_cumulative_current = min(round(total_original_replaceable_count * p_cumulative_demolition_ratio_curr), total_original_replaceable_count)
        if p_cumulative_demolition_ratio_curr >= 1.0: target_demolished_cumulative_current = total_original_replaceable_count
        
        where_already_demolished_total = f"{config.FIELD_NODE_STATUS} = '{config.STATUS_DEMOLISHED}'"
        num_already_demolished_total = 0
        temp_total_dem_check = arcpy.management.MakeFeatureLayer(temp_output_path, f"total_dem_check_{timestamp_step3}_B", where_already_demolished_total); temp_items_step3.append(temp_total_dem_check)
        num_already_demolished_total = int(arcpy.management.GetCount(temp_total_dem_check).getOutput(0))

        num_to_demolish_this_step = max(0, target_demolished_cumulative_current - num_already_demolished_total)
        print(f"    누적 철거 목표 {target_demolished_cumulative_current}개, 현재까지 총 철거된 수 {num_already_demolished_total}개")

        where_still_original_urban_for_demolition = f"({status_check_field_delim} = '{config.STATUS_ORIGINAL_LOW_PRI}' OR {status_check_field_delim} = '{config.STATUS_ORIGINAL_HIGH_PRI}')"
        available_slots_for_demolition_layer = arcpy.management.MakeFeatureLayer(temp_output_path, f"available_slots_dem_{timestamp_step3}").getOutput(0); temp_items_step3.append(available_slots_for_demolition_layer)
        arcpy.management.SelectLayerByAttribute(available_slots_for_demolition_layer, "NEW_SELECTION", where_still_original_urban_for_demolition)
        current_demolishable_slots_count = int(arcpy.management.GetCount(available_slots_for_demolition_layer).getOutput(0))

        actual_num_to_demolish_this_step = min(num_to_demolish_this_step, current_demolishable_slots_count)
        print(f"    현재 철거 가능 상태 노드 수 (대체 후 남은 Original Urban): {current_demolishable_slots_count}개")
        print(f"    이번 단계 추가 철거 목표 수: {actual_num_to_demolish_this_step}개")

        if actual_num_to_demolish_this_step > 0:
            demolition_candidates_this_step = []; sql_clause_dem = (None, f"ORDER BY {order_by_field_dem} ASC"); print(f"        철거 대상 선정 SearchCursor (정렬: {order_by_field_dem} ASC)...")
            try:
                with arcpy.da.SearchCursor(available_slots_for_demolition_layer, [config.FIELD_UNIQUE_ID, order_by_field_dem], sql_clause=sql_clause_dem) as cursor:
                    count = 0;
                    for row in cursor:
                        if count < actual_num_to_demolish_this_step: demolition_candidates_this_step.append(row[0]); count += 1
                        else: break
            except Exception as e_dem_srch: print(f"        오류: 철거 대상 검색 실패 - {e_dem_srch}."); demolition_candidates_this_step = []
            ids_to_demolish = demolition_candidates_this_step; demolish_ids_str = ','.join(map(str, ids_to_demolish)); print(f"        철거 대상 ID {len(ids_to_demolish)}개 선정.")
            if demolish_ids_str:
                where_clause_demolish = f"{config.FIELD_UNIQUE_ID} IN ({demolish_ids_str})"; demolish_update_count = 0; print("        철거 UpdateCursor 실행...")
                try:
                    time.sleep(0.5);
                    with arcpy.da.UpdateCursor(temp_output_path, [config.FIELD_NODE_STATUS, config.FIELD_NODE_TYPE_LABEL], where_clause=where_clause_demolish) as cursor:
                        for row in cursor:
                            if row[0] != config.STATUS_DEMOLISHED: row[0] = config.STATUS_DEMOLISHED; row[1] = config.DEMOLISHED_LABEL; cursor.updateRow(row); demolish_update_count += 1
                    print(f"    {demolish_update_count}개 노드 상태 '{config.STATUS_DEMOLISHED}', 라벨 '{config.DEMOLISHED_LABEL}' 업데이트."); newly_demolished_ids.update(ids_to_demolish)
                except Exception as dem_err: print(f"        오류: 철거 UpdateCursor 실패 - {dem_err}")
            else: print("    선정된 철거 대상 ID 없음.")
        else: print("    이번 단계 추가 철거 대상 없음."); time.sleep(0.5)

        # --- 3C. 최종 포인트 결과에 목축지 분류 필드 추가 ---
        print(f"    ({phase_name}) 최종 포인트 결과에 목축지 분류 필드 추가 중...")
        current_output_fields = [f.name for f in arcpy.ListFields(temp_output_path)]
        if config.FIELD_IS_GRAZING not in current_output_fields: arcpy.management.AddField(temp_output_path, config.FIELD_IS_GRAZING, "TEXT", field_length=10)
        if config.FIELD_GRAZING_TYPE not in current_output_fields: arcpy.management.AddField(temp_output_path, config.FIELD_GRAZING_TYPE, "TEXT", field_length=50)
        fields_for_grazing_class = [] ; l3_code_idx = -1
        if config.FIELD_L3_CODE not in current_output_fields: print(f"    경고: 포인트 결과에 {config.FIELD_L3_CODE} 필드 없음. 분류 정확도↓."); fields_for_grazing_class = [config.FIELD_NODE_STATUS, config.FIELD_NODE_TYPE_LABEL, config.FIELD_IS_GRAZING, config.FIELD_GRAZING_TYPE]
        else: fields_for_grazing_class = [config.FIELD_NODE_STATUS, config.FIELD_NODE_TYPE_LABEL, config.FIELD_L3_CODE, config.FIELD_IS_GRAZING, config.FIELD_GRAZING_TYPE]; l3_code_idx = 2
        with arcpy.da.UpdateCursor(temp_output_path, fields_for_grazing_class) as u_cursor:
            for row in u_cursor:
                status, type_label = row[0], row[1]; l3_code_val = row[l3_code_idx] if l3_code_idx != -1 and l3_code_idx < len(row) else None
                current_is_grazing = "No"; current_grazing_type = "NonGrazing"
                if status == config.STATUS_DEMOLISHED: current_is_grazing = "Yes"; current_grazing_type = "DemolishedToGrazing"
                elif status == config.STATUS_REPLACED:
                    if type_label in ["LS", "NGRASS_Grazing"]: current_is_grazing = "Yes"; current_grazing_type = "EvolvedToGrazing"
                    elif config.EVOLVED_TO_L3_MAPPING.get(type_label) in config.GRAZING_L3_CODES: current_is_grazing = "Yes"; current_grazing_type = "EvolvedToGrazing"
                    elif config.EVOLVED_TO_L3_MAPPING.get(type_label) in config.FOREST_L3_CODES: current_grazing_type = "EvolvedToForest"
                elif status == config.STATUS_ORIGINAL_NONURBAN:
                    if l3_code_val in config.FOREST_L3_CODES: current_grazing_type = "OriginalForest"
                    elif l3_code_val in config.BASE_GRAZING_CODES: current_is_grazing = "Yes"; current_grazing_type = "OriginalGrazing"
                row[fields_for_grazing_class.index(config.FIELD_IS_GRAZING)] = current_is_grazing
                row[fields_for_grazing_class.index(config.FIELD_GRAZING_TYPE)] = current_grazing_type
                u_cursor.updateRow(row)
        print(f"    ({phase_name}) 목축지 분류 필드 업데이트 완료.")

        # --- 3D. 최종 결과물 GDB에 저장 ---
        if arcpy.Exists(output_path): arcpy.management.Delete(output_path)
        arcpy.management.CopyFeatures(temp_output_path, output_path)
        print(f"단계 3 ({phase_name}) 완료. 최종 결과 저장: {output_path}")
        
        processed_source_node_ids.update(selected_new_source_oids)
        return output_path, processed_source_node_ids
        
    except arcpy.ExecuteError: print(f"ArcGIS Error in Step 3 ({phase_name}):\n{arcpy.GetMessages(2)}"); traceback.print_exc(); raise
    except Exception as e: print(f"Non-ArcGIS Error in Step 3 ({phase_name}): {e}"); traceback.print_exc(); raise
    finally:
        print(f"  단계 3 ({phase_name}) 내부 임시 데이터 정리...");
        for item in temp_items_step3:
            if item and arcpy.Exists(item):
                try: arcpy.management.Delete(item)
                except Exception as del_e_step3: print(f"    임시 삭제 오류 무시 (단계 3 finally): {del_e_step3}")