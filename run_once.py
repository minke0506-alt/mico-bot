import anthropic
import feedparser
import asyncio
from datetime import datetime
from telegram import Bot
import os
from dart_tracker import fetch_dart_disclosures, format_dart_for_claude, classify_importance

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

RSS_FEEDS = [
    "https://www.hankyung.com/feed/finance",
    "https://rss.etnews.com/Section901.xml",
]

def fetch_news():
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", "")[:500],
                "link": entry.link
            })
    return articles

def summarize_news(articles):
    if not articles:
        return "수집된 뉴스 없음"
    news_text = "\n\n".join([f"제목: {a['title']}\n내용: {a['summary']}" for a in articles])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": f"다음 주식/금융 뉴스들을 한국 개인투자자 관점에서 핵심만 요약해줘. 각 뉴스별로 3줄 이내로, 투자에 미치는 영향을 중심으로 작성해줘. 이모지를 적절히 사용해서 가독성 좋게 만들어줘.\n\n{news_text}"}]
    )
    return message.content[0].text

def summarize_dart(disclosures):
    dart_text = format_dart_for_claude(disclosures)
    if not dart_text:
        return "신규 공시 없음"
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": f"미코(059090)의 DART 공시 목록이야. 각 공시가 주가와 투자에 어떤 의미인지 간결하게 설명해줘. HIGH 등급 공시는 특히 자세하게, 일반 공시는 한 줄로. 에너지/반도체 투자자 관점에서 작성해줘.\n\n{dart_text}"}]
    )
    return message.content[0].text

async def main():
    articles = fetch_news()
    disclosures = fetch_dart_disclosures(days_back=1)

    news_summary = summarize_news(articles)
    dart_summary = summarize_dart(disclosures)

    msg = (
        f"☀️ *브리핑 - {datetime.today().strftime('%m/%d')}*\n\n"
        f"━━━ 📰 시장 뉴스 ━━━\n{news_summary}\n\n"
        f"━━━ 📂 미코 공시 ━━━\n{dart_summary}"
    )
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")
    print("전송 완료!")

if __name__ == "__main__":
    asyncio.run(main())
