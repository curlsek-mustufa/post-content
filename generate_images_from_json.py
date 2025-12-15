import os
import json
import requests
from openai import OpenAI
from PIL import Image

# =========================
# CONFIG
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found")

client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_JSON = r"D:\Data\post content\current_week.json"
OUT_DIR = "generated_images"
IMAGE_SIZE = "1024x1024"

LOGO_PATH = r"D:\Data\post content\curlsek_logo.jpeg"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# LOAD CAMPAIGN
# =========================
def load_campaign(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return json.load(f)

# =========================
# SAFE TOPIC NORMALIZATION (PERMANENT)
# =========================
SAFE_TOPIC_MAP = {
    "phishing": "digital communication security",
    "malware": "system integrity protection",
    "ransomware": "data availability and resilience",
    "breach": "data exposure risk management",
    "attack": "unauthorized system interaction",
    "hacking": "unauthorized system interaction",
    "exploit": "system weakness exposure",
    "pentest": "security validation processes",
    "vapt": "continuous security assessment",
    "api": "application interface security",
    "ai": "intelligent system monitoring",
    "llm": "automated decision systems",
    "zero trust": "access control architecture",
    "cloud": "distributed infrastructure protection",
}

DEFAULT_CATEGORY = "modern cybersecurity infrastructure protection"

# =========================
# SAFE VISUAL ABSTRACTIONS
# =========================
SAFE_VISUAL_CONCEPTS = {
    "digital communication security":
        "abstract digital communication flows passing through an intelligent filtering layer",

    "system integrity protection":
        "unstable digital signals stabilizing within a protected computing environment",

    "data availability and resilience":
        "secured digital assets remaining accessible within a reinforced system",

    "data exposure risk management":
        "sensitive digital information contained within layered security boundaries",

    "unauthorized system interaction":
        "external digital signals interacting with a protected system perimeter",

    "system weakness exposure":
        "highlighted structural weaknesses within a complex digital system",

    "security validation processes":
        "a digital system undergoing continuous structural verification",

    "continuous security assessment":
        "automated analysis layers evaluating a complex digital environment",

    "application interface security":
        "controlled data connections passing through a regulated gateway",

    "intelligent system monitoring":
        "an advanced intelligence core observing interconnected digital systems",

    "automated decision systems":
        "machine-driven analysis shaping digital operations",

    "access control architecture":
        "layered access zones protecting critical digital resources",

    "distributed infrastructure protection":
        "secured cloud-based systems operating across connected environments",
}

# =========================
# MASTER IMAGE PROMPT (IMMUTABLE)
# =========================
MASTER_IMAGE_PROMPT = """
Create a high-quality cybersecurity visual illustration.

This image is intended for editorial, technical, or research-oriented content.
It must be neutral, abstract, and informational.

Visual Concept:
{visual_concept}

Style:
- cinematic digital illustration or semi-realistic tech art
- abstract representation of cybersecurity systems
- dark professional background
- controlled lighting with subtle glow
- realistic proportions
- not cartoon
- not flat vector
- not promotional

Color Palette:
- deep blues, teals, and greens
- minimal red used only as abstract signal contrast
- dark navy or black background

Composition:
- one clear abstract idea
- minimal visual noise
- strong central focus
- balanced negative space

Strict Rules:
- no readable text
- no letters
- no numbers
- no logos
- no brand names
- no warning symbols
- no dashboards
- no charts
- no infographics

Mood:
- analytical
- technical
- calm
- authoritative
- trustworthy
"""

# =========================
# BUILD SAFE PROMPT (AUTOMATIC)
# =========================
def build_prompt(topic: str):
    t = topic.lower()
    category = DEFAULT_CATEGORY

    for key, mapped_category in SAFE_TOPIC_MAP.items():
        if key in t:
            category = mapped_category
            break

    visual_concept = SAFE_VISUAL_CONCEPTS.get(
        category,
        "a protected digital infrastructure operating within a secure environment"
    )

    return MASTER_IMAGE_PROMPT.format(visual_concept=visual_concept)

# =========================
# SAVE IMAGE (DALL·E URL)
# =========================
def save_image(resp_data, out_path):
    r = requests.get(resp_data.url, timeout=30)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)

# =========================
# LOGO: REMOVE WHITE BG, PRESERVE COLORS
# =========================
def load_logo_transparent(path, target_width):
    logo = Image.open(path).convert("RGBA")
    pixels = logo.getdata()
    new_pixels = []

    for r, g, b, a in pixels:
        # remove white background
        if r > 245 and g > 245 and b > 245:
            new_pixels.append((255, 255, 255, 0))
        # convert dark text to white
        elif r < 80 and g < 80 and b < 80:
            new_pixels.append((255, 255, 255, a))
        else:
            new_pixels.append((r, g, b, a))

    logo.putdata(new_pixels)
    scale = target_width / logo.size[0]
    logo = logo.resize((target_width, int(logo.size[1] * scale)), Image.LANCZOS)
    return logo

# =========================
# ADD CURLSEK WATERMARK ONLY
# =========================
def add_watermark(image_path):
    base = Image.open(image_path).convert("RGBA")
    w, h = base.size

    logo = load_logo_transparent(LOGO_PATH, int(w * 0.18))
    base.paste(
        logo,
        (w - logo.width - 40, h - logo.height - 40),
        logo
    )

    base.convert("RGB").save(image_path, "PNG")

# =========================
# MAIN
# =========================
def main():
    campaign = load_campaign(INPUT_JSON)
    topic = campaign.get("topic", "Cybersecurity")

    for day in campaign.get("days", []):
        day_num = int(day.get("day", 0))
        print(f"Generating Day {day_num}")

        prompt = build_prompt(topic)

        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=IMAGE_SIZE,
            n=1
        )

        out_path = os.path.join(OUT_DIR, f"week_day{day_num:02d}.png")
        save_image(resp.data[0], out_path)
        add_watermark(out_path)

        print("✅ Saved:", out_path)

if __name__ == "__main__":
    main()
