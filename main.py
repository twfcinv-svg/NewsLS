import feedparser
from textblob import TextBlob
from datetime import datetime
import os

def analyze_sentiment(text):
    """分析文字情緒，回傳分數與顏色"""
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    if score > 0.1:
        return score, "Bullish 🐂", "#d4edda", "#155724" # 綠色背景, 深綠字
    elif score < -0.1:
        return score, "Bearish 🐻", "#f8d7da", "#721c24" # 紅色背景, 深紅字
    else:
        return score, "Neutral 😐", "#e2e3e5", "#383d41" # 灰色

def main():
    # 1. 設定新聞來源 (這裡使用 Yahoo Finance 和 Google News 的 RSS)
    rss_urls = [
        "https://finance.yahoo.com/news/rssindex",
        "http://feeds.marketwatch.com/marketwatch/topstories/"
    ]

    news_items = []
    total_score = 0
    count = 0

    print("開始抓取新聞...")

    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            print(f"成功讀取: {url}, 共有 {len(feed.entries)} 則新聞")
            
            # 只取每個來源的前 5 則，避免太長
            for entry in feed.entries[:5]:
                title = entry.title
                link = entry.link
                published = entry.get('published', datetime.now().strftime('%Y-%m-%d'))
                
                score, tag, bg_color, text_color = analyze_sentiment(title)
                total_score += score
                count += 1

                # 建立單則新聞的 HTML 卡片
                item_html = f"""
                <div style="background-color: {bg_color}; color: {text_color}; padding: 15px; margin-bottom: 10px; border-radius: 5px; border-left: 5px solid {text_color};">
                    <div style="font-size: 0.9em; opacity: 0.8;">{published}</div>
                    <h3 style="margin: 5px 0;">
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">{title}</a>
                    </h3>
                    <div style="font-weight: bold; margin-top: 5px;">情緒判斷: {tag} (分數: {score:.2f})</div>
                </div>
                """
                news_items.append(item_html)
        except Exception as e:
            print(f"讀取錯誤 {url}: {e}")

    # 2. 計算整體市場情緒
    avg_score = total_score / count if count > 0 else 0
    market_status = "市場觀望中 😐"
    header_color = "gray"
    
    if avg_score > 0.05:
        market_status = "市場情緒偏多 🚀"
        header_color = "green"
    elif avg_score < -0.05:
        market_status = "市場情緒偏空 📉"
        header_color = "red"

    # 3. 生成完整 HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>每日市場情緒儀表板</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f4; }}
            .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: {header_color}; text-align: center; }}
            .timestamp {{ text-align: center; color: #666; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{market_status}</h1>
            <p class="timestamp">最後更新時間 (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            {''.join(news_items)}
        </div>
    </body>
    </html>
    """

    # 4. 寫入 index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("index.html 生成完畢！")

if __name__ == "__main__":
    main()
