import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
import google.generativeai as genai
import os, json, random, uuid
from dotenv import load_dotenv

# --- 1. CONFIG & MEMORY ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

if "build_queue" not in st.session_state: st.session_state.build_queue = []
if "final_json" not in st.session_state: st.session_state.final_json = None
if "scroll_up" not in st.session_state: st.session_state.scroll_up = False

st.set_page_config(page_title="VowelVault Pro", layout="wide", page_icon="🏫")

# --- 2. PHONICS DATABASE & DESCRIPTIONS ---
PHONICS_MENU = {
    "Mixed Review (All Types)": ["All Patterns Combined"],
    "CVC (Short Vowels)": ["Short A", "Short E", "Short I", "Short O", "Short U", "Mixed Short Vowels"],
    "Consonant Digraphs": ["sh", "ch", "th", "wh", "ck", "Mixed Digraphs"],
    "Consonant Blends": ["L-Blends", "R-Blends", "S-Blends", "Final Blends"],
    "Magic E (CVCe)": ["a-e", "i-e", "o-e", "u-e", "Mixed Magic E"],
    "R-Controlled Vowels": ["ar", "or", "er", "ir", "ur", "Mixed Bossy R"],
    "Predictable Vowel Teams": ["Long A (ai, ay)", "Long E (ee, ea)", "Long O (oa, ow)", "Long I (igh, ie)"],
    "Variant Vowel Teams": ["/ow/ (ou, ow)", "/oy/ (oi, oy)", "/oo/ (oo, ew)", "/aw/ (au, aw)"]
}

ACTIVITY_INFO = {
    "Decodable Story": "📖 Story (3+ paragraphs) & 3 Evidence Check questions.",
    "Nonsense Word Fluency": "🧪 21 pseudo-words with a custom Detective Task at the bottom.",
    "Word Bank Sort": "📊 Word Sort: A Word Bank and columns to categorize words.",
    "Sentence Match": "🔗 Sentence Match: 5 sentence halves to connect.",
    "Sound Mapping": "🟦 Mapping: Segment words into phoneme boxes.",
    "Detective Riddle Cards": "🔍 8 cards per page with 3 logic clues each."
}

