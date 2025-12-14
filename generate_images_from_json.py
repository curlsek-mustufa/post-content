import os
import json
import base64
from io import BytesIO

import requests
from PIL import Image


from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found. Set it in system env or .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_JSON = r"D:\Data\post content\current_week.json"   
OUT_DIR = "generated_images"
IMAGE_SIZE = "1024x1024"   
os.makedirs(OUT_DIR, exist_ok=True)



def load_campaign(path):
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return json.load(f)


def extract_hook(text, max_chars=100):
    if not text:
        return "CurlSek.ai"
    t = text.strip()
    if "\n" in t:
        first = t.split("\n", 1)[0].strip()
    else:
        
        first = t.split(".", 1)[0].strip()
    if len(first) > max_chars:
        return first[: max_chars - 3].rstrip() + "..."
    return first


def build_prompt(hook, topic=None):
    
    base = f'''Create a LinkedIn-style cybersecurity image based on the following content:

"{hook}"

Do NOT include any readable text, words, letters, numbers, or logos in the image.
Instead, represent the idea visually using cybersecurity elements such as:
networks, data flows, shields, threat indicators, code patterns, AI visuals, or digital system graphics.

Use a modern blue and dark color theme.
Make the design clean, professional, and appropriate for a LinkedIn post.
Ensure the center has some empty space so a headline can be added later.
Topic: {topic}
'''
    if topic:
        base += f" Topic: {topic}."
    return base


def save_bytes_to_file(b: bytes, path: str):
    with open(path, "wb") as f:
        f.write(b)


def decode_and_save_image(resp_data, out_path):
    """
    Handles typical image API response shapes:
    - base64 in resp_data['b64_json'] or resp_data.b64_json
    - url in resp_data['url']
    """
    
    b64 = None
    url = None

    if isinstance(resp_data, dict):
        b64 = resp_data.get("b64_json") or resp_data.get("b64")
        url = resp_data.get("url")
    else:
        
        b64 = getattr(resp_data, "b64_json", None) or getattr(resp_data, "b64", None)
        url = getattr(resp_data, "url", None)

    if b64:
        img_bytes = base64.b64decode(b64)
        save_bytes_to_file(img_bytes, out_path)
        return out_path

    if url:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        save_bytes_to_file(r.content, out_path)
        return out_path

    raise RuntimeError("Unexpected image response format: " + str(resp_data))


def main():
    campaign = load_campaign(INPUT_JSON)
    topic = campaign.get("topic", "")
    days = campaign.get("days", [])

    for day in days:
        daynum = int(day.get("day", 0))
        post_type = day.get("post_type", "post")
        content = day.get("content", "")
        hook = extract_hook(content, max_chars=90)
        prompt = build_prompt(hook, topic=topic)

        print(f"Day {daynum}: prompt -> {prompt}")

        
        try:
            resp = client.images.generate(prompt=prompt, size=IMAGE_SIZE, n=1)
        except Exception as e:
            print("Image API call failed:", e)
            continue

        
        try:
            resp_data = resp.data[0]
        except Exception as e:
            print("Unexpected response structure:", e)
            continue

        filename = f"week_day{daynum:02d}.png"
        out_path = os.path.join(OUT_DIR, filename)

        try:
            saved_path = decode_and_save_image(resp_data, out_path)
            print("Saved image to", saved_path)

            
            img = Image.open(saved_path)
            
        except Exception as e:
            print("Failed to decode/save image:", e)


if __name__ == "__main__":
    main()