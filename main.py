import feedparser
from datetime import datetime
import re
import random

# ===========================
# 1. 設定與關鍵字資料庫
# ===========================

RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股大盤
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://news.cnyes.com/rss/cnyes/all",                    # 鉅亨網
    "https://money.udn.com/rssfeed/news/1001/5588",            # 經濟日報-國際
]

# 分類關鍵字 (權重計分法：比對到越多關鍵字越準確)
CATEGORIES = {
    "electronics": [
        "台積電", "聯發科", "鴻海", "廣達", "緯創", "技嘉", "仁寶", "華碩", "宏碁",
        "半導體", "晶圓", "IC", "AI", "伺服器", "散熱", "PCB", "被動元件", "記憶體",
        "面板", "群創", "友達", "聯電", "力積電", "世界先進", "封測", "日月光",
        "輝達", "Nvidia", "AMD", "英特爾", "Intel", "蘋果", "Apple", "供應鏈",
        "信驊", "創意", "世芯", "矽智財", "IP", "光學", "大立光", "玉晶光"
    ],
    "finance_传产": [
        "金融", "金控", "銀行", "壽險", "國泰", "富邦", "中信", "兆豐",
        "鋼鐵", "中鋼", "塑化", "台塑", "南亞", "水泥", "台泥", "亞泥",
        "航運", "長榮", "陽明", "萬海", "航空", "長榮航", "華航",
        "紡織", "儒鴻", "聚陽", "電機", "重電", "士電", "華城", "中興電",
        "營建", "房市", "生技", "藥", "觀光", "餐飲"
    ],
    "international": [
        "美股", "道瓊", "那斯達克", "費半", "標普", "S&P", "ADR",
        "聯準會", "Fed", "鮑爾", "降息", "升息", "CPI", "PPI", "通膨",
        "外資", "美元", "匯率", "台幣", "歐股", "日股", "港股", "陸股", "ETF"
    ]
}

# 情緒字典 (針對台股用語優化)
SENTIMENT_DICT = {
    "bullish": [
        "漲", "飆", "揚", "攻", "噴", "旺", "熱", "強", "升", "高", 
        "紅", "多頭", "買超", "加碼", "利多", "樂觀", "成長", "創高", 
        "填息", "完勝", "進補", "受惠", "轉強", "復甦", "點火", "撐盤"
    ],
    "bearish": [
        "跌", "挫", "黑", "弱", "降", "低", "空", "賣超", "調節", "減碼", 
        "利空", "保守", "衰退", "破底", "貼息", "重挫", "縮水", "砍單", 
        "不如預期", "示警", "隱憂", "壓力", "失守", "翻黑", "跳水"
    ]
}

# 投資名言
QUOTES = [
    "行情總在絕望中誕生，在半信半疑中成長。",
    "不要與聯準會作對 (Don't fight the Fed).",
    "別人恐懼時我貪婪，別人貪婪時我恐懼。",
    "風險來自於你不知道自己在做什麼。",
    "你是要吃得好(Buy High)，還是要睡得好(Sleep Well)？"
]

# ===========================
# 2. 核心功能函式
# ===========================

def clean_title(title):
    """清理標題雜訊"""
    title = re.sub(r" - Yahoo.*", "", title)
    title = re.sub(r" - 鉅亨.*", "", title)
    title = re.sub(r" - 經濟.*", "", title)
    return title

def calculate_sentiment(title):
    """
    計算標題的多空分數
    回傳: (分數, 標籤, 顏色代碼)
    台股邏輯：紅色是漲(利多)，綠色是跌(利空)
    """
    score = 0
    # 簡單的詞頻加減分
    for word in SENTIMENT_DICT["bullish"]:
        if word in title: score += 1
    for word in SENTIMENT_DICT["bearish"]:
        if word in title: score -= 1.5  # 利空字眼通常權重重一點

    # 判斷結果
    if score >= 1:
        return score, "利多 🐂", "#ffcccc", "#cc0000" # 淺紅底, 深紅字
    elif score <= -1:
        return score, "利空 🐻", "#ccffcc", "#006600" # 淺綠底, 深綠字
    else:
        return score, "中立 😐", "#f0f0f0", "#666666" # 灰底

def classify_news_item(title):
    """判斷一則新聞屬於哪個分類"""
    # 優先判斷是否為「國際/總經」
    for k in CATEGORIES["international"]:
        if k in title: return "intl"
    
    # 判斷電子
    for k in CATEGORIES["electronics"]:
        if k in title: return "elec"
        
    # 判斷金融傳產
    for k in CATEGORIES["finance_传产"]:
        if k in title: return "non_elec"
        
    # 預設歸類
    return "market"

# ===========================
# 3. 主程式邏輯
# ===========================

