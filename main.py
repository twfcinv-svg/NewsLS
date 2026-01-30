import feedparser
from datetime import datetime
import re
import random

# 設定台灣財經新聞來源 (Yahoo 股市, UDN 財經等)
RSS_URLS = [
    "https://tw.stock.yahoo.com/rss?category=tw-market",       # 台股大盤
    "https://tw.stock.yahoo.com/rss?category=tech",            # 科技產業
    "https://tw.stock.yahoo.com/rss?category=intl-markets",    # 國際股市
    "https://news.cnyes.com/rss/cnyes/all",                    # 鉅亨網
]

# 關鍵字分類設定
KEYWORDS = {
    "electronics": ["台積電", "聯發科", "鴻海", "AI", "半導體", "晶圓", "面板", "IC", "電子", "廣達", "緯創", "技嘉", "信驊", "創意", "Nvidia", "AMD", "蘋果"],
    "finance_non_tech": ["金融", "銀行", "鋼鐵", "水泥", "航運", "長榮", "陽明", "中鋼", "台塑", "富邦", "國泰", "傳產", "紡織"],
    "international": ["美股", "道瓊", "那斯達克", "Fed", "聯準會", "外資", "匯率", "美元", "歐股", "日股", "ADR"],
    "bearish": ["跌停", "重挫", "大跌", "賣壓", "砍單", "下修", "利空", "保守", "衰退", "降評", "外資賣超", "翻黑"]
}

# 投資箴言庫
QUOTES = [
    "你不用什麼都懂，但你必須在某一方面懂得比別人多。 – 喬治·索羅斯",
    "別人恐懼時我貪婪，別人貪婪時我恐懼。 – 巴菲特",
    "行情總在絕望中誕生，在半信半疑中成長。 – 約翰·坦伯頓",
    "風險來自於你不知道自己在做什麼。 – 巴菲特",
    "不要與聯準會作對 (Don't fight the Fed).",
]

def clean_title(title):
    """清理標題，移除多餘的後綴"""
    title = re.sub(r" - Yahoo奇摩股市", "", title)
    title = re.sub(r" - 鉅亨網", "", title)
    return title

def classify_news(news_items):
    """將新聞依照關鍵字分門別類"""
    classified = {
        "focus": [],      # 重點議題 (通常放前幾則)
        "market": [],     # 大盤/總經
        "elec": [],       # 電子
        "non_elec": [],   # 金融/傳產
        "intl": [],       # 國際
        "bearish": []     # 利空 (獨立出來)
    }

    seen_links = set() # 避免重複新聞

    for item in news_items:
        if item['link'] in seen_links:
            continue
        seen_links.add(item['link'])
        
        title = item['title']
        
        # 1. 先抓利空 (優先權最高)
        if any(k in title for k in KEYWORDS["bearish"]):
            classified["bearish"].append(item)
            continue # 如果是利空，就歸類在利空，不往下分

        # 2. 國際股市
        if any(k in title for k in KEYWORDS["international"]):
            classified["intl"].append(item)
            continue

        # 3. 電子股
        if any(k in title for k in KEYWORDS["electronics"]):
            classified["elec"].append(item)
            continue

        # 4. 金融/傳產
        if any(k in title for k in KEYWORDS["finance_non_tech"]):
            classified["non_elec"].append(item)
            continue

        # 5. 剩下的歸類為大盤/總經 或 重點
        classified["market"].append(item)

    # 簡單邏輯：從大盤新聞中挑前 3 則當作「重點議題」
    if len(classified["market"]) > 3:
        classified["focus"] = classified["market"][:3]
        classified["market"] = classified["market"][3:]
    else:
        classified["focus"] = classified["market"]

    return classified

def main():
    all_news = []
    print("正在抓取台灣財經新聞...")

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                all_news.append({
                    "title": clean_title(entry.title),
                    "link": entry.link,
                    "published": entry.get("published", "")[:10] # 只取日期前段
                })
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # 進行分類
    data = classify_news(all_news)
    
    # 隨機選一句箴言
    quote = random.choice(QUOTES)
    today_date = datetime.now().strftime('%Y年%m月%d日')

    # 生成 HTML (模仿 PDF 格式)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>哈燒新聞 - {today_date}</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", "Heiti TC", sans-serif; background-color: #525659; margin: 0; padding: 20px; }}
            .paper {{ background-color: white; max-width: 800px; margin: 0 auto; padding: 40px; box-shadow: 0 0 10px rgba(0,0,0,0.5); min-height: 1000px; }}
            .header {{ border-bottom: 3px solid #c00; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: baseline; }}
            .header h1 {{ margin: 0; color: #c00; font-size: 28px; }}
            .header span {{ color: #666; font-size: 16px; }}
            
            .section {{ margin-bottom: 25px; }}
            .section-title {{ background-color: #f0f0f0; border-left: 5px solid #c00; padding: 5px 10px; font-weight: bold; font-size: 18px; margin-bottom: 10px; color: #333; }}
            
            ul {{ list-style-type: none; padding: 0; margin: 0; }}
            li {{ padding: 5px 0; border-bottom: 1px dashed #eee; font-size: 15px; line-height: 1.5; }}
            li:last-child {{ border-bottom: none; }}
            li a {{ text-decoration: none; color: #333; }}
            li a:hover {{ color: #c00; text-decoration: underline; }}
            .index {{ font-weight: bold; color: #c00; margin-right: 5px; }}
            
            .bearish-section .section-title {{ border-left-color: #28a745; background-color: #e6fffa; }} /* 利空用綠色標示(台股習俗) */
            
            .footer {{ margin-top: 50px; border-top: 2px solid #333; padding-top: 20px; text-align: center; color: #555; }}
            .quote {{ font-style: italic; font-size: 16px; margin-bottom: 10px; font-weight: bold; }}
            .disclaimer {{ font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div class="header">
                <h1>🔥 哈燒新聞</h1>
                <span>{today_date}</span>
            </div>

            <div class="section">
                <div class="section-title">◎ 重點議題 新聞</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['focus'][:5])])}
                </ul>
            </div>

            <div class="section">
                <div class="section-title">● 大盤/總經/類股 新聞</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['market'][:8])])}
                </ul>
            </div>

            <div class="section">
                <div class="section-title">⚡ 電子類股 新聞</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['elec'][:8])])}
                </ul>
            </div>

            <div class="section">
                <div class="section-title">🏭 金融、非電類股 新聞</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['non_elec'][:6])])}
                </ul>
            </div>

            <div class="section">
                <div class="section-title">🌎 國際股市 新聞</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['intl'][:5])])}
                </ul>
            </div>

            <div class="section bearish-section">
                <div class="section-title">📉 利空新聞 (留意風險)</div>
                <ul>
                    {''.join([f'<li><span class="index">{i+1}.</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for i, n in enumerate(data['bearish'][:5])])}
                    { '<li><span class="index">-</span> 近期無重大重挫或跌停新聞</li>' if not data['bearish'] else '' }
                </ul>
            </div>

            <div class="footer">
                <div class="quote">“ {quote} ”</div>
                <div class="disclaimer">(資料來源: Yahoo股市、鉅亨網等各大媒體 RSS; 內容僅供參考，不做任何承諾或保證!)</div>
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("哈燒新聞產生完畢！")

if __name__ == "__main__":
    main()
