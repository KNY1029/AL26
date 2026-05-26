import pandas as pd
import os
import urllib.request
import time

# [수정된 부분] 폴더 이름을 zinc_dbt로 변경
folder_name = "zinc_dbt"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# 1. 파일 링크 불러오기
# pandas의 read_csv를 사용하여 파일 데이터를 읽어옵니다 [2].
uri_df = pd.read_csv("ZINC-downloader-2D-txt.uri", header=None)

# [수정된 부분] 테스트를 위해 리스트 슬라이싱([:10])을 사용하여 첫 10개만 가져옵니다.
download_links = uri_df[0].tolist()[:10] 

total_files = len(download_links)
print(f"총 {total_files}개의 파일 다운로드 테스트를 시작합니다...")

max_retries = 30

while True:
    all_downloaded = True 
    
    for i, link in enumerate(download_links, 1):
        file_name = link.split('/')[-1] 
        save_path = os.path.join(folder_name, file_name)
        temp_path = save_path + ".part"
        
        # [수정된 부분] 기존 파일이 존재하는지 검사해서 건너뛰는(continue) 코드를 삭제했습니다.
        # 따라서 폴더에 파일이 있어도 무조건 처음부터 다운로드를 시도합니다.
        
        all_downloaded = False 
        
        for attempt in range(max_retries):
            try:
                headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                            "Connection": "keep-alive",
                            "Accept": "*/*"
                        }
                req = urllib.request.Request(link, headers=headers)
                
                with urllib.request.urlopen(req, timeout=60) as response, open(temp_path, 'wb') as out_file:
                    print(f"  -> [{i}/{total_files}] {file_name} 열심히 수신 중", end="", flush=True)
                    chunk_count = 0
                    while True:
                        chunk = response.read(1024 * 1024) 
                        if not chunk: 
                            break
                        out_file.write(chunk)
                        chunk_count += 1
                        if chunk_count % 50 == 0:
                            print(".", end="", flush=True)
                            
                print("\n")
                os.replace(temp_path, save_path)
                print(f"[{i}/{total_files}] {file_name} 다운로드 완료")
                
                # 성공 시 재시도 루프 탈출
                break 
                
            except Exception as e:
                print(f"\n  -> [{i}/{total_files}] {file_name} 실패 (시도 {attempt+1}/{max_retries}) - 에러 발생! 원인: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                if attempt == max_retries - 1:
                    print(f"  -> {file_name} 모두 실패. 포기하고 일단 다음 파일로 넘어갑니다.")
                    break 
                time.sleep(attempt) 
    
    if all_downloaded:
        print("\n=== 10개 파일 다운로드 테스트가 완벽하게 끝났습니다! ===")
        break 
    else:
        # 파일이 누락되었을 경우 다시 시도하는 기존 로직 유지 [1]
        print("\n=== 누락된 파일이 있어 처음부터 다시 검증을 시작합니다. ===\n")
        time.sleep(5) 