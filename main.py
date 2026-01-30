import feedparser
from datetime import datetime, timedelta, timezone
import re
import random

# ===========================
# 1. 究極新聞來源 (來源數 MAX)
# ===========================
RSS_URLS = [
    # --- Yahoo 奇摩股市 (分類最細，量最大) ---
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股盤勢
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=tradtional",      # 傳產
    "https://tw.stock.yahoo.com/rss?category=finance",         # 金融
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://tw.stock.yahoo.com/rss?category=hke-market",      # 港股
    "https://tw.stock.yahoo.com/rss?category=chk-market",      # 陸股
    "https://tw.stock.yahoo.com/rss?category=research",        # 研究報告
    "https://tw.stock.yahoo.com/rss?category=personal-finance",# 理財
    "https://tw.stock.yahoo.com/rss?category=foreign-exchange",# 匯率

    # --- 鉅亨網 CnYes (專業財經) ---
    "https://news.cnyes.com/rss/cnyes/all",                    # 頭條
    "https://news.cnyes.com/rss/cnyes/stock",                  # 台股
    "https://news.cnyes.com/rss/cnyes/us_stock",               # 美股
    "https://news.cnyes.com/rss/cnyes/future",                 # 期貨
    "https://news.cnyes.com/rss/cnyes/forex",                  # 外匯
    "https://news.cnyes.com/rss/cnyes/industry",               # 產業

    # --- 經濟日報 UDN ---
    "https://money.udn.com/rssfeed/news/1001/5590",            # 產業
    "https://money.udn.com/rssfeed/news/1001/5591",            # 證券
    "https://money.udn.com/rssfeed/news/1001/5607",            # 國際
    "https://money.udn.com/rssfeed/news/1001/12017",           # 基金

    # --- MoneyDJ 理財網 ---
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB010000", # 財經
    "https://www.moneydj.com/rss/newstrust.aspx?rsid=MB020000", # 國際

    # --- 自由時報 LTN ---
    "https://news.ltn.com.tw/rss/business.xml",                # 財經

    # --- 中時新聞網 ---
    "https://www.chinatimes.com/rss/realtimenews-finance.xml", # 財經

    # --- ETToday ---
    "https://feeds.feedburner.com/ettoday/finance",            # 財經雲
]

# ===========================
# 2. 投資關鍵字白名單 (過濾雜訊)
# ===========================
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