# --- 3. CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .builder-card { 
        background: white; padding: 10px; border-radius: 10px; 
        border-top: 5px solid #3b82f6; margin-bottom: 5px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
        min-height: 110px; display: flex; flex-direction: column; justify-content: center;
    }
    .donation-footer {
        background: #ffffff; padding: 25px; border-radius: 15px; 
        text-align: center; margin-top: 50px; border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. THE ARCHITECT SIDEBAR ---
with st.sidebar:
    st.title("🏫 Architect")
    grade = st.selectbox("Grade (Interest)", ["K", "1st", "2nd", "3rd", "4th+"])
    r_level = st.select_slider("Difficulty", options=["Beginning", "Intermediate", "Advanced"])
    
    sel_cat = st.selectbox("Phonics Category", list(PHONICS_MENU.keys()))
    sel_targets = st.multiselect("Specific Targets", PHONICS_MENU[sel_cat], default=[PHONICS_MENU[sel_cat][0]])
    
    st.divider()
    st.subheader("Add Section")
    add_type = st.selectbox("Activity", list(ACTIVITY_INFO.keys()))
    
    with st.popover("❔ What is this?", use_container_width=True):
        st.markdown(ACTIVITY_INFO[add_type])
    
    add_nonsense = st.checkbox("Include Nonsense Words")
    
    if st.button("➕ Add to Plan", use_container_width=True):
        st.session_state.build_queue.append({
            "type": add_type, "nonsense": add_nonsense, "id": str(uuid.uuid4()),
            "cat": sel_cat, "sounds": sel_targets
        })

    if st.button("🗑️ Clear Plan", use_container_width=True):
        st.session_state.build_queue = []
        st.session_state.final_json = None
        st.rerun()

# --- 5. MAIN BUILDER ---
col_plan, col_res = st.columns([1.5, 1])

with col_plan:
    st.header("📝 Worksheet Plan")
    if not st.session_state.build_queue:
        st.info("Queue is empty. Add activities from the sidebar!")
    else:
        for i in range(0, len(st.session_state.build_queue), 4):
            cols = st.columns(4)
            for j in range(4):
                idx = i + j
                if idx < len(st.session_state.build_queue):
                    item = st.session_state.build_queue[idx]
                    with cols[j]:
                        display_name = "Story & Questions" if item['type'] == "Decodable Story" else item['type']
                        st.markdown(f"""<div class='builder-card'>
                            <small style='color:gray;'>#{idx+1}</small>
                            <div style='font-weight:bold; font-size:0.85rem;'>{display_name}</div>
                            <div style='font-size:0.7rem; color:#3b82f6;'>{', '.join(item['sounds'])}</div>
                        </div>""", unsafe_allow_html=True)
                        if st.button("✖️ Remove", key=f"del_{item['id']}", use_container_width=True):
                            st.session_state.build_queue.pop(idx)
                            st.rerun()

    if st.session_state.build_queue:
        if st.button("🚀 GENERATE WORKSHEET", type="primary", use_container_width=True):
            with st.spinner("AI is crafting unique content..."):
                seed = random.randint(1, 1000000)
                targets_text = ", ".join(sel_targets)
                prompt = f"""
                You are an OG Reading Specialist. Create a {grade} worksheet ({r_level} level) targeting {targets_text}.
                Plan: {st.session_state.build_queue}.
                
                STRICT RULES:
                1. Stories MUST be 3+ paragraphs and MUST have unique titles.
                2. Comprehension questions MUST include the 'q' (question) and the 'a' (answer).
                3. NO MARKDOWN ASTERISKS (**). Plain text only.
                4. Nonsense Word Fluency must be exactly 21 decodable pseudo-words. You MUST also provide a 2-step "detective_task" array (e.g., "1. Circle the vowel teams", "2. Underline words with Long E").
                5. ZERO PROFANITY: Rigorously check all generated words (especially pseudo-words) to ensure they do not resemble profanity, slang, or anatomical terms.
                6. Provide exactly 8 distinct riddles for cards.
                7. Output ONLY raw JSON. You MUST use this exact schema:
                {{
                  "overview": "Phonics rule intro", 
                  "target_words": ["word1", "word2"],
                  "activities": [ 
                    {{
                      "type": "Exact Type from Plan", 
                      "content": {{
                         "title": "Story Title",
                         "paragraphs": ["Para 1 text", "Para 2 text"],
                         "questions": [ {{"q": "question here?", "a": "answer here"}} ],
                         "words": ["pseudo1", "pseudo2", "etc (up to 21)"],
                         "detective_task": ["1. Task one", "2. Task two"],
                         "sort_cats": {{"Cat1": ["w1"], "Cat2": ["w2"]}},
                         "match_l": ["Left 1"], "match_r": ["Right 1"],
                         "map_words": ["w1", "w2"],
                         "riddles": [ {{"clue1": "c1", "clue2": "c2", "clue3": "c3", "ans": "a"}} ]
                      }} 
                    }} 
                  ] 
                }}
                Seed: {seed}
                """
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                st.session_state.final_json = json.loads(response.text)
                st.session_state.scroll_up = True

# --- 6. BULLETPROOF PDF ENGINE WITH SANITIZER ---
def clean_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "--", "…": "...", "**": "", "*": ""}
    for bad_char, good_char in replacements.items(): text = text.replace(bad_char, good_char)
    return text

