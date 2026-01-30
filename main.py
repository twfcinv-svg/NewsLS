import feedparser
from datetime import datetime
import re
import random

# ===========================
# 1. 擴充新聞來源 (最大化資料量)
# ===========================
RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股大盤
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://news.cnyes.com/rss/cnyes/all",                    # 鉅亨網-頭條
    "https://news.cnyes.com/rss/cnyes/stock",                  # 鉅亨網-台股
    "https://money.udn.com/rssfeed/news/1001/5590",            # 經濟日報-產業
    "https://money.udn.com/rssfeed/news/1001/5591",            # 經濟日報-證券
    "https://money.udn.com/rssfeed/news/1001/5607",            # 經濟日報-國際
]

# ===========================
# 2. 升級版多空字典 (權重制)
# ===========================
# 權重設定：強烈(+2/-2), 普通(+1/-1), 微弱(+0.5/-0.5)
SENTIMENT_DICT = {
    # === 利多關鍵字 ===
    "bull_strong": ["漲停", "飆", "噴出", "大漲", "創高", "新高", "完勝", "大賺", "搶手", "暴漲", "報喜", "噴發", "熱錢"],
    "bull_normal": ["漲", "揚", "攻", "旺", "強", "升", "紅", "買超", "加碼", "利多", "樂觀", "成長", "填息", "進補", "受惠", "復甦", "點火", "獲利", "看好", "目標價", "法說", "發威", "撐盤", "收紅"],
    "bull_weak": ["微漲", "小漲", "回穩", "反彈", "收斂", "趨緩", "收復", "站上"],

    # === 利空關鍵字 ===
    "bear_strong": ["跌停", "崩", "暴跌", "重挫", "破底", "殺盤", "跳水", "大跌", "重摔", "血洗"],
    "bear_normal": ["跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", "利空", "保守", "衰退", "貼息", "縮水", "砍單", "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "疑慮", "下修", "虧損", "賣壓", "收黑"],
    "bear_weak": ["微跌", "小跌", "震盪", "整理", "觀望"],
    
    # === 否定/反轉詞 (重要！用來修正誤判) ===
    # 例如： "不" 畏下跌 -> 利多
    "negation": ["不", "未", "無", "非", "免", "抗", "防", "止", "終止", "收斂"]
}

# ===========================
# 3. 核心邏輯
# ===========================

def clean_title(title):
    """清理標題雜訊"""
    title = re.sub(r" - Yahoo.*", "", title)
    title = re.sub(r" - 鉅亨.*", "", title)
    title = re.sub(r" - 經濟.*", "", title)
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"\[.*?\]", "", title)
    return title.strip()

def calculate_sentiment_score(title):
    """
    計算精確分數
    邏輯：掃描關鍵字，並檢查關鍵字前方是否有「否定詞」
    """
    score = 0
    title_check = title # 備用
    
    # 簡單的否定檢查窗格 (看關鍵字前2個字有沒有否定詞)
    def is_negated(keyword, text):
        idx = text.find(keyword)
        if idx > 0:
            # 檢查前兩個字
            prefix = text[max(0, idx-2):idx]
            for neg in SENTIMENT_DICT["negation"]:
                if neg in prefix:
                    return True
        return False

    # 1. 掃描強利多 (+2)
    for w in SENTIMENT_DICT["bull_strong"]:
        if w in title:
            val = 2.5
            if is_negated(w, title): score -= val * 0.5 # 否定反而扣分
            else: score += val
            
    # 2. 掃描普通利多 (+1)
    for w in SENTIMENT_DICT["bull_normal"]:
        if w in title:
            val = 1.0
            if is_negated(w, title): score -= 0.5 # 例如：不漲 -> 微空
            else: score += val

    # 3. 掃描微利多 (+0.5)
    for w in SENTIMENT_DICT["bull_weak"]:
        if w in title: score += 0.5

    # 4. 掃描強利空 (-2)
    for w in SENTIMENT_DICT["bear_strong"]:
        if w in title:
            val = 2.5
            if is_negated(w, title): score += val * 0.8 # 例如：不畏崩盤 -> 利多
            else: score -= val

    # 5. 掃描普通利空 (-1)
    for w in SENTIMENT_DICT["bear_normal"]:
        if w in title:
            val = 1.2 # 利空通常影響較大，權重稍重
            if is_negated(w, title): score += 0.5 # 例如：終止跌勢 -> 微多
            else: score -= val

    return round(score, 1)

