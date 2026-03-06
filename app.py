from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import anthropic
import json
import os

st.set_page_config(page_title="AI Study Generator", page_icon="🎓", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0a1a 0%, #0d1117 100%); }
h1 { background: linear-gradient(135deg, #8B5CF6, #4ECDC4); -webkit-background-clip: text;
     -webkit-text-fill-color: transparent; font-size: 2.8rem !important;
     font-weight: 800 !important; text-align: center; }
.subtitle { text-align:center; color:rgba(255,255,255,0.4); font-size:1rem; margin-bottom:2rem; }
.flashcard-front { background: linear-gradient(135deg,rgba(139,92,246,0.2),rgba(59,130,246,0.15));
    border:1px solid rgba(139,92,246,0.4); border-radius:16px; padding:1.5rem; margin:0.8rem 0; }
.flashcard-answer { background: linear-gradient(135deg,rgba(78,205,196,0.2),rgba(139,92,246,0.15));
    border:1px solid rgba(78,205,196,0.4); border-radius:16px; padding:1.5rem; margin:0.5rem 0; }
.score-box { background:linear-gradient(135deg,rgba(139,92,246,0.2),rgba(78,205,196,0.15));
    border:1px solid rgba(139,92,246,0.4); border-radius:20px; padding:2rem; text-align:center; }
.section-heading { color:#8B5CF6; font-size:1.1rem; font-weight:700; margin-top:1.2rem; }
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #8B5CF6, #3B82F6) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    font-weight: 700 !important; font-size: 1rem !important; width: 100%; }
div[data-testid="stButton"] button:hover { box-shadow: 0 0 24px rgba(139,92,246,0.5) !important; }
.stTextInput input { background:rgba(255,255,255,0.05) !important;
    border:1px solid rgba(255,255,255,0.15) !important; border-radius:12px !important; color:white !important; }
.stSelectbox label, .stTextInput label { color:rgba(255,255,255,0.7) !important;
    font-weight:600 !important; letter-spacing:1px !important;
    font-size:0.8rem !important; text-transform:uppercase !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def build_prompt(topic, subject, mode, difficulty):
    prompts = {
        "flashcards": f'Create 6 flashcards about "{topic}" for {subject} at {difficulty} level. Return ONLY valid JSON: {{"cards": [{{"q": "question", "a": "answer"}}]}}',
        "quiz": f'Create 5 MCQ about "{topic}" for {subject} at {difficulty}. Return ONLY valid JSON: {{"questions": [{{"q": "question", "options": ["A","B","C","D"], "correct": 0, "explanation": "why"}}]}} correct=0-based index.',
        "summary": f'Study summary about "{topic}" for {subject} at {difficulty}. Return ONLY valid JSON: {{"title":"...","overview":"...","sections":[{{"heading":"...","content":"...","bullets":["..."]}}]}}',
        "code": f'3 code examples for "{topic}" in {subject} at {difficulty}. Return ONLY valid JSON: {{"examples":[{{"title":"...","language":"python","code":"...","explanation":"...","output":"..."}}]}}',
    }
    return prompts[mode]

def call_api(topic, subject, mode, difficulty):
    client = get_client()
    message = client.messages.create(
        model="claude-opus-4-6", max_tokens=1500,
        messages=[{"role": "user", "content": build_prompt(topic, subject, mode, difficulty)}]
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return json.loads(raw.strip())

def show_flashcards(data):
    cards = data.get("cards", [])
    st.markdown(f"### 🃏 {len(cards)} Flashcards")
    for i, card in enumerate(cards, 1):
        with st.expander(f"Card {i} — Click to Open", expanded=False):
            st.markdown(f'<div class="flashcard-front"><div style="color:#8B5CF6;font-size:0.75rem;letter-spacing:2px;font-weight:700;margin-bottom:8px">❓ QUESTION</div><div style="color:white;font-size:1.1rem;font-weight:600">{card["q"]}</div></div><div class="flashcard-answer"><div style="color:#4ECDC4;font-size:0.75rem;letter-spacing:2px;font-weight:700;margin-bottom:8px">✅ ANSWER</div><div style="color:rgba(255,255,255,0.9);font-size:1rem;line-height:1.6">{card["a"]}</div></div>', unsafe_allow_html=True)

def show_quiz(data):
    questions = data.get("questions", [])
    st.markdown(f"### 📝 Quiz — {len(questions)} Questions")
    if "quiz_answers" not in st.session_state: st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}: {q['q']}**")
        if not st.session_state.quiz_submitted:
            answer = st.radio("", q["options"], key=f"q_{i}", index=None, label_visibility="collapsed")
            if answer: st.session_state.quiz_answers[i] = q["options"].index(answer)
        else:
            selected = st.session_state.quiz_answers.get(i)
            for j, opt in enumerate(q["options"]):
                if j == q["correct"]: st.success(f"✅ {opt}")
                elif selected == j: st.error(f"❌ {opt}")
                else: st.markdown(f"&nbsp;&nbsp;{opt}")
            st.info(f"💡 {q['explanation']}")
        st.markdown("---")
    if not st.session_state.quiz_submitted:
        if st.button("Submit Quiz ✨"): st.session_state.quiz_submitted = True; st.rerun()
    else:
        score = sum(1 for i,q in enumerate(questions) if st.session_state.quiz_answers.get(i)==q["correct"])
        pct = (score/len(questions))*100
        emoji = "🏆" if pct>=80 else "👍" if pct>=50 else "📚"
        grade = "Excellent!" if pct>=80 else "Good job!" if pct>=50 else "Keep studying!"
        st.markdown(f'<div class="score-box"><div style="font-size:3rem">{emoji}</div><div style="font-size:2rem;font-weight:800;color:white">{score}/{len(questions)}</div><div style="font-size:1.2rem;color:#8B5CF6;font-weight:700">{pct:.0f}% — {grade}</div></div>', unsafe_allow_html=True)
        if st.button("🔄 Retry Quiz"): st.session_state.quiz_answers={}; st.session_state.quiz_submitted=False; st.rerun()

def show_summary(data):
    st.markdown(f"### 📋 {data.get('title','Study Summary')}")
    if data.get("overview"): st.info(data["overview"])
    for sec in data.get("sections", []):
        st.markdown(f'<div class="section-heading">◆ {sec["heading"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:rgba(255,255,255,0.75);line-height:1.7">{sec.get("content","")}</div>', unsafe_allow_html=True)
        for b in sec.get("bullets",[]): st.markdown(f"▸ {b}")
        st.markdown("---")

def show_code(data):
    examples = data.get("examples", [])
    st.markdown(f"### 💻 {len(examples)} Code Examples")
    tabs = st.tabs([f"Example {i+1}: {e['title']}" for i,e in enumerate(examples)])
    for tab, ex in zip(tabs, examples):
        with tab:
            st.markdown(f"**{ex['explanation']}**")
            st.code(ex["code"], language=ex.get("language","python"))
            if ex.get("output"): st.markdown("**Expected Output:**"); st.code(ex["output"], language="text")

# ── Main UI ──
st.markdown("<h1>🎓 AI Study Generator</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Powered by Claude AI — Generate study materials instantly</div>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([2,1])
with col1: topic = st.text_input("📚 Study Topic", placeholder="e.g. Python loops, World War II...")
with col2: subject = st.selectbox("📖 Subject", ["Programming","Mathematics","Science","History","Physics","Language Arts"])

col3, col4 = st.columns(2)
with col3: mode = st.selectbox("🎯 Study Mode", ["flashcards","quiz","summary","code"])
with col4: difficulty = st.selectbox("⚡ Difficulty", ["Beginner","Intermediate","Advanced","Expert"])

st.markdown("")
if st.button("✨ Generate Study Material"):
    if not topic.strip(): st.warning("⚠️ Please enter a study topic!")
    elif not os.environ.get("ANTHROPIC_API_KEY") or "ఇక్కడ" in os.environ.get("ANTHROPIC_API_KEY",""):
        st.error("❌ .env file లో real API Key పెట్టు! console.anthropic.com లో తీసుకో.")
    else:
        with st.spinner(f"🤖 Generating {mode} for '{topic}'..."):
            try:
                data = call_api(topic, subject, mode, difficulty)
                st.success("✅ Generated successfully!")
                st.markdown("---")
                {"flashcards": show_flashcards, "quiz": show_quiz, "summary": show_summary, "code": show_code}[mode](data)
            except json.JSONDecodeError: st.error("❌ Could not parse response. Try again.")
            except anthropic.AuthenticationError: st.error("❌ Invalid API Key! .env file check చెయ్యి.")
            except Exception as e: st.error(f"❌ Error: {str(e)}")

st.markdown("---")
st.markdown('<div style="text-align:center;color:rgba(255,255,255,0.2);font-size:0.8rem">Built with Claude AI + Streamlit</div>', unsafe_allow_html=True)
