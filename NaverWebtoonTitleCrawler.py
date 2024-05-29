import sqlite3
import requests
import random
import sys
from tqdm import tqdm
import re
import time, random

class InfoCrawler():
    def __init__(self):
        self.base_url = ""
        self.headers = {}
        self.user_agent_list = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            # Firefox
            'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
            'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
            'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
        ]

    def set_random_user_agent(self):
        user_agent = random.choice(self.user_agent_list)
        self.headers["User-Agent"] = user_agent
        return user_agent

class NaverWebtoonTitle(InfoCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://comic.naver.com/api/article/list?titleId={}&page={}&sort=ASC"
        self.set_random_user_agent()
        self.conn = sqlite3.connect('webtoons.db')

    def create_table(self, title_id):
        table_name = f"webtoon_{title_id}"
        with self.conn:
            self.conn.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                                 (no INTEGER PRIMARY KEY,
                                  thumbnailUrl TEXT,
                                  subtitle TEXT,
                                  detailUrl TEXT
                                  )''')

    def insert_data(self, title_id, no, thumbnailUrl, subtitle, detailUrl):
        table_name = f"webtoon_{title_id}"
        with self.conn:
            self.conn.execute(f'INSERT INTO {table_name} (no, thumbnailUrl, subtitle, detailUrl) VALUES (?, ?, ?, ?)',
                              (no, thumbnailUrl, subtitle, detailUrl))

    def week_parse(self, week):
        url = f"https://comic.naver.com/api/webtoon/titlelist/weekday?week={week}&order=user"
        res = requests.get(url, headers=self.headers).json()
       
        for data in res['titleList']:
          print(str(data['titleName'])+" 추출 시작")
          title_id = str(data['titleId'])+"_"+str(week)
          self.create_table(str(data['titleId'])+"_"+str(week))  
          self.parse_page("1",title_id)

    def parse_page(self, page_num, title_id): 
        try:
            numbers = re.findall(r'\d+', title_id)
            result = ''.join(numbers)
            target_url = self.base_url.format(result, page_num)
            res = requests.get(target_url, headers=self.headers).json()
            total_count = res['totalCount']
            
            page_count = (total_count + 19) // 20
            page_num = int(page_num)
            
            with tqdm(total=page_count, desc="Progress", unit="page") as pbar:
                while page_num <= page_count:
                    target_url = self.base_url.format(result, page_num)
                    res = requests.get(target_url, headers=self.headers).json()
                    for article in res['articleList']:
                        no = article['no']
                        thumbnailUrl = article['thumbnailUrl']
                        subtitle = article['subtitle']
                        detailUrl = f'https://comic.naver.com/webtoon/detail?titleId={result}&no={no}'
                        
                        self.insert_data(title_id, no, thumbnailUrl, subtitle, detailUrl)
                    page_num += 1
                    pbar.update(1)
            print(f"페이지 {page_count} 개가 저장되었습니다.")
        except:
            print("로그인이 필요한 웹툰입니다.")
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
    사용법 : python NaverWebtoonTitleCrawler.py <titleId>
    옵션 : 
        요일별 웹툰 추출
            -w <요일> 
              
        웹툰 본문 이미지 추출
            -f <titleId>

    예시 : python NaverWebtoonTitleCrawler.py -f 641253
           python NaverWebtoonTItleCrawler.py -w mon|tue|wed|thu|fri|sat|sun
        """)
    elif len(sys.argv) == 3 and sys.argv[1] == '-w':
        week = sys.argv[2]
        naver = NaverWebtoonTitle()
        naver.week_parse(week)
    else:
        titleId = sys.argv[2]

        naver = NaverWebtoonTitle()
        naver.create_table(titleId)
        naver.parse_page("1", titleId)
