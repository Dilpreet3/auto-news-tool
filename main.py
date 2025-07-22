import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Load API Keys from env
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")


def get_trending_news():
    url = f"https://gnews.io/api/v4/top-headlines?lang=en&country=in&max=5&apikey={GNEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print("🛑 GNews API Error:", response.text)
        return []
    return response.json().get("articles", [])


def get_image(query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1}
    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    if data.get("photos"):
        return data['photos'][0]['src']['large']
    return None


def create_image_with_text(text, image_url, filename):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    img = img.resize((1080, 1080))

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 100))  # semi-transparent dark overlay
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", size=42)
    except:
        font = ImageFont.load_default()

    # Word wrap
    margin = 40
    lines = []
    words = text.split()
    line = ""
    for word in words:
        if font.getsize(line + " " + word)[0] > img.width - 2 * margin:
            lines.append(line)
            line = word
        else:
            line += " " + word
    lines.append(line)

    # Draw text
    y = img.height - (len(lines) * 50) - margin
    for line in lines:
        draw.text((margin, y), line.strip(), font=font, fill="white")
        y += 50

    if not os.path.exists("output"):
        os.makedirs("output")
    img.convert("RGB").save(filename)


def post_to_facebook(image_path, caption):
    print("📤 Posting to Facebook:", caption)
    with open(image_path, "rb") as img:
        files = {"source": img}
        data = {
            "caption": caption,
            "access_token": FB_PAGE_TOKEN
        }
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        response = requests.post(url, files=files, data=data)
        print("✅ Facebook response:", response.json())


def main():
    news = get_trending_news()
    for i, item in enumerate(news):
        headline = item.get('title')
        print(f"\n[{i + 1}] {headline}")
        keyword = headline.split(" ")[0] if headline else "India"
        image_url = get_image(keyword)
        output_path = f"output/news_{i + 1}.jpg"

        if image_url and headline:
            create_image_with_text(headline, image_url, output_path)
            post_to_facebook(output_path, headline)
        else:
            print("⚠️ No image or headline found for:", keyword)


if __name__ == "__main__":
    main()
