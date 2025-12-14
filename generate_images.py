import os
import json
import base64
from io import BytesIO

import requests
from PIL import Image


from dotenv import load_dotenv
from google import genai
from google.genai import types 

load_dotenv() 


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    
    raise RuntimeError("GEMINI_API_KEY not found. Set it in system env or .env file.")


client = genai.Client(api_key=GEMINI_API_KEY)


IMAGE_MODEL = "gemini-2.5-flash-image"
IMAGE_ASPECT_RATIO = "1:1" 

INPUT_JSON = r"D:\Data\post content\current_week.json"  
OUT_DIR = "generated_images"
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
    
    base = f'''Create a high-quality cybersecurity-themed background image inspired by the following content:

"{hook}"

Translate the meaning of the content into visual concepts. Use elements such as AI-driven attacks, malware evolution, automated phishing, code patterns, neural-network shapes, data flows, network graphs, digital shields, exploit chains, or reconnaissance visuals — whichever best represents the idea of the content.

Important:
- Do NOT include any readable text, letters, numbers, or logos.
- Do NOT show human faces.
- Use a modern, dark-blue professional cybersecurity style.
- The image should look like a LinkedIn banner background.
- Keep the center area clean so a headline can be added later.

Topic: "{topic}"

'''
    if topic:
        base += f" Topic: {topic}."
    return base


def save_bytes_to_file(b: bytes, path: str):
    with open(path, "wb") as f:
        f.write(b)


def decode_and_save_image(resp_data, out_path):
    """
    Handles Google Gen AI (Gemini Image model) response.
    The response structure is slightly different for the Gemini Image model.
    It returns a generate_content response with an Image Part.
    """
    if hasattr(resp_data, 'inline_data') and hasattr(resp_data.inline_data, 'data'):
        
        img_bytes = base64.b64decode(resp_data.inline_data.data)
        save_bytes_to_file(img_bytes, out_path)
        return out_path

    raise RuntimeError("Unexpected image response format from Gemini Image API.")


def main():
    campaign = load_campaign(INPUT_JSON)
    topic = campaign.get("topic", "")
    days = campaign.get("days", [])

    
    image_config = types.ImageConfig(
        aspect_ratio=IMAGE_ASPECT_RATIO,
    )
    
    
    content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=image_config
    )

    for day in days:
        daynum = int(day.get("day", 0))
        post_type = day.get("post_type", "post")
        content = day.get("content", "")
        hook = extract_hook(content, max_chars=90)
        prompt = build_prompt(hook, topic=topic)

        print(f"Day {daynum}: prompt -> {prompt}")

        
        try:
            
            resp = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=[prompt],
                config=content_config
            )
        except Exception as e:
            print("Image API call failed:", e)
            continue

        
        try:
            
            resp_data = resp.parts[0]
        except Exception as e:
            print("Unexpected response structure or no image part found:", e)
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