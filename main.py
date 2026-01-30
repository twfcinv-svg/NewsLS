import feedparser
from datetime import datetime, timedelta, timezone
import re
import random
import time

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
    "https://tw.stock.yahoo.com/rss?category=research",        

    # 鉅亨網 CnYes
    "https://news.cnyes.com/rss/cnyes/stock",                  
    "https://news.cnyes.com/rss/cnyes/all",                    
    "https://news.cnyes.com/rss/cnyes/industry",               

    # 經濟日報 & 工商時報
    "https://money.udn.com/rssfeed/news/1001/5591",            
    "https://money.udn.com/rssfeed/news/1001/5590",            
    "https://ctee.com.tw/feed",                                

    # MoneyDJ / 中時 / 自由 / ETToday / PTT
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB010000", 
    "https://www.chinatimes.com/rss/realtimenews-finance.xml", 
    "https://news.ltn.com.tw/rss/business.xml",                
    "https://feeds.feedburner.com/ettoday/finance",            
    "https://rss.ptt.cc/Stock.xml",
]

# ===========================
# 2. 關鍵字過濾與分類系統
# ===========================

# [個股優先名單] 只要出現這些字，絕對歸類為「個股」(即使標題有三大法人)
STOCK_KEYWORDS = [
    # 權值股
    "台積", "鴻海", "聯發科", "廣達", "緯創", "技嘉", "中華電", "富邦金", "國泰金", "台塑", "南亞",
    # 熱門股/中小型
    "力積電", "華通", "神盾", "安國", "智原", "創意", "世芯", "緯穎", "奇鋐", "雙鴻", "建準", 
    "聯電", "華碩", "宏碁", "微星", "長榮", "陽明", "萬海", "長榮航", "華航", "亞翔", "中興電", "華城", "士電",
    "群創", "友達", "彩晶", "聯詠", "瑞昱", "聯發科", "信驊", "大立光", "玉晶光", "欣興", "南電", "景碩",
    # 產業/概念
    "CoWoS", "AI", "散熱", "IP", "IC", "PCB", "被動元件", "記憶體", "面板", "網通", "低軌", "電動車",
    # 代碼特徵
    "2330", "2317", "2454", "3008", "3035", "3037", "2382", "3231", "2603", "2609", "2615"
]

# [一般投資關鍵字] 用來過濾非財經新聞
INVESTMENT_KEYWORDS = STOCK_KEYWORDS + [
    "股", "債", "券", "金控", "銀行", "ETF", "基金", "外資", "法人", "投信", "自營", "主力",
    "買超", "賣超", "多頭", "空頭", "漲", "跌", "盤", "指數", "加權", "櫃買", "期貨", "選擇權",
    "道瓊", "那斯達克", "標普", "費半", "ADR", "匯率", "美元", "央行", "升息", "降息", "通膨", "CPI",
    "營收", "獲利", "EPS", "盈餘", "毛利", "股利", "配息", "除權", "填息", "殖利率", "法說", 
    "季報", "年報", "月報", "財報", "展望", "目標價", "評等", "庫存", "接單", "訂單", "產能"
]

# [黑名單] 剔除雜訊
EXCLUDE_KEYWORDS = [
    "徵才", "招募", "求職", "面試", "員工", "薪資", "年終", "分紅", "尾牙", "開缺", "工程師", "人才",
    "藝人", "網紅", "男星", "女星", "豪宅", "理財術", "存股術", "買房", "房貸", "後悔", "翻身", "致富", "百萬",
    "油價", "汽油", "柴油", "加油", "開車", "每公升", "調漲", "調降", "路況", "氣象", "颱風", "放假",
    "詐騙", "假冒", "專家傳授", "教你", "懶人包", "閒聊", "公告", "新聞", "標的"
]

