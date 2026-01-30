import feedparser
from datetime import datetime
import re
import random

# ===========================
# 1. 擴充新聞來源 (確保母體夠大)
# ===========================
RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股大盤
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://news.cnyes.com/rss/cnyes/all",                    # 鉅亨網-頭條
    "https://news.cnyes.com/rss/cnyes/stock",                  # 鉅亨網-台股
    "https://news.cnyes.com/rss/cnyes/us_stock",               # 鉅亨網-美股 (新增)
    "https://money.udn.com/rssfeed/news/1001/5590",            # 經濟日報-產業
    "https://money.udn.com/rssfeed/news/1001/5591",            # 經濟日報-證券
    "https://money.udn.com/rssfeed/news/1001/5607",            # 經濟日報-國際
]

# ===========================
# 2. 投資相關關鍵字 (白名單過濾)
# ===========================
# 只有包含這些字的新聞才算「投資新聞」，其餘剔除
INVESTMENT_KEYWORDS = [
    # 市場術語
    "股", "債", "券", "金控", "銀行", "ETF", "基金", "外資", "法人", "投信", "自營", "主力",
    "買超", "賣超", "多頭", "空頭", "漲", "跌", "盤", "指數", "加權", "櫃買", "期貨", "選擇權",
    "道瓊", "那斯達克", "標普", "費半", "ADR", "匯率", "美元", "央行", "升息", "降息", "通膨", "CPI",
    # 財報基本面
    "營收", "獲利", "EPS", "盈餘", "毛利", "股利", "配息", "除權", "填息", "殖利率", "法說", 
    "季報", "年報", "月報", "財報", "展望", "目標價", "評等", "庫存", "接單", "訂單", "產能",
    # 產業與熱門股
    "台積", "鴻海", "聯發科", "AI", "半導體", "晶圓", "伺服器", "散熱", "CoWoS", "IP",
    "IC", "PCB", "被動元件", "記憶體", "面板", "網通", "低軌", "電動車", "車用",
    "航運", "貨櫃", "散裝", "鋼鐵", "塑化", "重電", "生技", "軍工", "營建", "觀光"
]

