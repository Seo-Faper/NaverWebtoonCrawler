import sqlite3
import requests
import random
import sys
from tqdm import tqdm

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
    def __init__(self, title_id):
        super().__init__()
        self.title_id = title_id
        self.base_url = "https://comic.naver.com/api/article/list?titleId={}&page={}&sort=ASC".format(title_id, "{}")
        self.set_random_user_agent()
        self.conn = sqlite3.connect('webtoons.db')
        self.create_table()

    def create_table(self):
        table_name = f"webtoon_{self.title_id}"
        with self.conn:
            self.conn.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                                 (no INTEGER PRIMARY KEY,
                                  thumbnailUrl TEXT,
                                  subtitle TEXT,
                                  detailUrl TEXT)''')

    def insert_data(self, no, thumbnailUrl, subtitle, detailUrl):
        table_name = f"webtoon_{self.title_id}"
        with self.conn:
            self.conn.execute(f'INSERT INTO {table_name} (no, thumbnailUrl, subtitle, detailUrl) VALUES (?, ?, ?, ?)',
                              (no, thumbnailUrl, subtitle, detailUrl))

    def parse_page(self, page_num):
        target_url = self.base_url.format(page_num)
        res = requests.get(target_url, headers=self.headers).json()
        total_count = res['totalCount']
        page_count = (total_count + 19) // 20
        page_num = int(page_num)
        
        with tqdm(total=page_count, desc="Progress", unit="page") as pbar:
            while page_num <= page_count:
                target_url = self.base_url.format(page_num)
                res = requests.get(target_url, headers=self.headers).json()
                for article in res['articleList']:
                    no = article['no']
                    thumbnailUrl = article['thumbnailUrl']
                    subtitle = article['subtitle']
                    detailUrl = 'https://comic.naver.com/webtoon/detail?titleId={}&no={}'.format(self.title_id, no)
                    self.insert_data(no, thumbnailUrl, subtitle, detailUrl)
                page_num += 1
                pbar.update(1)
        print(f"페이지 {page_count} 개가 저장되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
    사용법 : python NaverWebtoonTitleCrawler.py <titleId>
              
    예시 : python NaverWebtoonTitleCrawler.py 641253
        """)
    else:
        titleId = sys.argv[1]
        naver = NaverWebtoonTitle(titleId)
        naver.parse_page("1")