def main():
    print("啟動財經新聞爬蟲...")
    all_news = []
    seen_links = set()

    # 1. 抓取所有來源
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link in seen_links: continue
                seen_links.add(entry.link)
                
                title = clean_title(entry.title)
                score, tag, bg_color, text_color = calculate_sentiment(title)
                category = classify_news_item(title)
                
                all_news.append({
                    "title": title,
                    "link": entry.link,
                    "score": score,
                    "tag": tag,
                    "bg_color": bg_color,
                    "text_color": text_color,
                    "category": category
                })
        except Exception as e:
            print(f"Error: {e}")

    # 2. 分類整理
    data = {
        "focus": [], "market": [], "elec": [], "non_elec": [], "intl": [], "bearish": []
    }

    # 依照分數排序 (分數絕對值越高的越重要)
    all_news.sort(key=lambda x: abs(x['score']), reverse=True)

    for item in all_news:
        # 特別規則：如果是超級利空 (分數 <= -1.5)，直接複製一份到「利空區」
        if item['score'] <= -1.5:
            data['bearish'].append(item)

        # 正常分類
        if item['category'] == 'intl':
            data['intl'].append(item)
        elif item['category'] == 'elec':
            data['elec'].append(item)
        elif item['category'] == 'non_elec':
            data['non_elec'].append(item)
        else:
            data['market'].append(item)

    # 取前幾名高分/重要的新聞當作「焦點」
    data['focus'] = data['market'][:3] + data['elec'][:2] 

    # 3. 生成 HTML
    today_date = datetime.now().strftime('%Y/%m/%d')
    quote = random.choice(QUOTES)

    def generate_list(items, limit=8):
        html = ""
        for i, item in enumerate(items[:limit]):
            # 這是每一行新聞的 HTML 結構
            html += f"""
            <li style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #eee;">
                <div style="flex: 1;">
                    <span style="font-weight: bold; margin-right: 5px; color: #888;">{i+1}.</span>
                    <a href="{item['link']}" target="_blank" style="text-decoration: none; color: #333; font-size: 15px;">{item['title']}</a>
                </div>
                <div style="margin-left: 10px; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background-color: {item['bg_color']}; color: {item['text_color']}; white-space: nowrap;">
                    {item['tag']} {item['score'] if item['score'] != 0 else ''}
                </div>
            </li>
            """
        return html if html else "<li style='color:#999'>目前無相關新聞</li>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>每日財經多空日報</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", sans-serif; background: #525659; margin: 0; padding: 20px; }}
            .paper {{ background: white; max-width: 850px; margin: 0 auto; padding: 40px; box-shadow: 0 0 15px rgba(0,0,0,0.3); }}
            h1 {{ color: #b71c1c; border-bottom: 3px solid #b71c1c; padding-bottom: 10px; }}
            .section-title {{ background: #f5f5f5; padding: 8px 12px; border-left: 5px solid #333; font-weight: bold; margin-top: 25px; margin-bottom: 10px; display: flex; justify-content: space-between; }}
            ul {{ list-style: none; padding: 0; margin: 0; }}
            a:hover {{ text-decoration: underline !important; color: #b71c1c !important; }}
            .footer {{ margin-top: 40px; border-top: 1px solid #ccc; padding-top: 20px; text-align: center; color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div style="display: flex; justify-content: space-between; align-items: end;">
                <h1>📈 每日財經多空日報</h1>
                <span style="color: #666; font-size: 1.1em; font-weight: bold; padding-bottom: 15px;">{today_date}</span>
            </div>

            <div class="section-title" style="border-left-color: #d32f2f;">🔥 重點頭條 (Focus)</div>
            <ul>{generate_list(data['focus'], 5)}</ul>

            <div class="section-title" style="border-left-color: #1976d2;">⚡ 電子產業 (Tech)</div>
            <ul>{generate_list(data['elec'], 8)}</ul>

            <div class="section-title" style="border-left-color: #388e3c;">🏭 金融與傳產 (Non-Tech)</div>
            <ul>{generate_list(data['non_elec'], 6)}</ul>

            <div class="section-title" style="border-left-color: #fbc02d;">🌎 國際總經 (Global)</div>
            <ul>{generate_list(data['intl'], 6)}</ul>
            
            <div class="section-title" style="border-left-color: #000; background: #ffebee;">⚠️ 市場利空警示 (Bearish Alerts)</div>
            <ul>{generate_list(data['bearish'], 5)}</ul>

            <div class="footer">
                <p style="font-style: italic; font-weight: bold;">“ {quote} ”</p>
                <p>資料來源：Yahoo 股市、鉅亨網 | 自動生成系統</p>
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("日報生成完畢！")

if __name__ == "__main__":
    main()
