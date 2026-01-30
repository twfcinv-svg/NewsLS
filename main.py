import feedparser
from datetime import datetime
import re
import random

# ===========================
# 1. 擴充新聞來源 (為了達到 2 頁內容)
# ===========================
RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股大盤
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://news.cnyes.com/rss/cnyes/all",                    # 鉅亨網-頭條
    "https://news.cnyes.com/rss/cnyes/stock",                  # 鉅亨網-台股
    "https://money.udn.com/rssfeed/news/1001/5590",            # 經濟日報-產業
    "https://money.udn.com/rssfeed/news/1001/5591",            # 經濟日報-證券
]

# ===========================
# 2. 關鍵字與評分邏輯 (更嚴格)
# ===========================
SENTIMENT_DICT = {
    "bullish": [
        "漲", "飆", "揚", "攻", "噴", "旺", "熱", "強", "升", "高", "頂", 
        "紅", "多頭", "買超", "加碼", "利多", "樂觀", "成長", "創高", 
        "填息", "完勝", "進補", "受惠", "轉強", "復甦", "點火", "撐盤",
        "大賺", "獲利", "新高", "搶手", "反彈", "看好", "目標價", "法說"
    ],
    "bearish": [
        "跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", 
        "利空", "保守", "衰退", "破底", "貼息", "重挫", "縮水", "砍單", 
        "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "跳水", 
        "疑慮", "下修", "利潤減", "虧損", "賣壓"
    ]
}

# 增加產業關鍵字以利自動分類 (視覺用)
CATEGORIES = {
    "elec": ["台積", "半導體", "電子", "AI", "廣達", "緯創", "技嘉", "鴻海", "聯發科", "晶圓", "IC", "蘋概", "光學"],
    "finance": ["金控", "銀行", "壽險", "富邦", "國泰", "中信"],
    "old": ["航運", "長榮", "鋼鐵", "中鋼", "塑化", "紡織", "水泥", "重電"],
}

# ===========================
# 3. 核心函式
# ===========================

def clean_title(title):
    """清理標題雜訊"""
    title = re.sub(r" - Yahoo.*", "", title)
    title = re.sub(r" - 鉅亨.*", "", title)
    title = re.sub(r" - 經濟.*", "", title)
    title = re.sub(r"\(.*?\)", "", title) # 移除括號內容
    return title.strip()

def calculate_sentiment(title):
    """
    回傳: (分數, 標籤, 顏色)
    """
    score = 0
    title_check = title.replace("不畏", "") # 排除雙重否定誤判
    
    for word in SENTIMENT_DICT["bullish"]:
        if word in title_check: score += 1
    for word in SENTIMENT_DICT["bearish"]:
        if word in title_check: score -= 1.2  # 利空權重加重

    # 嚴格判斷：必須要有分數才算，0分就是中立
    if score > 0:
        return score, "利多 🐂", "#ffebee", "#c62828" # 紅底紅字
    elif score < 0:
        return score, "利空 🐻", "#e8f5e9", "#2e7d32" # 綠底綠字
    else:
        return 0, "中立", "gray", "gray"

def classify_category(title):
    for key, keywords in CATEGORIES.items():
        for k in keywords:
            if k in title: return key
    return "other"

# ===========================
# 4. 主程式
# ===========================

def main():
    print("啟動加強版爬蟲...")
    all_news = []
    seen_links = set()

    # 1. 暴力抓取 (每源抓 20 則，確保量大)
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]: # 增加抓取數量
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                score, tag, bg, text = calculate_sentiment(title)
                
                # 【關鍵修改】直接過濾掉中立新聞 (分數為0的不收錄)
                if score == 0: 
                    continue
                
                all_news.append({
                    "title": title,
                    "link": entry.link,
                    "score": score,
                    "tag": tag,
                    "bg": bg,
                    "text": text,
                    "cat": classify_category(title)
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # 2. 分流：多方 vs 空方
    bullish_news = [n for n in all_news if n['score'] > 0]
    bearish_news = [n for n in all_news if n['score'] < 0]

    # 3. 排序 (強勢的在最上面，慘烈的在最下面)
    bullish_news.sort(key=lambda x: x['score'], reverse=True) # 分數高到低
    bearish_news.sort(key=lambda x: x['score']) # 分數低到高 (越負越慘)

    # 4. 生成 HTML (多方在前，空方在最後)
    today_date = datetime.now().strftime('%Y/%m/%d')
    
    # 輔助函式：產生列表 HTML
    def generate_html_list(news_list, title, color_code):
        if not news_list: return ""
        
        list_html = ""
        for i, item in enumerate(news_list):
            list_html += f"""
            <li style="display: flex; align-items: flex-start; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed #ddd;">
                <div style="flex: 1;">
                    <span style="font-weight: bold; margin-right: 8px; color: #999; font-size: 0.9em;">{i+1}.</span>
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-size: 16px; line-height: 1.5;">{item['title']}</a>
                </div>
                <div style="margin-left: 15px; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; background-color: {item['bg']}; color: {item['text']}; white-space: nowrap; height: fit-content;">
                    {item['tag']}
                </div>
            </li>
            """
        
        return f"""
        <div style="margin-bottom: 40px; page-break-inside: avoid;">
            <div style="background: {color_code}; color: white; padding: 10px 15px; font-size: 18px; font-weight: bold; border-radius: 5px 5px 0 0;">
                {title} (共 {len(news_list)} 則)
            </div>
            <ul style="list-style: none; padding: 15px; margin: 0; background: #fff; border: 1px solid #eee; border-top: none; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                {list_html}
            </ul>
        </div>
        """

    # 5. 組合最終頁面
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>深度多空日報</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", "Segoe UI", sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 50px; box-shadow: 0 0 20px rgba(0,0,0,0.1); min-height: 2000px; }} /* 強制高度模擬2頁 */
            h1 {{ text-align: center; color: #1a237e; border-bottom: 4px double #1a237e; padding-bottom: 15px; margin-bottom: 30px; }}
            .meta {{ text-align: center; color: #666; margin-bottom: 40px; font-size: 1.1em; }}
            a:hover {{ text-decoration: underline !important; color: #d32f2f !important; }}
            .quote {{ text-align: center; font-style: italic; color: #555; margin: 30px 0; padding: 20px; background: #fafafa; border-left: 5px solid #666; }}
            
            @media print {{
                body {{ background: white; }}
                .container {{ box-shadow: none; width: 100%; max-width: 100%; padding: 0; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 深度財經多空日報 (Pro)</h1>
            <div class="meta">日期：{today_date} | 資料來源：Yahoo/鉅亨/經濟日報 | 篩選模式：嚴格多空</div>

            {generate_html_list(bullish_news, "🚀 多方強勢焦點 (Bullish News)", "#c62828")}

            <div class="quote">
                “行情總在絕望中誕生，在半信半疑中成長，在憧憬中成熟，在希望中毀滅。”
            </div>

            <br><br>

            {generate_html_list(bearish_news, "📉 市場利空與風險警示 (Bearish / Risks)", "#2e7d32")}

            <div style="text-align: center; color: #aaa; margin-top: 50px; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 20px;">
                End of Report - Generated by GitHub Actions
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"報告生成完畢：多方 {len(bullish_news)} 則，空方 {len(bearish_news)} 則。")

if __name__ == "__main__":
    main()
