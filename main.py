import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("FB_PAGE_ID")

def get_trending_news():
    url = f"https://gnews.io/api/v4/top-headlines?lang=en&country=in&max=3&apikey={GNEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Error from GNews:", response.text)
        return []
    return response.json().get("articles", [])

def create_image_with_text(text, image_url, filename):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        print("⚠️ Could not load image, using fallback")
        img = Image.new("RGBA", (1080, 1080), color=(30, 30, 30, 255))

    img = img.resize((1080, 1080))
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 100))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", size=42)
    except:
        font = ImageFont.load_default()

    # Word wrapping (uses textlength, works with Pillow 11+)
    margin = 40
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = line + " " + word if line else word
        text_width = draw.textlength(test_line, font=font)
        if text_width > img.width - 2 * margin:
            lines.append(line)
            line = word
        else:
            line = test_line
    lines.append(line)

    # Draw text on image
    y = img.height - (len(lines) * 50) - margin
    for line in lines:
        draw.text((margin, y), line.strip(), font=font, fill="white")
        y += 50

    if not os.path.exists("output"):
        os.makedirs("output")

    output_path = os.path.join("output", filename)
    img.convert("RGB").save(output_path)
    return output_path

def upload_photo_to_facebook(image_path, caption):
    url = f"https://graph.facebook.com/{PAGE_ID}/photos"
    files = {'source': open(image_path, 'rb')}
    data = {
        'caption': caption,
        'access_token': PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, files=files, data=data)
    if response.status_code == 200:
        print("✅ Posted successfully:", response.json().get("post_id"))
    else:
        print("❌ Facebook post failed:", response.text)

def main():
    news_items = get_trending_news()
    for index, article in enumerate(news_items):
        headline = article.get("title", "No Title")
        image_url = article.get("image", "")
        print(f"[{index+1}] {headline}")
        output_path = f"news_{index}.jpg"
        create_image_with_text(headline, image_url, output_path)
        upload_photo_to_facebook(output_path, headline)

if __name__ == "__main__":
    main()