def render_pdf(data, is_key=False):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.add_page()
    if is_key:
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="R"); pdf.set_text_color(0,0,0)
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Name: __________________________________________________", ln=True)
        pdf.ln(2)
    
    pdf.set_font("Helvetica", "B", 14); pdf.cell(0, 10, "Packet Overview", ln=True)
    pdf.set_font("Helvetica", "I", 11); pdf.multi_cell(0, 7, clean_text(data.get("overview", "Read the instructions carefully.")))
    pdf.ln(5)

    first_page = True
    for act in data.get("activities", []):
        if not first_page: pdf.add_page()
        if is_key and not first_page:
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="R"); pdf.set_text_color(0,0,0)
        elif not is_key and not first_page:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, "Name: ___________________________________", ln=True, align="R")
            pdf.ln(2)
        
        first_page = False
        a_type, content = act['type'], act['content']

        if a_type == "Decodable Story":
            title_text = clean_text(content.get('title', 'Decodable Story'))
            pdf.set_font("Helvetica", "B", 22); pdf.cell(0, 15, title_text, ln=True, align="C")
            pdf.set_font("Helvetica", "", 14)
            for para in content.get('paragraphs', []):
                pdf.set_x(15)
                pdf.multi_cell(0, 8, clean_text(para))
                pdf.ln(4)
            
            pdf.ln(5); pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Evidence Check", ln=True)
            pdf.set_font("Helvetica", "", 14)
            for q_data in content.get('questions', []):
                q_text = clean_text(q_data.get('q', str(q_data)) if isinstance(q_data, dict) else str(q_data))
                a_text = clean_text(q_data.get('a', 'Refer to text.') if isinstance(q_data, dict) else 'Refer to text.')
                
                pdf.set_x(15); pdf.set_font("Helvetica", "B", 14); pdf.multi_cell(0, 8, q_text)
                if is_key:
                    pdf.set_x(15); pdf.set_font("Helvetica", "I", 12); pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(0, 7, f"Answer: {a_text}"); pdf.set_text_color(0, 0, 0); pdf.ln(3)
                else:
                    pdf.ln(12)

        elif a_type == "Nonsense Word Fluency":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Decoding Drills (Nonsense Words)", ln=True); pdf.ln(5)
            words = content.get('words', [])[:21]
            for i, word in enumerate(words):
                pdf.set_font("Helvetica", "B", 24)
                pdf.cell(60, 20, clean_text(word), 1, (i + 1) % 3 == 0, 'C')
            
            # THE NEW DETECTIVE TASK BLOCK
            tasks = content.get('detective_task', [])
            if tasks:
                pdf.ln(10)
                pdf.set_x(15)
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 8, "DETECTIVE TASK:", ln=True)
                pdf.set_font("Helvetica", "", 12)
                for task in tasks:
                    pdf.set_x(15)
                    pdf.multi_cell(0, 6, clean_text(task))
                pdf.ln(5)

        elif a_type == "Word Bank Sort":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Activity: Word Sort", ln=True); pdf.ln(2)
            cats = list(content.get('sort_cats', {}).keys())
            
            if cats:
                all_words = []
                for cat_words in content['sort_cats'].values():
                    all_words.extend([clean_text(w) for w in cat_words])
                random.shuffle(all_words)
                
                pdf.set_font("Helvetica", "", 13)
                pdf.multi_cell(0, 8, "Word Bank:  " + "   |   ".join(all_words))
                pdf.ln(5)

                w = 180 / len(cats)
                pdf.set_font("Helvetica", "B", 12)
                for c in cats: pdf.cell(w, 10, clean_text(c), 1, 0, 'C')
                pdf.ln(); pdf.set_font("Helvetica", "", 12)
                
                if not is_key:
                    for _ in range(6):
                        for _ in cats: pdf.cell(w, 12, "", 1, 0)
                        pdf.ln()
                else:
                    max_r = max([len(content['sort_cats'][c]) for c in cats])
                    pdf.set_text_color(200, 0, 0)
                    for r in range(max_r):
                        for c in cats:
                            lst = content['sort_cats'][c]
                            pdf.cell(w, 10, clean_text(lst[r]) if r < len(lst) else "", 1, 0, 'C')
                        pdf.ln()
                    pdf.set_text_color(0, 0, 0)

        elif a_type == "Sentence Match":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Sentence Match", ln=True); pdf.ln(5)
            l, r = content.get('match_l', []), content.get('match_r', [])
            dr = r if is_key else random.sample(r, len(r))
            for i in range(len(l)):
                pdf.set_x(15)
                pdf.set_font("Helvetica", "", 13); pdf.cell(85, 12, clean_text(l[i]), 0, 0)
                pdf.set_font("Courier", "", 10); pdf.cell(10, 12, "....", 0, 0, 'C')
                if is_key: pdf.set_text_color(200, 0, 0)
                pdf.cell(85, 12, clean_text(dr[i]) if i < len(dr) else "", 0, 1, 'R')
                pdf.set_text_color(0, 0, 0)

        elif a_type == "Sound Mapping":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Sound Mapping", ln=True); pdf.ln(5)
            for word in content.get('map_words', []):
                pdf.set_font("Helvetica", "B", 14); pdf.cell(50, 12, f"{clean_text(word)} -> ", 0, 0, 'R')
                if is_key:
                    pdf.set_text_color(200, 0, 0)
                    pdf.cell(60, 12, "(Break word into phonemes)", 0, 1)
                    pdf.set_text_color(0, 0, 0)
                else:
                    pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 1)
                pdf.ln(2)

        elif a_type == "Detective Riddle Cards":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 12, "Detective Riddle Cards", ln=True, align="C")
            cards = content.get('riddles', [])[:8]
            xs, ys = 10, 30
            c_w, c_h = 90, 46 
            for i, r in enumerate(cards):
                col, row = i % 2, i // 2
                x, y = xs + (col * 95), ys + (row * 48) 
                pdf.rect(x, y, c_w, c_h)
                pdf.set_xy(x+2, y+2); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 5, f"Riddle #{i+1}")
                pdf.set_xy(x+2, y+8); pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(c_w-4, 4.5, f"Clue 1: {clean_text(r.get('clue1',''))}\nClue 2: {clean_text(r.get('clue2',''))}\nClue 3: {clean_text(r.get('clue3',''))}")
                if is_key:
                    pdf.set_xy(x, y + c_h - 7)
                    pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(200,0,0)
                    pdf.cell(c_w, 6, f"Ans: {clean_text(r.get('ans',''))}", 0, 0, 'C'); pdf.set_text_color(0,0,0)

    # PAGE: Teacher Reference Page
    if is_key:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16); pdf.cell(0, 10, "Teacher Reference: Target Words", ln=True)
        pdf.set_font("Helvetica", "", 12)
        target_list = ", ".join([clean_text(w) for w in data.get("target_words", [])])
        pdf.multi_cell(0, 8, f"These target words were generated for this specific packet: \n\n{target_list}")

    return bytes(pdf.output())

# --- 7. DOWNLOADS ---
with col_res:
    if st.session_state.final_json:
        st.header("📥 Results Ready")
        spdf = render_pdf(st.session_state.final_json, False)
        tpdf = render_pdf(st.session_state.final_json, True)
        c1, c2 = st.columns(2)
        with c1: st.download_button("📘 Student Packet", spdf, "Student_Worksheet.pdf", use_container_width=True)
        with c2: st.download_button("🗝️ Teacher Key", tpdf, "Teacher_Key.pdf", use_container_width=True)

        if st.session_state.scroll_up:
            components.html(
                "<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>",
                height=0
            )
            st.session_state.scroll_up = False

# --- 8. DONATION ---
st.markdown("<div class='donation-footer'><h3>☕ Support VowelVault</h3><p>Keep this free for teachers!</p><a href='https://venmo.com'>Venmo</a> | <a href='https://paypal.me'>PayPal</a></div>", unsafe_allow_html=True)