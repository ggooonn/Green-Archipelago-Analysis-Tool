# -*- coding: utf-8 -*-
"""
GAC System Prototype 설정 파일

이 파일은 시뮬레이션에 필요한 모든 사용자 설정 변수를 중앙에서 관리합니다.
분석 로직을 직접 수정하지 않고 이 파일의 값만 변경하여 다양한 시나리오를 실행할 수 있습니다.
"""

# --- 1. ArcGIS Pro 프로젝트 및 지오데이터베이스 설정 ---
# 결과물이 저장될 출력 지오데이터베이스(GDB) 경로
OUTPUT_GDB = r"F:\Architecture(9)\1주차\GAZA\GIS\MyProject1\MyProject1.gdb"

# 현재 ArcGIS Pro 활성 맵에 있는 입력 레이어 이름
LC_LAYER_NAME = "LandCover_Polygon"
GB_LAYER_NAME = "Greenbelt_Boundary"
ISLAND_LAYER_NAME = "Greenbelt_Islands"

# --- 2. GIS 필드 이름 ---
# 스크립트 전반에서 사용되는 데이터 필드(컬럼) 이름입니다.
# GIS 데이터의 필드명이 변경되면 여기만 수정하면 됩니다.
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

# --- 3. 시뮬레이션 시나리오 파라미터 ---
# 각 단계별 시뮬레이션 연도 정의
SCENARIO_PHASES = {"Phase1": 2050, "Phase2": 2075, "Phase3": 2100}

# 이주(신규 토지 이용 생성) 및 철거에 대한 누적 비율
# 예: 2050년까지 전체 잠재력의 50%, 2075년까지 80%를 실현
CUMULATIVE_MIGRATION_RATIO = {2050: 0.50, 2075: 0.80, 2100: 1.00}
CUMULATIVE_DEMOLITION_RATIO = {2050: 0.50, 2075: 0.80, 2100: 1.00}

# --- 4. 토지 전환 로직 ---
# "압축률(CompressionFactor)"는 하나의 고효율 'GAC 모듈'을 만드는 데
# 필요한 기존 토지 단위의 수를 나타냅니다.
# 예: 기존 AG-FC 토지 50단위가 1개의 신규 GAC 모듈로 압축됨
COMPRESSION_FACTORS = {
    "AG-FC": 50,
    "AG-LV": 100,
    "AG-FV": 100,
    "LS": 2,
    "FR": 30,
    "NGRASS_Grazing": 1
}

# 신규 'GAC 모듈'의 목표 카테고리
EVOLVED_CATEGORIES = list(COMPRESSION_FACTORS.keys())

# 신규 Evolved Category를 GIS 심볼로 표현하기 위한 대표 L3_CODE 매핑
EVOLVED_TO_L3_MAPPING = {
    "AG-FC": "211",
    "AG-LV": "221",
    "AG-FV": "241",
    "LS": "251",
    "FR": "331",
    "NGRASS_Grazing": "411"
}

# --- 5. 토지피복코드(L3_CODE) 정의 ---
# 대한민국 환경부 토지피복지도 세분류 기준
SOURCE_L3_CODES = ['211', '212', '221', '222', '231', '241', '251', '311', '321', '331', '411', '423', '623']
LOW_PRIORITY_URBAN_CODES = ['111', '112', '141', '161', '162', '163']
HIGH_PRIORITY_URBAN_CODES = ['121', '131', '132']
REPLACEABLE_URBAN_L3_CODES = LOW_PRIORITY_URBAN_CODES + HIGH_PRIORITY_URBAN_CODES
INDUSTRIAL_L3_CODES = ['121']
TRANSPORT_L3_CODES = ['151', '152', '153', '154', '155']
FOREST_L3_CODES = ['311', '321', '331']

# --- 6. 입지 적합도 지수(SSI) 가중치 ---
# 대체 대상 도시 지역의 우선순위를 계산할 때 각 요소의 중요도를 결정
WEIGHT_STATUS = 0.5         # 고밀도/상업 vs 저밀도/주거 지역
WEIGHT_INV_CEN_DIST = 0.3   # 섬 중심까지의 역거리 (가까울수록 높음)
WEIGHT_INV_IND_DIST = 0.2   # 공업지역까지의 역거리 (가까울수록 높음)

# --- 7. 내부 스크립트 상수 ---
# 상태 필드에 사용될 값 정의
STATUS_REPLACED = "Replaced"
STATUS_DEMOLISHED = "Demolished"
STATUS_ORIGINAL_LOW_PRI = "Original_Urban_LowPri"
STATUS_ORIGINAL_HIGH_PRI = "Original_Urban_HighPri"
STATUS_ORIGINAL_TRANSPORT = "Original_Transport"
STATUS_ORIGINAL_NONURBAN = "Original_NonUrban_Island"
DEMOLISHED_LABEL = "Demolished_To_Grazing"

# 거리 계산 시 기본값
DEFAULT_LARGE_DISTANCE = 1000.0