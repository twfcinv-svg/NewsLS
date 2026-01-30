import feedparser
from datetime import datetime, timedelta, timezone
import re
import random

# ===========================
# 1. 究極新聞來源
# ===========================
RSS_URLS = [
    # Yahoo 奇摩股市
    "https://tw.stock.yahoo.com/rss?category=tw-market",       
    "https://tw.stock.yahoo.com/rss?category=tech",            
    "https://tw.stock.yahoo.com/rss?category=tradtional",      
    "https://tw.stock.yahoo.com/rss?category=finance",         
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    
    "https://tw.stock.yahoo.com/rss?category=hke-market",      
    "https://tw.stock.yahoo.com/rss?category=chk-market",      
    "https://tw.stock.yahoo.com/rss?category=research",        
    "https://tw.stock.yahoo.com/rss?category=personal-finance",
    "https://tw.stock.yahoo.com/rss?category=foreign-exchange",

    # 鉅亨網 CnYes
    "https://news.cnyes.com/rss/cnyes/all",                    
    "https://news.cnyes.com/rss/cnyes/stock",                  
    "https://news.cnyes.com/rss/cnyes/us_stock",               
    "https://news.cnyes.com/rss/cnyes/future",                 
    "https://news.cnyes.com/rss/cnyes/forex",                  
    "https://news.cnyes.com/rss/cnyes/industry",               

    # 經濟日報 UDN
    "https://money.udn.com/rssfeed/news/1001/5590",            
    "https://money.udn.com/rssfeed/news/1001/5591",            
    "https://money.udn.com/rssfeed/news/1001/5607",            
    "https://money.udn.com/rssfeed/news/1001/12017",           

    # MoneyDJ / ETToday / LTN / ChinaTimes
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB010000", 
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB020000", 
    "https://feeds.feedburner.com/ettoday/finance",            
    "https://news.ltn.com.tw/rss/business.xml",                
    "https://www.chinatimes.com/rss/realtimenews-finance.xml", 
]

# ===========================
# 2. 關鍵字過濾系統 (白名單 vs 黑名單)
# ===========================

# [白名單] 必須包含這些字才保留
INVESTMENT_KEYWORDS = [
    "股", "債", "券", "金控", "銀行", "ETF", "基金", "外資", "法人", "投信", "自營", "主力",
    "買超", "賣超", "多頭", "空頭", "漲", "跌", "盤", "指數", "加權", "櫃買", "期貨", "選擇權",
    "道瓊", "那斯達克", "標普", "費半", "ADR", "匯率", "美元", "央行", "升息", "降息", "通膨", "CPI",
    "營收", "獲利", "EPS", "盈餘", "毛利", "股利", "配息", "除權", "填息", "殖利率", "法說", 
    "季報", "年報", "月報", "財報", "展望", "目標價", "評等", "庫存", "接單", "訂單", "產能",
    "台積", "鴻海", "聯發科", "AI", "半導體", "晶圓", "伺服器", "散熱", "CoWoS", "IP",
    "IC", "PCB", "被動元件", "記憶體", "面板", "網通", "低軌", "電動車", "車用",
    "航運", "貨櫃", "散裝", "鋼鐵", "塑化", "重電", "生技", "軍工", "營建", "觀光"
]

# [黑名單] 標題有這些字直接剔除 (針對你的需求設定)
EXCLUDE_KEYWORDS = [
    # 徵才/職場類
    "徵才", "招募", "求職", "面試", "員工", "薪資", "年終", "分紅", "尾牙", "開缺", "工程師", "人才",
    # 藝人/個人故事/理財雞湯類
    "藝人", "網紅", "男星", "女星", "豪宅", "理財術", "存股術", "買房", "房貸", "後悔", "翻身", "致富", "百萬",
    # 民生消費/油價類
    "油價", "汽油", "柴油", "加油", "開車", "每公升", "調漲", "調降", "路況", "氣象", "颱風", "放假",
    # 廣告/詐騙/其他
    "詐騙", "假冒", "專家傳授", "教你", "懶人包"
]

