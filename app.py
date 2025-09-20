import streamlit as st
import wikipedia
import requests
import os
from dotenv import load_dotenv
from groq import Groq
import tempfile
import pyttsx3 
import base64

# ========== LOAD ENV VARS ==========
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key not found. Please set it in .env file.")
    st.stop()

client = Groq(api_key=api_key)

# ========== CONFIG ==========
st.set_page_config(page_title="AfroFacts / Wetin Happen?", page_icon="🇳🇬", layout="centered")

# ========== TITLE & INTRO ==========
st.title("🇳🇬 AfroFacts")
st.markdown("### Type a Nigerian place, person, or event → Get the TRUE story told like Nollywood 🎬")
st.caption("No fiction. Just facts… with flavor. Made for Nigerian history.")

# ========== INPUT ==========
user_input = st.text_input(
    "Enter a Nigerian town, person, or landmark (e.g., 'Ahmadu Bello', 'Olumo Rock', 'Ibadan'):",
    ""
)

def get_wiki_facts(query):
    query = query.strip()
    if not query:
        return "Empty query provided.", "", []

    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_").title()
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if "extract" in data and data["extract"]:
                facts = data["extract"]
                source_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

                images = []
                if "thumbnail" in data and data["thumbnail"].get("source"):
                    images.append(data["thumbnail"]["source"])
                if "originalimage" in data and data["originalimage"].get("source"):
                    images.append(data["originalimage"]["source"])

                return facts, source_url, images
            else:
                return "No summary available for this topic.", "", []
        else:
            return f"Wikipedia returned status {res.status_code}", "", []
    except Exception as e:
        return f"Error fetching data: {str(e)}", "", []

# ========== HELPER: GPT STORY REWRITER ==========
def generate_naija_story(facts, topic):
    prompt = f"""
You are a Nigerian griot and historian. Your task is to combine two sources:
1. Verified facts from Wikipedia (given below).
2. Your own historical and cultural knowledge about "{topic}".

Then rewrite them into a rich, compelling, 300–500 word story — like a Nollywood trailer or a fireside tale.

STRICT RULES:
- Use BOTH the Wikipedia facts and your own knowledge (but only if relevant and true).
- Must be between 300 and 500 words.
- Keep accuracy: DO NOT invent or add false claims.
- Style: engaging gist with Nigerian flavor — local proverbs, pidgin expressions, Yoruba/Igbo/Hausa sayings when natural.
- Inject emotion, humor, and culture without changing the truth.
- Use 1–2 emojis naturally (not spammy).
- End with a strong, memorable closing line that feels final.
- Finish with this hashtag: #AfroFacts

WIKIPEDIA FACTS:
{facts}

OUTPUT:
Only the story, no disclaimers or explanations.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a master Nigerian griot and history dramatizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Story engine down 😅 Try again or check groq key. Error: {str(e)}"

# ========== HELPER: GENERATE IMAGE ==========
def generate_story_image(topic):
    prompt = f"Nigerian art style, dramatic scene from the history of {topic}, vibrant colors, cultural symbols, no text, cinematic, folklore illustration"
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '+')}"
    return url

# ========== HELPER: OFFLINE TTS ==========
def text_to_speech(story_text, filename="story.mp3"):
    engine = pyttsx3.init()
    # Optional: adjust voice/speed
    engine.setProperty("rate", 160)  # speed
    engine.setProperty("volume", 0.9)  # volume

    # Save to file
    engine.save_to_file(story_text, filename)
    engine.runAndWait()
    return filename

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio autoplay controls>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# ========== MAIN LOGIC ==========
if user_input:
    with st.spinner("🔍 Digging up true Naija facts..."):
        facts, source_url, wiki_images = get_wiki_facts(user_input)

    if "Sorry, no solid facts" not in facts:
        with st.spinner("🎬 Turning facts into blockbuster story..."):
            story = generate_naija_story(facts, user_input)

        st.success("✅ History Ready!")
        st.markdown("### 📖 Your Story:")
        st.write(story)

        # ========== TTS BUTTON ==========
        if st.button("🔊 Listen to Story"):
            with st.spinner("🎶 Generating audio..."):
                filename = text_to_speech(story)
                autoplay_audio(filename)
                st.success("Playing story audio 🎧")

        # ========== IMAGE GENERATION ==========
        if st.button("🖼️ Generate Naija-Style Image"):
            with st.spinner("🎨 Creating image..."):
                image_url = generate_story_image(user_input)
                if image_url:
                    st.image(image_url, caption=f"AI-generated scene from {user_input}", use_column_width=True)
                else:
                    st.error("Image generation failed. Try again later.")

            # ========== WIKIPEDIA IMAGES ==========
            if wiki_images:
                st.markdown("### 🖼️ From the Archives")
                for img in wiki_images:
                    st.image(img, caption=f"Wikipedia image of {user_input}", use_column_width=True)

        # ========== TOGGLE: SHOW SOURCES ==========
        with st.expander("🔍 Show True Sources"):
            st.write("**Raw Facts from Wikipedia:**")
            st.write(facts)
            st.markdown(f"**Source:** [{source_url}]({source_url})")

    else:
        st.error(facts)

# ========== FOOTER ==========
st.markdown("---")
st.caption("Reviving history, one AI story at a time.")
st.caption("AfroFacts — Wetin Happen for Your Village?")
