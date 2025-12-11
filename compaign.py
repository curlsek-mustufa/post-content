import os
import json
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found. Set it in system env or .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate(prompt):
    r = client.completions.create(
        model="gpt-5.1",
        prompt=prompt,
        max_tokens=5000,
        n=1
    )
    return r.choices[0].text.strip()

def extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("JSON not found")
    return json.loads(text[start:end+1])

# Load all campaigns
def load_all_weeks():
    if os.path.exists("all_weeks.json"):
        return json.load(open("all_weeks.json"))
    return {"campaigns": []}

# Append into all_weeks.json
def save_to_all_weeks(data):
    db = load_all_weeks()
    week_number = len(db["campaigns"]) + 1
    entry = {
        "week": week_number,
        "topic": data["topic"],
        "days": data["days"]
    }
    db["campaigns"].append(entry)
    json.dump(db, open("all_weeks.json", "w"), indent=2, ensure_ascii=False)
    return week_number

PROMPT = """
I am part of a B2B SaaS company called CurlSek (https://curlsek.ai). We are an AI powered offensive security product company mainly targeting VAPT and continuous penetration testing. Create a weekly LinkedIn campaign based on a real cybersecurity news event from the last 2 weeks involving AI or a threat where AI fits naturally. Avoid generic topics.

Provide 7 days of content:
Day 1 short post
Day 2 long post
Day 3 carousel script
Day 4 video script
Day 5 analytic post
Day 6 insight post
Day 7 recap post

Each day's post must:
Include a CTA to https://curlsek.ai
Be unique
Contain no emojis or special characters

Output ONLY JSON:

{
  "topic": "MAIN TOPIC",
  "days": [
    { "day": 1, "post_type": "short_post", "content": "..." },
    { "day": 2, "post_type": "long_post", "content": "..." },
    { "day": 3, "post_type": "carousel", "content": "..." },
    { "day": 4, "post_type": "video_script", "content": "..." },
    { "day": 5, "post_type": "analytic_post", "content": "..." },
    { "day": 6, "post_type": "insight_post", "content": "..." },
    { "day": 7, "post_type": "recap_post", "content": "..." }
  ]
}
"""

raw = generate(PROMPT)

try:
    data = extract_json(raw)

    # Save into all_weeks.json (append)
    week_num = save_to_all_weeks(data)

    # Save latest output to current_week.json (overwrite)
    current_week_data = {
        "week": week_num,
        "topic": data["topic"],
        "days": data["days"]
    }
    json.dump(current_week_data, open("current_week.json", "w"), indent=2, ensure_ascii=False)

    print("\nSaved latest campaign to current_week.json")
    print("Appended all campaigns to all_weeks.json")
    print("Week number:", week_num)
    print("\nPreview:\n", json.dumps(current_week_data, indent=2, ensure_ascii=False))

except Exception as e:
    print("\nJSON Error:", e)
    print("\nRaw model output:\n", raw)