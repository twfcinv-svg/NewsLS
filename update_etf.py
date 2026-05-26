import json
import os
from datetime import datetime

# 設定存檔名稱
HISTORY_FILE = 'etf_news_history.json'

def load_history():
    """讀取既有的 ETF 新聞歷史紀錄"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    """將資料存回 JSON，並依據分數(score)由高至低排序"""
    history = sorted(history, key=lambda x: x.get('score', 0), reverse=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def get_new_data():
    """
    【請將這裡替換成您實際的爬蟲程式碼】
    這裡以模擬資料作為測試範例
    """
    return [
        {"title": "00929「1天就飆6.35%」漲幅超過整年！投資達人：活躍期才剛開始", "url": "https://finance.ettoday.net/news/3172261", "score": 3.5, "source": "ETtoday"},
        {"title": "ETF「冷門黑馬」暴漲近80% 超狂經理人被挖出！", "url": "https://finance.ettoday.net/news/3172287", "score": 2.0, "source": "ETtoday"},
        {"title": "迎戰台股高檔震盪 主動式ETF加入掩護性買權", "url": "https://tw.stock.yahoo.com/news/123", "score": -1.5, "source": "Yahoo股市"}
    ]

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始執行 ETF 新聞更新...")
    
    history = load_history()
    new_data = get_new_data()
    
    # 建立目前已存在的網址集合 (Set)，加速比對速度
    existing_urls = {item['url'] for item in history}
    added_count = 0
    
    # 進行網址去重比對
    for news in new_data:
        if news['url'] not in existing_urls:
            history.append(news)
            existing_urls.add(news['url'])
            added_count += 1
            
    # 存檔
    save_history(history)
    print(f"✅ 更新完成！本次新增 {added_count} 筆，歷史庫共 {len(history)} 筆。")

if __name__ == "__main__":
    main()