# [嚴格大盤關鍵字] 只有在「不包含」上述個股關鍵字時，才生效
MACRO_KEYWORDS = [
    "大盤", "台股", "加權", "指數", "櫃買", "道瓊", "那斯達克", "標普", "費半", 
    "三大法人", "投信", "外資", "央行", "聯準會", "Fed", "升息", "降息", "通膨", 
    "CPI", "匯率", "新台幣", "美元", "美股", "亞股", "歐股", "盤前", "盤後", 
    "收盤", "開盤", "行情", "龍年", "蛇年", "封關", "開紅盤", "台指期"
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

def is_individual_stock(title):
    # 1. 優先檢查：如果有具體個股名稱，絕對是個股 (Priority High)
    for kw in STOCK_KEYWORDS:
        if kw in title: return True
        
    # 2. 檢查是否為大盤 (Priority Low)
    for kw in MACRO_KEYWORDS:
        if kw in title: return False
        
    # 3. 預設歸類為個股/產業
    return True

def main():
    print("啟動 V12 智能過濾引擎 (12H + 個股優先)...")
    all_news = []
    seen_links = set()
    total_raw_count = 0
    skipped_old_count = 0

    # 設定時間門檻 (12小時前)
    time_threshold = datetime.utcnow() - timedelta(hours=12)

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries: 
                total_raw_count += 1
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                # [時間過濾] 檢查文章發布時間
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    # 將 struct_time 轉為 datetime
                    published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    if published_dt < time_threshold:
                        skipped_old_count += 1
                        continue # 太舊了，跳過
                
                title = clean_title(entry.title)
                
                if not filter_news(title): continue

                score = calculate_sentiment_score(title)
                if score == 0: continue
                
                # 判斷分類 (優先權邏輯已修正)
                news_type = "individual" if is_individual_stock(title) else "macro"
                
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
                    "bg": bg_color,
                    "type": news_type
                })
        except Exception as e:
            print(f"Error: {e}")

    # 分類
    bull_macro = sorted([n for n in all_news if n['score'] > 0 and n['type'] == 'macro'], key=lambda x: x['score'], reverse=True)
    bull_stock = sorted([n for n in all_news if n['score'] > 0 and n['type'] == 'individual'], key=lambda x: x['score'], reverse=True)
    bear_macro = sorted([n for n in all_news if n['score'] < 0 and n['type'] == 'macro'], key=lambda x: x['score'])
    bear_stock = sorted([n for n in all_news if n['score'] < 0 and n['type'] == 'individual'], key=lambda x: x['score'])

    # 時間
    tz_tw = timezone(timedelta(hours=8))
    now_tw = datetime.now(tz_tw).strftime('%Y/%m/%d %H:%M:%S')
    
    def generate_rows(news_list):
        html = ""
        for i, item in enumerate(news_list):
            score_sign = "+" if item['score'] > 0 else ""
            html += f"""
            <tr style="border-bottom: 1px solid #eee; background-color: {item['bg']};">
                <td style="padding: 6px; color: #666; font-size: 0.8em; text-align: center; width: 30px;">{i+1}</td>
                <td style="padding: 6px; color: #888; font-size: 0.85em; width: 80px;">{item['source']}</td>
                <td style="padding: 6px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-weight: 500; display: block; line-height: 1.4; font-size: 14px;">
                        {item['title']}
                    </a>
                </td>
                <td style="padding: 6px; text-align: right; width: 50px; font-family: monospace; font-weight: bold; color: {item['color']}; font-size: 1.1em;">
                    {score_sign}{item['score']}
                </td>
            </tr>
            """
        return html if news_list else "<tr><td colspan='4' style='padding:10px; text-align:center; color:#999;'>無相關新聞</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>投資情報快篩 V12</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", sans-serif; background: #fff; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
            h1 {{ margin: 0; font-size: 22px; color: #000; }}
            .controls {{ display: flex; gap: 10px; align-items: center; }}
            .btn-pdf {{ background: #333; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
            .update-time {{ color: #d32f2f; font-weight: bold; font-size: 14px; margin-right: 15px; }}
            
            .section-main {{ margin-top: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
            .section-title {{ padding: 10px 15px; font-weight: bold; color: white; font-size: 1.1em; display: flex; justify-content: space-between; }}
            .bull-title {{ background: #c62828; }}
            .bear-title {{ background: #2e7d32; }}
            
            .sub-section {{ padding: 0; }}
            .sub-title {{ background: #f0f0f0; color: #333; padding: 6px 15px; font-weight: bold; font-size: 0.95em; border-bottom: 1px solid #ddd; border-top: 1px solid #ddd; }}
            
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 8px; background: #fafafa; color: #666; font-size: 0.85em; border-bottom: 1px solid #eee; }}
            
            @media print {{
                .btn-pdf {{ display: none; }}
                body {{ padding: 0; }}
                .container {{ max-width: 100%; }}
                .section-main {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 投資情報快篩</h1>
                <div class="controls">
                    <span class="update-time">更新：{now_tw}</span>
                    <button class="btn-pdf" onclick="window.print()">🖨️ PDF</button>
                </div>
            </header>
            
            <div style="background:#f8f9fa; padding:8px; text-align:center; font-size:0.9em; border-radius:4px; margin-bottom:20px; color:#555;">
                母體掃描: {total_raw_count} 則 (已過濾 {skipped_old_count} 則逾時舊聞) | 資料來源含 Yahoo, 鉅亨, 經濟, 工商, PTT
            </div>

            <div class="section-main">
                <div class="section-title bull-title">
                    <span>🔥 多方訊號 (Bullish)</span>
                    <span>共 {len(bull_macro) + len(bull_stock)} 筆</span>
                </div>
                
                <div class="sub-section">
                    <div class="sub-title">🌎 大盤 & 總體經濟</div>
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
                            {generate_rows(bull_macro)}
                        </tbody>
                    </table>
                </div>
                
                <div class="sub-section">
                    <div class="sub-title">🏢 個股 & 產業動態</div>
                    <table>
                        <tbody>
                            {generate_rows(bull_stock)}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="section-main">
                <div class="section-title bear-title">
                    <span>📉 空方訊號 (Bearish)</span>
                    <span>共 {len(bear_macro) + len(bear_stock)} 筆</span>
                </div>
                
                <div class="sub-section">
                    <div class="sub-title">🌎 大盤 & 總體經濟</div>
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
                            {generate_rows(bear_macro)}
                        </tbody>
                    </table>
                </div>
                
                <div class="sub-section">
                    <div class="sub-title">🏢 個股 & 產業動態</div>
                    <table>
                        <tbody>
                            {generate_rows(bear_stock)}
                        </tbody>
                    </table>
                </div>
            </div>

            <div style="text-align: center; color: #ccc; font-size: 11px; margin-top: 30px;">
                Generated by GitHub Actions | V12 Time-Filtered
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Done. Processed {total_raw_count} items, skipped {skipped_old_count} old items.")

if __name__ == "__main__":
    main()
