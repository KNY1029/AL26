import pandas as pd
import glob
import time
import bisect
from mpi4py import MPI

# ==========================================
# 이진 탐색(Binary Search)용 함수 정의 [5]
# ==========================================
def binary_search(sorted_list, target):
    idx = bisect.bisect_left(sorted_list, target)
    return idx < len(sorted_list) and sorted_list[idx] == target

# ==========================================
# MPI 통신 초기화
# ==========================================
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# 1. 농약 데이터 로드 및 3가지 형태의 비교군 준비 [1, 2]
# 주의: PubChem_Agrochemical.csv 파일이 실행 폴더에 있어야 합니다.
pesticides = pd.read_csv("PubChem_Agrochemical.csv")
pesticides_smi = pesticides['smiles'].to_list()       # 선형 탐색용 리스트 [2]
pesticides_binary = sorted(pesticides_smi)            # 이진 탐색용 정렬된 리스트 [3]
pesticides_hash = set(pesticides_smi)                 # 해시 탐색용 해시 테이블(Set) [4]

# 2. 개인 PC의 ZINC DB 파일 경로 설정 및 분배 (이전 대화 내용 반영)
folder_path = r"C:\Users\DS\ny\AL\zinc_db\*.txt"
zinc_files = sorted(glob.glob(folder_path))

if rank == 0:
    print(f"총 {len(zinc_files)}개의 파일 탐색을 {size}개의 코어로 시작합니다...\n")

# 코어 개수만큼 파일을 N등분하여 나누어 가짐
my_files = zinc_files[rank::size]

# (외부 지식: 코어 간 속도 차이를 맞추기 위해 측정 전 대기시키는 기능)
comm.Barrier() 

# ==========================================
# [TEST 1] Linear Search (선형 탐색) [2]
# ==========================================
start_time = time.time()
local_lin_count = 0
for f in my_files:
    try:
        zinc = pd.read_csv(f, sep='\t', usecols=['smiles'])
        for smi in zinc['smiles']:
            if smi in pesticides_smi: # 일일이 비교
                local_lin_count += 1
    except:
        pass
comm.Barrier()
lin_time = time.time() - start_time
total_lin = comm.reduce(local_lin_count, op=MPI.SUM, root=0)

# ==========================================
# [TEST 2] Binary Search (이진 탐색) [3]
# ==========================================
start_time = time.time()
local_bin_count = 0
for f in my_files:
    try:
        zinc = pd.read_csv(f, sep='\t', usecols=['smiles'])
        for smi in zinc['smiles']:
            if binary_search(pesticides_binary, smi): # 반씩 잘라가며 탐색 [5]
                local_bin_count += 1
    except:
        pass
comm.Barrier()
bin_time = time.time() - start_time
total_bin = comm.reduce(local_bin_count, op=MPI.SUM, root=0)

# ==========================================
# [TEST 3] Hash Search (해시 탐색) [4]
# ==========================================
start_time = time.time()
local_hash_count = 0
for f in my_files:
    try:
        zinc = pd.read_csv(f, sep='\t', usecols=['smiles'])
        for smi in zinc['smiles']:
            if smi in pesticides_hash: # 해시 테이블에서 즉시 탐색 [4]
                local_hash_count += 1
    except:
        pass
comm.Barrier()
hash_time = time.time() - start_time
total_hash = comm.reduce(local_hash_count, op=MPI.SUM, root=0)

# ==========================================
# 3. 결과 출력 및 파일 저장 (0번 코어 대장이 수행)
# ==========================================
if rank == 0:
    # 화면 및 파일에 출력할 결과 텍스트 포맷 구성 (외부 지식)
    result_text = (
        "==========================================\n"
        "   [ZINC DB 농약 탐색 알고리즘 성능 비교]\n"
        "==========================================\n"
        f"1. Linear Search (선형 탐색): {total_lin}개 발견 / {lin_time:.2f}초 소요\n"
        f"2. Binary Search (이진 탐색): {total_bin}개 발견 / {bin_time:.2f}초 소요\n"
        f"3. Hash Search   (해시 탐색): {total_hash}개 발견 / {hash_time:.2f}초 소요\n"
        "==========================================\n"
    )
    
    # 1. 화면에 출력
    print(result_text)
    
    # 2. 파일로 저장 (외부 지식: 파이썬의 기본 파일 쓰기 기능 활용)
    with open("search_results.txt", "w", encoding="utf-8") as file:
        file.write(result_text)
    print("성능 분석 결과가 'search_results.txt' 파일로 무사히 저장되었습니다!")