# ===========================
# 3. 多空權重字典
# ===========================
SENTIMENT_DICT = {
    "bull_strong": ["漲停", "飆", "噴出", "大漲", "創高", "新高", "完勝", "大賺", "搶手", "暴漲", "報喜", "噴發", "熱錢", "軋空", "避風港", "抗跌"],
    "bull_normal": ["漲", "揚", "攻", "旺", "強", "升", "紅", "買超", "加碼", "利多", "樂觀", "成長", "填息", "進補", "受惠", "復甦", "點火", "獲利", "看好", "目標價", "法說", "發威", "撐盤", "收紅", "擴產", "防禦", "高股息", "護盤"],
    "bull_weak": ["微漲", "小漲", "回穩", "反彈", "收斂", "趨緩", "收復", "站上", "有守"],

    "bear_strong": ["跌停", "崩", "暴跌", "重挫", "破底", "殺盤", "跳水", "大跌", "重摔", "血洗", "股災"],
    "bear_normal": ["跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", "利空", "保守", "衰退", "貼息", "縮水", "砍單", "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "疑慮", "下修", "虧損", "賣壓", "收黑", "裁員"],
    "bear_weak": ["微跌", "小跌", "震盪", "整理", "觀望", "疲軟"],
    
    "negation": ["不", "未", "無", "非", "免", "抗", "防", "止", "終止", "收斂", "無懼"]
}

# ===========================
# 4. 核心功能
# ===========================

def clean_title(title):
    title = re.sub(r" - Yahoo.*", "", title)
    title = re.sub(r" - 鉅亨.*", "", title)
    title = re.sub(r" - 經濟.*", "", title)
    title = re.sub(r"\(.*?\)", "", title)
    return title.strip()

def identify_source(link):
    if "yahoo" in link: return "Yahoo股市"
    if "cnyes" in link: return "鉅亨網"
    if "udn" in link: return "經濟日報"
    if "moneydj" in link: return "MoneyDJ"
    if "ltn" in link: return "自由財經"
    if "chinatimes" in link: return "中時"
    if "ettoday" in link: return "ETtoday"
    return "網路新聞"

def filter_news(title):
    # 1. 黑名單檢查 (只要中一個就剔除)
    for bad_word in EXCLUDE_KEYWORDS:
        if bad_word in title:
            return False # 剔除
    
    # 2. 白名單檢查 (必須包含至少一個投資關鍵字)
    for good_word in INVESTMENT_KEYWORDS:
        if good_word in title:
            return True # 保留
            
    return False # 沒中白名單也剔除

def calculate_sentiment_score(title):
    score = 0
    def is_negated(keyword, text):
        idx = text.find(keyword)
        if idx > 0:
            prefix = text[max(0, idx-2):idx]
            for neg in SENTIMENT_DICT["negation"]:
                if neg in prefix: return True
        return False

    for w in SENTIMENT_DICT["bull_strong"]:
        if w in title: score += 2.5 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_normal"]:
        if w in title: score += 1.0 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_weak"]:
        if w in title: score += 0.5
    for w in SENTIMENT_DICT["bear_strong"]:
        if w in title: score -= 2.5 if not is_negated(w, title) else -2.0
    for w in SENTIMENT_DICT["bear_normal"]:
        if w in title: score -= 1.2 if not is_negated(w, title) else -0.5
    return round(score, 1)

def main():
    print("啟動 V9 精準引擎...")
    all_news = []
    seen_links = set()
    total_raw_count = 0

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries: 
                total_raw_count += 1
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                
                # 【核心過濾邏輯】
                if not filter_news(title):
                    continue

                score = calculate_sentiment_score(title)
                if score == 0: continue
                
                if score > 0:
                    color = "#b71c1c" # 紅
                    bg_color = "#fff5f5"
                else:
                    color = "#1b5e20" # 綠
                    bg_color = "#f1f8e9"

                all_news.append({
                    "title": title,
                    "link": entry.link,
                    "source": identify_source(entry.link),
                    "score": score,
                    "color": color,
                    "bg": bg_color
                })
        except: pass

    # 排序
    bullish = sorted([n for n in all_news if n['score'] > 0], key=lambda x: x['score'], reverse=True)
    bearish = sorted([n for n in all_news if n['score'] < 0], key=lambda x: x['score'])

    # 時間
    tz_tw = timezone(timedelta(hours=8))
    now_tw = datetime.now(tz_tw).strftime('%Y/%m/%d %H:%M:%S')
    
    def generate_rows(news_list):
        html = ""
        for i, item in enumerate(news_list):
            score_sign = "+" if item['score'] > 0 else ""
            html += f"""
            <tr style="border-bottom: 1px solid #eee; background-color: {item['bg']};">
                <td style="padding: 8px; color: #666; font-size: 0.8em; text-align: center; width: 40px;">{i+1}</td>
                <td style="padding: 8px; color: #888; font-size: 0.85em; width: 80px;">{item['source']}</td>
                <td style="padding: 8px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-weight: 500; display: block; line-height: 1.4; font-size: 15px;">
                        {item['title']}
                    </a>
                </td>
                <td style="padding: 8px; text-align: right; width: 60px; font-family: monospace; font-weight: bold; color: {item['color']}; font-size: 1.1em;">
                    {score_sign}{item['score']}
                </td>
            </tr>
            """
        return html

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>投資情報快篩 V9</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", sans-serif; background: #fff; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
            h1 {{ margin: 0; font-size: 22px; color: #000; }}
            .controls {{ display: flex; gap: 10px; align-items: center; }}
            .btn-pdf {{ background: #333; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-flex; align-items: center; }}
            .btn-pdf:hover {{ background: #555; }}
            .update-time {{ color: #d32f2f; font-weight: bold; font-size: 14px; margin-right: 15px; }}
            
            .section-header {{ background: #333; color: #fff; padding: 8px 15px; font-weight: bold; margin-top: 25px; border-radius: 4px 4px 0 0; display: flex; justify-content: space-between; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #ddd; }}
            th {{ text-align: left; padding: 8px; background: #f8f9fa; color: #555; font-size: 0.9em; border-bottom: 2px solid #ddd; }}
            
            .bull-header {{ background: #c62828; }}
            .bear-header {{ background: #2e7d32; }}
            
            @media print {{
                .btn-pdf {{ display: none; }}
                body {{ padding: 0; }}
                .container {{ max-width: 100%; }}
                a {{ text-decoration: none; color: black; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 投資情報快篩</h1>
                <div class="controls">
                    <span class="update-time">更新：{now_tw}</span>
                    <button class="btn-pdf" onclick="window.print()">🖨️ 下載 PDF / 列印</button>
                </div>
            </header>
            
            <div style="background:#f0f0f0; padding:10px; text-align:center; font-size:0.9em; border-radius:4px; margin-bottom:15px;">
                母體掃描: {total_raw_count} 則 | 精選情報: {len(bullish)+len(bearish)} 則 (已濾除藝人/徵才/油價雜訊)
            </div>

            <div class="section-header bull-header">
                <span>🔥 多方強勢 (Bullish)</span>
                <span>{len(bullish)} 筆</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="text-align:center;">#</th>
                        <th>來源</th>
                        <th>新聞標題</th>
                        <th style="text-align:right;">分數</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_rows(bullish)}
                </tbody>
            </table>

            <div class="section-header bear-header">
                <span>📉 空方風險 (Bearish)</span>
                <span>{len(bearish)} 筆</span>
            </div>
            <table>
                 <thead>
                    <tr>
                        <th style="text-align:center;">#</th>
                        <th>來源</th>
                        <th>新聞標題</th>
                        <th style="text-align:right;">分數</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_rows(bearish)}
                </tbody>
            </table>

            <div style="text-align: center; color: #ccc; font-size: 11px; margin-top: 30px;">
                Generated by GitHub Actions | Filter Logic V9
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Done.")

if __name__ == "__main__":
    main()
