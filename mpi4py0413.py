from mpi4py import MPI
import pandas as pd
import glob
import time
import os

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    start_time = time.time()

# 1. 파일 분배
all_files = sorted(glob.glob('./zinc_db/*.txt'))

# [수정포인트 1] 0번 코어가 총 몇 개의 파일을 탐색하는지 화면에 출력
if rank == 0:
    print(f"\n[시스템] 탐색을 시작합니다. 총 탐색 대상 파일 개수: {len(all_files)}개")

my_files = all_files[rank::size]

local_top5_list = []
for f in my_files:
    try:
        df = pd.read_csv(f, sep='\t', usecols=['smiles', 'logp'])
        
        # [수정포인트 2] 이 물질이 도대체 어느 파일에서 나왔는지 '출처(source_file)' 열을 추가
        df['source_file'] = os.path.basename(f) 
        
        local_top5_list.append(df.nsmallest(5, 'logp'))
    except:
        continue

# 각 일꾼의 하위 5개 취합
if local_top5_list:
    my_best_5 = pd.concat(local_top5_list).nsmallest(5, 'logp')
else:
    my_best_5 = pd.DataFrame(columns=['smiles', 'logp', 'source_file'])

# 2. 모든 결과를 Rank 0으로 수집
all_reports = comm.gather(my_best_5, root=0)

# 3. 최종 보고
if rank == 0:
    final_df = pd.concat(all_reports, ignore_index=True)
    global_top5 = final_df.nsmallest(5, 'logp').reset_index(drop=True)
    
    print("\n=============================================")
    print("      --- 최종 분석 결과 ---")
    print(global_top5) # 결과 출력 시 smiles, logp와 함께 출처 파일명도 출력됨
    print("=============================================")
    print(f"분석 소요 시간: {time.time() - start_time:.4f} sec")