def main():
    print("啟動高精度爬蟲...")
    all_news = []
    seen_links = set()

    # 1. 大量抓取 (每源抓 50 則)
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            print(f"來源: {url} - 取得 {len(feed.entries)} 則")
            
            for entry in feed.entries[:50]: 
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                score = calculate_sentiment_score(title)
                
                # 只過濾完全無關的 (0分)，保留微幅波動的新聞以充實版面
                if score == 0: 
                    continue
                
                # 決定顏色 (純文字風格，不花俏)
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

    # 2. 分流排序
    bullish = [n for n in all_news if n['score'] > 0]
    bearish = [n for n in all_news if n['score'] < 0]

    bullish.sort(key=lambda x: x['score'], reverse=True) # 分數高 -> 低
    bearish.sort(key=lambda x: x['score']) # 分數低 -> 高 (負越多越慘)

    # 3. 生成 HTML (簡潔報表風)
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    def generate_table_rows(news_list):
        html = ""
        for i, item in enumerate(news_list):
            score_sign = "+" if item['score'] > 0 else ""
            html += f"""
            <tr style="border-bottom: 1px solid #eee; background-color: {item['bg']};">
                <td style="padding: 8px; color: #666; font-size: 0.85em; width: 40px; text-align: center;">{i+1}</td>
                <td style="padding: 8px;">
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-weight: 500; display: block; line-height: 1.4;">
                        {item['title']}
                    </a>
                </td>
                <td style="padding: 8px; text-align: right; width: 80px; font-family: monospace; font-weight: bold; color: {item['color']};">
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
        <title>市場多空量化日報</title>
        <style>
            body {{ font-family: "Segoe UI", "Microsoft JhengHei", sans-serif; background: #fff; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            header {{ border-bottom: 2px solid #333; margin-bottom: 30px; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: baseline; }}
            h1 {{ margin: 0; font-size: 24px; color: #000; }}
            .meta {{ color: #666; font-size: 14px; }}
            
            .section-header {{ 
                background: #333; color: #fff; padding: 8px 15px; font-weight: bold; 
                margin-top: 40px; margin-bottom: 0; border-radius: 4px 4px 0 0;
                display: flex; justify-content: space-between;
            }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #ddd; }}
            
            .bull-header {{ background: #c62828; }}
            .bear-header {{ background: #2e7d32; }}
            
            @media print {{
                .section-header {{ -webkit-print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📈 市場多空量化日報 (Quant Daily)</h1>
                <span class="meta">日期: {today_date} | 資料量: {len(all_news)} 則</span>
            </header>

            <div class="section-header bull-header">
                <span>多方強勢訊號 (Bullish Signals)</span>
                <span>共 {len(bullish)} 筆</span>
            </div>
            <table>
                {generate_table_rows(bullish)}
            </table>

            <div class="section-header bear-header">
                <span>空方風險示警 (Bearish Signals)</span>
                <span>共 {len(bearish)} 筆</span>
            </div>
            <table>
                {generate_table_rows(bearish)}
            </table>

            <div style="text-align: center; color: #999; font-size: 12px; margin-top: 50px; border-top: 1px dashed #ccc; padding-top: 10px;">
                Generated by GitHub Actions | Score > 0: Bullish | Score < 0: Bearish
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Done. Bullish: {len(bullish)}, Bearish: {len(bearish)}")

if __name__ == "__main__":
    main()
