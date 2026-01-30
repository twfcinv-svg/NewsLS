#!/usr/bin/env python
# coding: utf-8

# In[1]:


# 範例概念代碼 (main.py)
import feedparser
from textblob import TextBlob
from datetime import datetime

# 1. 抓取新聞 (這裡示範用 RSS)
rss_url = "http://feeds.marketwatch.com/marketwatch/topstories/"
feed = feedparser.parse(rss_url)

news_items = []
total_sentiment = 0

for entry in feed.entries[:10]: # 取前10則
    # 2. 簡單的情緒分析
    analysis = TextBlob(entry.title)
    sentiment_score = analysis.sentiment.polarity # -1(空) 到 1(多)
    total_sentiment += sentiment_score
    
    # 判斷標籤
    tag = "中立"
    color = "gray"
    if sentiment_score > 0.1:
        tag = "多方 🐂"
        color = "green"
    elif sentiment_score < -0.1:
        tag = "空方 🐻"
        color = "red"
        
    news_items.append(f"""
        <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background: #f9f9f9;">
            <h3>{entry.title}</h3>
            <p><strong>情緒：</strong> <span style="color:{color}">{tag}</span></p>
            <a href="{entry.link}" target="_blank">閱讀更多</a>
        </div>
    """)

# 3. 判斷整體趨勢
market_status = "盤整中"
if total_sentiment > 0.5: market_status = "市場情緒：偏多 🚀"
if total_sentiment < -0.5: market_status = "市場情緒：偏空 📉"

# 4. 生成 HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>新聞多空儀表板</title></head>
<body style="font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
    <h1>📊 {market_status}</h1>
    <p>更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <hr>
    {''.join(news_items)}
</body>
</html>
"""

# 寫入檔案
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)


# In[ ]:




