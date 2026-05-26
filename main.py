import feedparser
from datetime import datetime, timedelta, timezone
import re
import random
import time
import math
from collections import Counter
import csv  # 新增：用於存檔
import os   # 新增：用於判斷檔案是否存在

# ===========================
# 1. 究極新聞來源
# ===========================
RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       
    "https://tw.stock.yahoo.com/rss?category=tech",            
    "https://tw.stock.yahoo.com/rss?category=tradtional",      
    "https://tw.stock.yahoo.com/rss?category=finance",         
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    
    "https://tw.stock.yahoo.com/rss?category=research",        
    "https://news.cnyes.com/rss/cnyes/stock",                  
    "https://news.cnyes.com/rss/cnyes/all",                    
    "https://news.cnyes.com/rss/cnyes/industry",               
    "https://money.udn.com/rssfeed/news/1001/5591",            
    "https://money.udn.com/rssfeed/news/1001/5590",            
    "https://ctee.com.tw/feed",                                
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB010000", 
    "https://www.chinatimes.com/rss/realtimenews-finance.xml", 
    "https://news.ltn.com.tw/rss/business.xml",                
    "https://feeds.feedburner.com/ettoday/finance",            
    "https://rss.ptt.cc/Stock.xml",
]

# (關鍵字設定與 SENTIMENT_DICT 保持不變，為節省篇幅省略顯示)
STOCK_KEYWORDS = ["台積", "鴻海", "聯發科", "廣達", "緯創", "技嘉", "中華電", "富邦金", "國泰金", "台塑", "南亞", "力積電", "華通", "神盾", "安國", "智原", "創意", "世芯", "緯穎", "奇鋐", "雙鴻", "建準", "聯電", "華碩", "宏碁", "微星", "長榮", "陽明", "萬海", "長榮航", "華航", "亞翔", "中興電", "華城", "士電", "群創", "友達", "彩晶", "聯詠", "瑞昱", "信驊", "大立光", "玉晶光", "欣興", "南電", "景碩", "CoWoS", "AI", "散熱", "IP", "IC", "PCB", "被動元件", "記憶體", "面板", "網通", "低軌", "電動車", "2330", "2317", "2454", "3008", "3035", "3037", "2382", "3231", "2603", "2609", "2615"]
INVESTMENT_KEYWORDS = STOCK_KEYWORDS + ["股", "債", "券", "金控", "銀行", "ETF", "基金", "外資", "法人", "投信", "自營", "主力", "買超", "賣超", "多頭", "空頭", "漲", "跌", "盤", "指數", "加權", "櫃買", "期貨", "選擇權", "道瓊", "那斯達克", "標普", "費半", "ADR", "匯率", "美元", "央行", "升息", "降息", "通膨", "CPI", "營收", "獲利", "EPS", "盈餘", "毛利", "股利", "配息", "除權", "填息", "殖利率", "法說", "季報", "年報", "月報", "財報", "展望", "目標價", "評等", "庫存", "接單", "訂單", "產能", "輝達", "行情", "走勢", "動態", "概況", "預估", "預測", "分析", "觀點", "研究", "報告", "供應鏈", "需求", "報價", "擴產", "擴廠", "設廠", "資本支出", "景氣", "復甦", "衰退", "風險", "避險"]
EXCLUDE_KEYWORDS = ["徵才", "招募", "求職", "面試", "員工", "薪資", "年終", "分紅", "尾牙", "開缺", "工程師", "人才", "藝人", "網紅", "男星", "女星", "豪宅", "理財術", "存股術", "買房", "房貸", "後悔", "翻身", "致富", "百萬", "油價", "汽油", "柴油", "加油", "開車", "每公升", "調漲", "調降", "路況", "氣象", "颱風", "放假", "詐騙", "假冒", "專家傳授", "教你", "懶人包", "閒聊", "公告", "新聞", "標的"]
MACRO_KEYWORDS = ["大盤", "台股", "加權", "指數", "櫃買", "道瓊", "那斯達克", "標普", "費半", "三大法人", "投信", "外資", "央行", "聯準會", "Fed", "升息", "降息", "通膨", "CPI", "匯率", "新台幣", "美元", "美股", "亞股", "歐股", "盤前", "盤後", "收盤", "開盤", "行情", "龍年", "蛇年", "封關", "開紅盤", "台指期"]
SENTIMENT_DICT = {"bull_strong": ["漲停", "飆", "噴出", "大漲", "創高", "新高", "完勝", "大賺", "搶手", "暴漲", "報喜", "噴發", "熱錢", "軋空", "避風港", "抗跌", "逢低", "布局", "搶進", "包地"], "bull_normal": ["漲", "揚", "攻", "旺", "強", "升", "紅", "買超", "加碼", "利多", "樂觀", "成長", "填息", "進補", "受惠", "復甦", "點火", "獲利", "看好", "目標價", "法說", "發威", "撐盤", "收紅", "擴產", "防禦", "高股息", "護盤", "契作", "卡位", "站買方", "撐腰"], "bull_weak": ["微漲", "小漲", "回穩", "反彈", "收斂", "趨緩", "收復", "站上", "有守"], "bear_strong": ["跌停", "崩", "暴跌", "重挫", "破底", "殺盤", "跳水", "大跌", "重摔", "血洗", "股災", "慎防", "變盤"], "bear_normal": ["跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", "利空", "保守", "衰退", "貼息", "縮水", "砍單", "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "疑慮", "下修", "虧損", "賣壓", "收黑", "裁員", "留意", "回檔", "震盪", "修正", "獲利了結", "春節", "過年", "長假", "觀望"], "bear_weak": ["微跌", "小跌", "整理", "疲軟"], "negation": ["不", "未", "無", "非", "免", "抗", "防", "止", "終止", "收斂", "無懼"]}

def clean_title(title):
    title = re.sub(r" - Yahoo.*", "", title); title = re.sub(r" - 鉅亨.*", "", title); title = re.sub(r" - 經濟.*", "", title); title = re.sub(r"\(.*?\)", "", title)
    return title.strip()

def identify_source(link):
    if "yahoo" in link: return "Yahoo股市"
    if "cnyes" in link: return "鉅亨網"
    if "udn" in link: return "經濟日報"
    if "moneydj" in link: return "MoneyDJ"
    if "ltn" in link: return "自由財經"
    if "chinatimes" in link: return "中時"
    if "ettoday" in link: return "ETtoday"
    if "ptt.cc" in link: return "PTT Stock"
    if "ctee" in link: return "工商時報"
    return "網路新聞"

def filter_news(title):
    for bad_word in EXCLUDE_KEYWORDS:
        if bad_word in title: return False
    for good_word in INVESTMENT_KEYWORDS:
        if good_word in title: return True
    return False

def calculate_sentiment_score(title):
    score = 0
    def is_negated(keyword, text):
        idx = text.find(keyword)
        if idx > 0:
            prefix = text[max(0, idx-2):idx]
            for neg in SENTIMENT_DICT["negation"]:
                if neg in prefix: return True
        return False
    # (權重計算邏輯省略，同原程式)
    for w in SENTIMENT_DICT["bull_strong"]: if w in title: score += 2.5 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_normal"]: if w in title: score += 1.0 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_weak"]: if w in title: score += 0.5
    for w in SENTIMENT_DICT["bear_strong"]: if w in title: score -= 2.5 if not is_negated(w, title) else -2.0
    for w in SENTIMENT_DICT["bear_normal"]: if w in title: score -= 1.5 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bear_weak"]: if w in title: score -= 0.5
    return round(score, 1)

def is_individual_stock(title):
    for kw in STOCK_KEYWORDS: if kw in title: return True
    for kw in MACRO_KEYWORDS: if kw in title: return False
    return True

def generate_wordcloud_html(all_titles):
    # (詞雲邏輯省略，同原程式)
    # ...
    return ""

def main():
    print("啟動 V15 智慧校正與 CSV 歸檔...")
    all_news = []
    seen_links = set(); seen_titles = set(); total_raw_count = 0; skipped_old_count = 0; skipped_dup_count = 0
    time_threshold = datetime.utcnow() - timedelta(hours=12)

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                total_raw_count += 1
                if entry.link in seen_links: continue
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if published_dt < time_threshold: skipped_old_count += 1; continue
                title = clean_title(entry.title)
                title_fingerprint = re.sub(r"[^\w]", "", title)
                if title_fingerprint in seen_titles: skipped_dup_count += 1; continue
                if not filter_news(title): continue
                score = calculate_sentiment_score(title)
                if score == 0: continue
                seen_links.add(entry.link); seen_titles.add(title_fingerprint)
                news_type = "individual" if is_individual_stock(title) else "macro"
                all_news.append({"title": title, "link": entry.link, "source": identify_source(entry.link), "score": score, "type": news_type, "color": "#b71c1c" if score > 0 else "#1b5e20", "bg": "#fff5f5" if score > 0 else "#f1f8e9"})
        except: pass

    # ===========================
    # CSV 存檔邏輯
    # ===========================
    csv_filename = "news_archive.csv"
    file_exists = os.path.isfile(csv_filename)
    tz_tw = timezone(timedelta(hours=8))
    now_tw = datetime.now(tz_tw).strftime('%Y/%m/%d %H:%M:%S')

    with open(csv_filename, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["時間", "標題", "來源", "分數", "類型", "連結"])
        for item in all_news:
            writer.writerow([now_tw, item['title'], item['source'], item['score'], item['type'], item['link']])
    print(f"資料已成功同步存入 {csv_filename}")

    # (後續生成 index.html 的邏輯省略，同原程式)
    # ...

if __name__ == "__main__":
    main()
