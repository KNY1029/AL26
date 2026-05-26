from mpi4py import MPI
import pandas as pd
import glob
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    start_time = time.time()

# 1. 파일 분배 및 로컬 분석 (기존 로직)
all_files = sorted(glob.glob('./zinc_db/*.txt'))
my_files = all_files[rank::size] 

local_top5_list = []
for f in my_files:
    try:
        df = pd.read_csv(f, sep='\t', usecols=['smiles', 'logp'])
        local_top5_list.append(df.nsmallest(5, 'logp'))
    except:
        continue

# 각 일꾼의 하위 5개 취합
if local_top5_list:
    my_best_5 = pd.concat(local_top5_list).nsmallest(5, 'logp')
else:
    my_best_5 = pd.DataFrame(columns=['smiles', 'logp'])

# 2. 모든 결과를 Rank 0으로 수집
all_reports = comm.gather(my_best_5, root=0)

# 3. 최종 보고 (Rank 0 출력 스타일 수정)
if rank == 0:
    final_df = pd.concat(all_reports, ignore_index=True)
    global_top5 = final_df.nsmallest(5, 'logp').reset_index(drop=True)
    
    print("\n" + "="*45)
    print("      --- 최종 분석 결과 ---")
    
    for i, row in global_top5.iterrows():
        print(f"[{i+1}]")
        print(f"SMILES: {row['smiles']}")
        print(f"Lowest LogP: {row['logp']}")
        if i < 4: # 마지막 항목이 아니면 구분선 추가
            print("-" * 45)
            
    print("="*45)
    
    end_time = time.time()
    print(f"분석 소요 시간: {end_time - start_time:.4f} sec")