# ===========================
# 3. 多空權重字典 (Sentiment V2)
# ===========================
SENTIMENT_DICT = {
    "bull_strong": ["漲停", "飆", "噴出", "大漲", "創高", "新高", "完勝", "大賺", "搶手", "暴漲", "報喜", "噴發", "熱錢", "軋空"],
    "bull_normal": ["漲", "揚", "攻", "旺", "強", "升", "紅", "買超", "加碼", "利多", "樂觀", "成長", "填息", "進補", "受惠", "復甦", "點火", "獲利", "看好", "目標價", "法說", "發威", "撐盤", "收紅", "擴產"],
    "bull_weak": ["微漲", "小漲", "回穩", "反彈", "收斂", "趨緩", "收復", "站上", "有守"],

    "bear_strong": ["跌停", "崩", "暴跌", "重挫", "破底", "殺盤", "跳水", "大跌", "重摔", "血洗", "股災"],
    "bear_normal": ["跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", "利空", "保守", "衰退", "貼息", "縮水", "砍單", "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "疑慮", "下修", "虧損", "賣壓", "收黑", "裁員"],
    "bear_weak": ["微跌", "小跌", "震盪", "整理", "觀望", "疲軟"],
    
    "negation": ["不", "未", "無", "非", "免", "抗", "防", "止", "終止", "收斂", "無懼"]
}

# ===========================
# 4. 核心邏輯
# ===========================

def clean_title(title):
    title = re.sub(r" - Yahoo.*", "", title)
    title = re.sub(r" - 鉅亨.*", "", title)
    title = re.sub(r" - 經濟.*", "", title)
    title = re.sub(r"\(.*?\)", "", title)
    return title.strip()

def is_investment_related(title):
    """檢查是否包含投資關鍵字"""
    for kw in INVESTMENT_KEYWORDS:
        if kw in title:
            return True
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

    # 1. 強利多 (+2.5)
    for w in SENTIMENT_DICT["bull_strong"]:
        if w in title:
            val = 2.5
            if is_negated(w, title): score -= val * 0.5
            else: score += val
            
    # 2. 普通利多 (+1)
    for w in SENTIMENT_DICT["bull_normal"]:
        if w in title:
            val = 1.0
            if is_negated(w, title): score -= 0.5
            else: score += val

    # 3. 微利多 (+0.5)
    for w in SENTIMENT_DICT["bull_weak"]:
        if w in title: score += 0.5

    # 4. 強利空 (-2.5)
    for w in SENTIMENT_DICT["bear_strong"]:
        if w in title:
            val = 2.5
            if is_negated(w, title): score += val * 0.8
            else: score -= val

    # 5. 普通利空 (-1.2)
    for w in SENTIMENT_DICT["bear_normal"]:
        if w in title:
            val = 1.2
            if is_negated(w, title): score += 0.5
            else: score -= val

    return round(score, 1)

def main():
    print("啟動 V6 投資快篩引擎...")
    all_news = []
    seen_links = set()

    # 1. 大量抓取 (每源抓 60 則 -> 總量可達 400+ 原始新聞)
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            print(f"來源: {url} - 取得 {len(feed.entries)} 則")
            
            for entry in feed.entries[:60]: 
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                
                # 【關鍵步驟】先過濾：是否為投資新聞？
                if not is_investment_related(title):
                    continue

                score = calculate_sentiment_score(title)
                
                # 【關鍵步驟】再過濾：剔除完全無關的中立新聞 (0分)
                if score == 0: 
                    continue
                
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

    # 2. 分流與排序
    bullish = [n for n in all_news if n['score'] > 0]
    bearish = [n for n in all_news if n['score'] < 0]

    bullish.sort(key=lambda x: x['score'], reverse=True)
    bearish.sort(key=lambda x: x['score']) 

    # 3. 生成 HTML
    today_date = datetime.now().strftime('%Y-%m-%d')
    total_count = len(bullish) + len(bearish)
    
    def generate_table_rows(news_list):
        html = ""
        for i, item in enumerate(news_list):
            score_sign = "+" if item['score'] > 0 else ""
            html += f"""
            <tr style="border-bottom: 1px solid #eee; background-color: {item['bg']};">
                <td style="padding: 6px; color: #666; font-size: 0.8em; width: 30px; text-align: center;">{i+1}</td>
                <td style="padding: 6px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-weight: 500; display: block; line-height: 1.4; font-size: 15px;">
                        {item['title']}
                    </a>
                </td>
                <td style="padding: 6px; text-align: right; width: 60px; font-family: monospace; font-weight: bold; color: {item['color']}; font-size: 1.1em;">
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
        <title>投資情報快篩日報</title>
        <style>
            body {{ font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; background: #fff; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: baseline; }}
            h1 {{ margin: 0; font-size: 24px; color: #000; }}
            .meta {{ color: #666; font-size: 14px; }}
            
            .section-header {{ 
                background: #333; color: #fff; padding: 6px 15px; font-weight: bold; 
                margin-top: 30px; margin-bottom: 0; border-radius: 4px 4px 0 0;
                display: flex; justify-content: space-between; font-size: 1.1em;
            }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #ddd; }}
            
            .bull-header {{ background: #c62828; }}
            .bear-header {{ background: #2e7d32; }}
            
            .stats-bar {{ background: #f8f9fa; padding: 10px; text-align: center; border-radius: 5px; margin-bottom: 20px; font-size: 0.9em; color: #555; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 投資情報快篩日報 (Investment Focus)</h1>
                <span class="meta">{today_date}</span>
            </header>
            
            <div class="stats-bar">
                經由 {len(RSS_URLS)} 個來源掃描，從母體中篩選出 <strong>{total_count}</strong> 則高相關新聞
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

            <div style="text-align: center; color: #999; font-size: 12px; margin-top: 50px; border-top: 1px dashed #ccc; padding-top: 10px;">
                系統自動生成 | 僅保留投資相關標題
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"篩選完畢。多方: {len(bullish)}, 空方: {len(bearish)}")

if __name__ == "__main__":
    main()