# ===========================
# 3. 多空權重字典 (含避風港邏輯)
# ===========================
SENTIMENT_DICT = {
    # 強力多 (+2.5)
    "bull_strong": [
        "漲停", "飆", "噴出", "大漲", "創高", "新高", "完勝", "大賺", "搶手", "暴漲", 
        "報喜", "噴發", "熱錢", "軋空", "避風港", "抗跌"
    ],
    # 普通多 (+1.0)
    "bull_normal": [
        "漲", "揚", "攻", "旺", "強", "升", "紅", "買超", "加碼", "利多", "樂觀", 
        "成長", "填息", "進補", "受惠", "復甦", "點火", "獲利", "看好", "目標價", 
        "法說", "發威", "撐盤", "收紅", "擴產", "防禦", "高股息", "護盤"
    ],
    # 微多 (+0.5)
    "bull_weak": [
        "微漲", "小漲", "回穩", "反彈", "收斂", "趨緩", "收復", "站上", "有守"
    ],

    # 強利空 (-2.5)
    "bear_strong": [
        "跌停", "崩", "暴跌", "重挫", "破底", "殺盤", "跳水", "大跌", "重摔", "血洗", "股災"
    ],
    # 普通空 (-1.2)
    "bear_normal": [
        "跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", "利空", 
        "保守", "衰退", "貼息", "縮水", "砍單", "不如預期", "示警", "隱憂", "壓力", 
        "失守", "翻黑", "疑慮", "下修", "虧損", "賣壓", "收黑", "裁員"
    ],
    # 微空 (-0.5)
    "bear_weak": [
        "微跌", "小跌", "震盪", "整理", "觀望", "疲軟"
    ],
    
    # 否定詞
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

def is_investment_related(title):
    for kw in INVESTMENT_KEYWORDS:
        if kw in title: return True
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

    # 計算多方
    for w in SENTIMENT_DICT["bull_strong"]:
        if w in title:
            score += 2.5 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_normal"]:
        if w in title:
            score += 1.0 if not is_negated(w, title) else -0.5
    for w in SENTIMENT_DICT["bull_weak"]:
        if w in title: score += 0.5

    # 計算空方
    for w in SENTIMENT_DICT["bear_strong"]:
        if w in title:
            score -= 2.5 if not is_negated(w, title) else -2.0 # 否定崩盤=利多
    for w in SENTIMENT_DICT["bear_normal"]:
        if w in title:
            score -= 1.2 if not is_negated(w, title) else -0.5

    return round(score, 1)

def main():
    print("啟動【Max Source】掃描引擎...")
    all_news = []
    seen_links = set()
    total_raw_count = 0

    # 1. 抓取所有來源
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            items = feed.entries
            print(f"掃描: {url} -> {len(items)} 則")
            
            for entry in items: 
                total_raw_count += 1
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                
                # 投資過濾
                if not is_investment_related(title):
                    continue

                score = calculate_sentiment_score(title)
                
                # 剔除中立
                if score == 0: 
                    continue
                
                # 顏色
                if score > 0:
                    color = "#b71c1c" # 紅
                    bg_color = "#fff5f5"
                else:
                    color = "#1b5e20" # 綠
                    bg_color = "#f1f8e9"

                all_news.append({
                    "title": title,
                    "link": entry.link,
                    "score": score,
                    "color": color,
                    "bg": bg_color,
                    "date": entry.get("published", "")[:10]
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # 2. 排序
    bullish = [n for n in all_news if n['score'] > 0]
    bearish = [n for n in all_news if n['score'] < 0]

    bullish.sort(key=lambda x: x['score'], reverse=True)
    bearish.sort(key=lambda x: x['score']) 

    # 3. 時間設定 (UTC+8)
    tz_tw = timezone(timedelta(hours=8))
    now_tw = datetime.now(tz_tw).strftime('%Y/%m/%d %H:%M:%S (台灣時間)')
    final_count = len(bullish) + len(bearish)
    
    def generate_table_rows(news_list):
        html = ""
        for i, item in enumerate(news_list):
            score_sign = "+" if item['score'] > 0 else ""
            html += f"""
            <tr style="border-bottom: 1px solid #eee; background-color: {item['bg']};">
                <td style="padding: 5px; color: #888; font-size: 0.8em; width: 30px; text-align: center;">{i+1}</td>
                <td style="padding: 5px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-weight: 500; display: block; line-height: 1.4; font-size: 14px;">
                        {item['title']}
                    </a>
                </td>
                <td style="padding: 5px; text-align: right; width: 50px; font-family: monospace; font-weight: bold; color: {item['color']}; font-size: 1.1em;">
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
        <title>投資情報快篩 (Live)</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", sans-serif; background: #fff; margin: 0; padding: 10px; color: #333; }}
            .container {{ max-width: 100%; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #333; margin-bottom: 10px; padding-bottom: 5px; display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; }}
            h1 {{ margin: 0; font-size: 20px; color: #000; }}
            .update-time {{ color: #d32f2f; font-weight: bold; font-size: 14px; }}
            
            .section-header {{ 
                background: #333; color: #fff; padding: 5px 10px; font-weight: bold; 
                margin-top: 20px; margin-bottom: 0; border-radius: 4px 4px 0 0;
                display: flex; justify-content: space-between; font-size: 1em;
            }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #ddd; }}
            
            .bull-header {{ background: #c62828; }}
            .bear-header {{ background: #2e7d32; }}
            
            .stats-bar {{ background: #f0f0f0; padding: 8px; text-align: center; border-radius: 4px; margin-bottom: 15px; font-size: 0.85em; color: #555; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 投資情報快篩</h1>
                <span class="update-time">最後更新：{now_tw}</span>
            </header>
            
            <div class="stats-bar">
                掃描母體：<strong>{total_raw_count}</strong> 則新聞 | 
                AI 篩選後：<strong>{final_count}</strong> 則高相關情報
            </div>

            <div class="section-header bull-header">
                <span>🔥 多方強勢 (Bullish)</span>
                <span>{len(bullish)} 筆</span>
            </div>
            <table>
                {generate_table_rows(bullish)}
            </table>

            <div class="section-header bear-header">
                <span>📉 空方風險 (Bearish)</span>
                <span>{len(bearish)} 筆</span>
            </div>
            <table>
                {generate_table_rows(bearish)}
            </table>

            <div style="text-align: center; color: #ccc; font-size: 11px; margin-top: 30px;">
                Generated by GitHub Actions | Update Time: {now_tw}
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"更新完畢。時間: {now_tw}, 母體: {total_raw_count}")

if __name__ == "__main__":
    main()
