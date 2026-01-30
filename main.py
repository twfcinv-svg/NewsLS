import feedparser
from textblob import TextBlob
from datetime import datetime

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

def main():
    # 使用 Yahoo Finance 的 RSS
    rss_url = "https://finance.yahoo.com/news/rssindex"
    print(f"正在抓取新聞: {rss_url}")
    
    try:
        feed = feedparser.parse(rss_url)
        print(f"成功抓到 {len(feed.entries)} 則新聞")
    except Exception as e:
        print(f"抓取失敗: {e}")
        return

    news_html = ""
    for entry in feed.entries[:10]: # 只取前10則
        score = analyze_sentiment(entry.title)
        color = "green" if score > 0 else "red" if score < 0 else "gray"
        sentiment = "看多 🐂" if score > 0 else "看空 🐻" if score < 0 else "中立 😐"
        
        news_html += f"""
        <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="color: #888; font-size: 0.8em;">{entry.published}</div>
            <h3><a href="{entry.link}" style="text-decoration: none; color: #333;">{entry.title}</a></h3>
            <p>情緒判斷: <strong style="color:{color}">{sentiment}</strong> (分數: {score:.2f})</p>
        </div>
        """

    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>新聞多空儀表板</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family: sans-serif; background: #f4f4f4; padding: 20px; max-width: 800px; margin: 0 auto;">
        <h1 style="text-align: center;">📊 即時新聞情緒</h1>
        <p style="text-align: center;">更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        {news_html}
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("網頁生成完畢！")

if __name__ == "__main__":
    main()
