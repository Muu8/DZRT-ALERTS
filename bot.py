import os
import aiohttp
import random
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio

# إعداد القيم الأساسية من البيئة المحيطة
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')'

if not bot_token or not chat_id:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

bot = Bot(bot_token)

initial_check_interval = 0.5  # تقليل الفاصل الزمني للتأكد من توفر المنتجات بشكل أسرع
extended_check_interval = 0.5  # زيادة الفاصل الزمني عند العثور على توفر المنتجات لتجنب الطلبات المتكررة
product_url = "https://www.dzrt.com/ar/our-products.html"

last_availability = {}

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML، مثل Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML، مثل Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML، مثل Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML، مثل Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"
]

async def check_product_availability(session, url):
    global last_availability
    headers = {
        "User-Agent": random.choice(user_agents)
    }
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            html = await response.text()
            print("Fetched page successfully")  # رسالة تشخيصية
    except aiohttp.ClientError as e:
        print(f"Failed to fetch the page: {e}")
        return
    
    soup = BeautifulSoup(html, 'html.parser')
    product_items = soup.select("li.item.product.product-item")
    print(f"Found {len(product_items)} products on the page")  # رسالة تشخيصية
    
    for index, item in enumerate(product_items):
        product_name_tag = item.find("a", {"class": "product-item-link"})
        product_link_tag = item.find("a", {"class": "product-item-photo"})
        if product_name_tag and product_link_tag:
            product_name = product_name_tag.text.strip()
            product_link = product_link_tag.get("href")
            availability = "unavailable" not in item["class"]
            
            if product_name not in last_availability or last_availability[product_name] != availability:
                last_availability[product_name] = availability
                if availability:
                    print(f"Product '{product_name}' is now available at position {index}.")
                    try:
                        await bot.send_message(chat_id=chat_id, text=f' {product_name} متوفرة الآن \n {product_link}')
                    except Exception as e:
                        print(f"Failed to send message: {e}")
                else:
                    print(f"Product '{product_name}' is now unavailable at position {index}.")
            else:
                print(f"Product '{product_name}' availability unchanged.")
        else:
            print(f"Product name or link not found for item at position {index}.")

async def main():
    async with aiohttp.ClientSession() as session:
        check_interval = initial_check_interval
        while True:
            await check_product_availability(session, product_url)
            if any(last_availability.values()):
                check_interval = extended_check_interval
            else:
                check_interval = initial_check_interval
            await asyncio.sleep(check_interval)

if __name__ == "__main__":
    asyncio.run(main())
