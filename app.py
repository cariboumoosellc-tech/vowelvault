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
if "just_generated" not in st.session_state: st.session_state.just_generated = False

# ==========================================
# 🎨 BRANDING SECTION
# ==========================================
APP_NAME = "WIN Time Phonics Builder"
APP_EMOJI = "✨" 
SIDEBAR_TITLE = "📐 Architect Tools"
FOOTER_TEXT = "🚀 WIN Time Phonics v2.5"

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon=APP_EMOJI)

# --- 2. PHONICS DATABASE ---
PHONICS_MENU = {
    "Mixed Review (All Types)": ["All Patterns Combined"],
    "CVC (Short Vowels)": ["Short A", "Short E", "Short I", "Short O", "Short U", "Mixed Short Vowels"],
    "Consonant Digraphs": ["sh", "ch", "th", "wh", "ck", "Mixed Digraphs"],
    "Consonant Blends": ["L-Blends", "R-Blends", "S-Blends", "Final Blends"],
    "Magic E (CVCe)": ["a-e", "i-e", "o-e", "u-e", "Mixed Magic E"],
    "Vowel r": ["ar", "or", "er", "ir", "ur", "Mixed Vowel r"],
    "Predictable Vowel Teams": ["Long A (ai, ay)", "Long E (ee, ea)", "Long O (oa, ow)", "Long I (igh, ie)"],
    "Variant Vowel Teams": ["/ow/ (ou, ow)", "/oy/ (oi, oy)", "/oo/ (oo, ew)", "/aw/ (au, aw)"],
    "Multisyllable": ["closed/closed", "silent e", "open", "vowel team", "consonant le", "vowel r"],
    "Endings": ["ed", "ing", "s", "es", "er", "est"]
}

ACTIVITY_INFO = {
    "Decodable Story": "📖 Story (3+ paragraphs) & 3 Evidence Check questions.",
    "Nonsense Word Fluency": "🧪 21 pseudo-words with a custom Detective Task.",
    "Word Bank Sort": "📊 Word Sort: A Word Bank and columns to categorize words.",
    "Sentence Match": "🔗 Sentence Match: 5 sentence halves to connect.",
    "Sound Mapping": "🟦 Mapping: Segment words into phoneme boxes.",
    "Detective Riddle Cards": "🔍 8 cards per page with 3 logic clues each.",
    "Mystery Grid (Color-by-Code)": "🎨 FULL-PAGE 8x8 Aztec/Quilt geometric grid."
}

# --- 3. PREMIUM UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
    .builder-card { 
        background: #ffffff; padding: 20px; border-radius: 16px; 
        border-top: 6px solid #6366f1; margin-bottom: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); text-align: center;
        min-height: 120px; display: flex; flex-direction: column; justify-content: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .builder-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    .empty-state {
        background-color: transparent; border: 2px dashed #cbd5e1;
        border-radius: 16px; padding: 40px 20px; text-align: center;
        color: #64748b; margin-top: 20px;
    }
    .success-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0; border-radius: 16px; padding: 25px 20px;
        text-align: center; margin-top: 20px; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important; font-weight: bold !important; border-radius: 8px !important;
        border: none !important; box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2) !important;
        transition: transform 0.1s ease !important;
    }
    button[kind="primary"]:hover { transform: scale(1.02) !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. PDF GENERATORS ---
def generate_tracker_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Skill Mastery Tracker", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Student: _________________________________", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(220, 230, 245)
    pdf.cell(100, 10, " Phonics Skill", 1, 0, 'L', fill=True)
    pdf.cell(30, 10, "Practice", 1, 0, 'C', fill=True)
    pdf.cell(30, 10, "Pass-Off", 1, 0, 'C', fill=True)
    pdf.cell(30, 10, "Initials", 1, 1, 'C', fill=True)
    
    skills = [
        ("Letter Names & Sounds", False), ("Short Vowels (CVC)", False),
        ("Consonant Blends", False), ("Digraphs", False),
        ("Final Blends", False), ("Silent e (CVCe)", False),
        ("Vowel Teams", False), ("R-Controlled Vowels", False),
        ("MULTISYLLABLE", True), ("   - closed/closed", False), ("   - silent e", False), 
        ("   - open", False), ("   - vowel team", False), ("   - consonant le", False), ("   - vowel r", False),
        ("ENDINGS", True), ("   - ed", False), ("   - ing", False), ("   - s", False), 
        ("   - es", False), ("   - er", False), ("   - est", False),
        ("High-Frequency Words", False)
    ]
    
    row_count = 0
    for s, is_h in skills:
        if is_h:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(235, 235, 235)
            pdf.cell(190, 8, f" {s}", 1, 1, 'L', fill=True)
            row_count = 0
        else:
            pdf.set_font("Helvetica", "", 10)
            if row_count % 2 == 0:
                pdf.set_fill_color(250, 250, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(100, 8, f" {s}", 1, 0, 'L', fill=True)
            pdf.cell(30, 8, "", 1, 0, 'C', fill=True)
            pdf.cell(30, 8, "", 1, 0, 'C', fill=True)
            pdf.cell(30, 8, "", 1, 1, 'C', fill=True)
            row_count += 1
    return bytes(pdf.output())

def get_color_rgb(color_name):
    c = str(color_name).lower().strip()
    colors = {
        "red": ((255, 180, 180), (0,0,0)), "blue": ((180, 210, 255), (0,0,0)),
        "green": ((180, 255, 180), (0,0,0)), "yellow": ((255, 255, 180), (0,0,0)),
        "orange": ((255, 220, 180), (0,0,0)), "purple": ((220, 180, 255), (0,0,0)),
        "pink": ((255, 200, 230), (0,0,0)), "brown": ((210, 190, 170), (0,0,0))
    }
    return colors.get(c, ((255,255,255), (0,0,0)))

# --- 5. SIDEBAR ARCHITECT ---
with st.sidebar:
    st.title(SIDEBAR_TITLE)
    with st.container():
        st.subheader("1. Setup Profile")
        grade = st.selectbox("📚 Grade Level", ["1st", "2nd", "3rd", "4th+"])
        r_level = st.select_slider("🧠 Difficulty", options=["Beginning", "Intermediate", "Advanced"])
    st.divider()
    with st.container():
        st.subheader("2. Choose Skills")
        sel_cat = st.selectbox("🎯 Phonics Category", list(PHONICS_MENU.keys()))
        sel_targets = st.multiselect("📌 Specific Targets", PHONICS_MENU[sel_cat], default=[PHONICS_MENU[sel_cat][0]])
    st.divider()
    with st.container():
        st.subheader("3. Add Activities")
        add_type = st.selectbox("🧩 Activity Type", list(ACTIVITY_INFO.keys()))
        add_nonsense = st.checkbox("🧪 Include Nonsense Words", value=(add_type in ["Nonsense Word Fluency", "Mystery Grid (Color-by-Code)"]))
        if st.button("➕ Add to Worksheet Plan", use_container_width=True):
            st.session_state.build_queue.append({
                "type": add_type, "nonsense": add_nonsense, "id": str(uuid.uuid4()),
                "cat": sel_cat, "sounds": sel_targets
            })
    st.divider()
    st.subheader("⚡ Quick Actions")
    if st.button("🪄 Auto-Build Full Packet", use_container_width=True):
        st.session_state.build_queue = []
        grade_logic = {"1st": ["CVC (Short Vowels)", "Consonant Digraphs"], "2nd": ["Magic E (CVCe)", "Vowel r"], 
                       "3rd": ["Multisyllable", "Endings"], "4th+": ["Multisyllable", "Endings"]}
        acts = list(ACTIVITY_INFO.keys())
        random.shuffle(acts)
        for act in acts[:5]:
            cat = random.choice(grade_logic[grade])
            st.session_state.build_queue.append({"type": act, "nonsense": (act=="Nonsense Word Fluency"), "id": str(uuid.uuid4()), "cat": cat, "sounds": [random.choice(PHONICS_MENU[cat])]})
        st.rerun()

    if st.button("🗑️ Clear Plan", use_container_width=True):
        st.session_state.build_queue = []; st.session_state.final_json = None; st.rerun()

    st.divider()
    st.markdown("""
        <div style="background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <h3 style="margin-top:0; color: #1e293b; font-size: 1.1rem;">☕ Support the App</h3>
            <p style="font-size: 13px; color: #64748b; margin-bottom: 15px;">If you love generating WIN Time interventions, consider donating to keep this tool free!</p>
            <div style="display: flex; justify-content: center; gap: 10px;">
                <a href="https://venmo.com/u/BRADONI" target="_blank" style="background: #008CFF; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 12px; transition: 0.2s;">Venmo</a>
                <a href="https://paypal.me/WINTIMEPHONIX" target="_blank" style="background: #003087; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 12px; transition: 0.2s;">PayPal</a>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.caption(FOOTER_TEXT)

# --- 6. HEADER ---
c1, c2 = st.columns([3, 1])
with c1: 
    st.title("✨ Welcome to WIN Time Phonics")
    st.markdown("Build targeted, data-driven phonics interventions in seconds.")
with c2: 
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("📋 Download Tracker", generate_tracker_pdf(), "Skill_Tracker.pdf", "application/pdf", use_container_width=True, type="primary")
st.divider()

# --- 7. MAIN BUILDER CANVAS ---
col_plan, col_res = st.columns([1.5, 1])

with col_plan:
    st.header("📝 Worksheet Plan")
    if not st.session_state.build_queue: 
        st.markdown("""
        <div class='empty-state'>
            <h3 style='margin:0; color:#94a3b8;'>Your queue is empty</h3>
            <p style='font-size: 14px; margin-top:5px;'>Use the <b>Architect Tools</b> in the sidebar to add activities, or click <b>Auto-Build Full Packet</b> to generate one instantly.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i in range(0, len(st.session_state.build_queue), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < len(st.session_state.build_queue):
                    item = st.session_state.build_queue[idx]
                    with cols[j]:
                        display_name = "Story & Q's" if item['type'] == "Decodable Story" else item['type'].replace("Mystery Grid ", "")
                        st.markdown(f"""
                        <div class='builder-card'>
                            <small style='color:#94a3b8; font-weight:bold;'>Activity #{idx+1}</small>
                            <div style='font-weight:800; font-size:0.95rem; color:#1e293b; margin: 8px 0; word-break: keep-all; overflow-wrap: normal; line-height: 1.2;'>{display_name}</div>
                            <div style='font-size:0.75rem; color:#6366f1; background:#e0e7ff; padding: 4px 8px; border-radius: 12px; display:inline-block; word-break: keep-all;'>{', '.join(item['sounds'])}</div>
                        </div>""", unsafe_allow_html=True)
                        if st.button("✖️ Remove", key=f"del_{item['id']}", use_container_width=True):
                            st.session_state.build_queue.pop(idx)
                            st.rerun()

    if st.session_state.build_queue:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 GENERATE WORKSHEET", type="primary", use_container_width=True):
            with st.spinner("✨ AI is crafting rigorous content..."):
                prompt = f"""
                Create a {grade} worksheet ({r_level} level). 
                Plan: {st.session_state.build_queue}.
                
                STRICT QUANTITY & CONTENT RULES:
                1. RIGOR: For 3rd/4th+ grade, use advanced vocabulary. NO simple words like 'cat'. 
                2. STORY: MUST be 3+ paragraphs. MUST have exactly 3 questions.
                3. NONSENSE WORDS: MUST generate EXACTLY 21 pseudo-words.
                4. WORD SORT: MUST generate at least 15 words total across categories. Categories MUST be 1 or 2 words maximum (e.g. "-ed" or "Long A"). Do NOT write sentences for headers.
                5. SENTENCE MATCH: MUST generate EXACTLY 5 sentences. Halves MUST be under 6 words each.
                6. SOUND MAPPING: MUST generate EXACTLY 10 words.
                7. RIDDLES: MUST generate EXACTLY 8 distinct riddle cards.
                8. MYSTERY GRID: Choose EXACTLY 4 distinct colors. Generate EXACTLY 8 unique words for EACH color.
                
                JSON SAFETY: NO TRAILING COMMAS. Do NOT use double quotes (") inside strings. Use single quotes (') for dialogue.
                Output raw JSON ONLY:
                {{
                  "overview": "3 sentence intro.", "target_words": ["word1", "word2"],
                  "activities": [ {{
                    "type": "Exact Type", 
                    "content": {{
                      "title": "text", "paragraphs": ["Para 1 text"], "questions": [{{"q":"?","a":""}}],
                      "words": ["pseudo1"], "detective_task": ["1. Task"], "sort_cats": {{"Cat1":["w1"]}},
                      "match_l": ["Left 1"], "match_r": ["Right 1"], "map_words": ["w1"], "riddles": [{{"clue1":"c1","clue2":"c2","clue3":"c3","ans":"a"}}],
                      "mystery_grid": {{ "legend": {{"Red":"target 1", "Blue":"target 2"}}, "color_words": {{"Red":["w1","w2"]}} }}
                    }}
                  }} ]
                }}
                """
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "max_output_tokens": 8192})
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"): raw_text = raw_text[7:]
                    if raw_text.startswith("```"): raw_text = raw_text[3:]
                    if raw_text.endswith("```"): raw_text = raw_text[:-3]
                    
                    st.session_state.final_json = json.loads(raw_text.strip())
                    st.session_state.just_generated = True 
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ JSON Parsing Error: {str(e)}. Please click Generate again.")

# --- 8. BULLETPROOF PDF RENDERER ---
def clean_text(t): return str(t).replace("’","'").replace("“",'"').replace("”",'"').replace("**","")

def render_pdf(data, is_key=False):
    pdf = FPDF(unit='mm', format='A4')
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, margin=15)
    
    # COVER PAGE
    pdf.add_page()
    if is_key:
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(200, 0, 0)
        pdf.set_x(15); pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="R"); pdf.set_text_color(0,0,0)
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(15); pdf.cell(0, 10, "Name: ___________________________________   Date: ___________", ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 26); pdf.set_x(15); pdf.cell(0, 15, "WIN Time Phonics Packet", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14); pdf.set_x(15); pdf.cell(0, 8, "Learning Focus:", ln=True)
    pdf.set_font("Helvetica", "", 12); pdf.set_x(15); pdf.multi_cell(0, 6, clean_text(data.get("overview", "Practice targeted phonics skills.")))
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14); pdf.set_x(15); pdf.cell(0, 8, "Target Word Bank:", ln=True)
    pdf.set_font("Helvetica", "", 12)
    target_list = [clean_text(w) for w in data.get("target_words", [])]
    pdf.set_x(15)
    if target_list: pdf.multi_cell(0, 6, "   |   ".join(target_list))
    else: pdf.cell(0, 6, "Words provided in activities.", ln=True)
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 14); pdf.set_x(15); pdf.cell(0, 8, "Packet Checklist:", ln=True)
    pdf.set_font("Helvetica", "", 12)
    for i, act in enumerate(data.get("activities", [])):
        pdf.set_x(15); pdf.cell(0, 8, f"[   ]  {i+1}. {clean_text(act.get('type', 'Activity'))}", ln=True)
    
    # ACTIVITIES
    for act in data.get("activities", []):
        a_type, content = act['type'], act['content']
        pdf.add_page() 
        
        if a_type == "Mystery Grid (Color-by-Code)":
            pdf.rect(10, 10, 190, 277) 
            pdf.set_font("Helvetica", "B", 20); pdf.set_x(15); pdf.cell(0, 15, "Aztec Quilt Mystery Grid", ln=True, align="C")
            
            if not is_key:
                pdf.set_font("Helvetica", "B", 12); pdf.set_x(15); pdf.cell(0, 10, " Name: ___________________________________", ln=True, align="L")
            else:
                pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(200, 0, 0)
                pdf.set_x(15); pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="C"); pdf.set_text_color(0,0,0)

            grid_data = content.get('mystery_grid', {})
            legend = grid_data.get('legend', {})
            color_names = list(legend.keys())
            
            pdf.set_font("Helvetica", "B", 10)
            legend_str = " | ".join([f"{k}: {v}" for k, v in legend.items()])
            pdf.set_x(15); pdf.multi_cell(0, 8, "Legend: " + clean_text(legend_str), align="C")
            pdf.ln(5)
            
            patterns = [
                [[0,0,1,1,1,1,0,0],[0,1,2,2,2,2,1,0],[1,2,3,3,3,3,2,1],[1,2,3,0,0,3,2,1],[1,2,3,0,0,3,2,1],[1,2,3,3,3,3,2,1],[0,1,2,2,2,2,1,0],[0,0,1,1,1,1,0,0]],
                [[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0],[0,1,2,2,2,2,1,0],[1,0,2,3,3,2,0,1],[0,1,2,3,3,2,1,0],[1,0,2,2,2,2,0,1],[0,1,0,1,0,1,0,1],[1,0,1,0,1,0,1,0]]
            ]
            chosen_pattern = random.choice(patterns)
            w_dict = grid_data.get('color_words', {})
            
            size = 22; start_x = (210 - (8 * size)) / 2
            for r in range(8):
                pdf.set_x(start_x)
                for c in range(8):
                    c_idx = chosen_pattern[r][c] % max(1, len(color_names))
                    c_name = color_names[c_idx]
                    word_list = w_dict.get(c_name, ["?"])
                    word = clean_text(word_list[ (r*8+c) % max(1, len(word_list)) ])
                    
                    if is_key:
                        fill, text = get_color_rgb(c_name)
                        pdf.set_fill_color(*fill); pdf.set_text_color(*text)
                        pdf.set_font("Helvetica", "B", 7); pdf.cell(size, size, word, 1, 0, 'C', fill=True)
                        pdf.set_text_color(0,0,0)
                    else:
                        pdf.set_font("Helvetica", "", 8); pdf.cell(size, size, word, 1, 0, 'C')
                pdf.ln(size)
            continue

        if is_key:
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(200, 0, 0)
            pdf.set_x(15); pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="R"); pdf.set_text_color(0,0,0)
        else:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(15); pdf.cell(0, 8, "Name: ___________________________________", ln=True, align="R")
        
        pdf.ln(2); pdf.set_font("Helvetica", "B", 14); pdf.set_x(15); pdf.cell(0, 10, a_type, ln=True); pdf.ln(2)
        
        if a_type == "Decodable Story":
            pdf.set_font("Helvetica", "B", 12); pdf.set_x(15); pdf.cell(0, 10, clean_text(content.get('title','')), ln=True, align="C")
            pdf.set_font("Helvetica", "", 11)
            for p in content.get('paragraphs', []): 
                pdf.set_x(15); pdf.multi_cell(0, 6, clean_text(p)); pdf.ln(2)
            
            if pdf.get_y() > 220: pdf.add_page()
            
            pdf.ln(5); pdf.set_font("Helvetica", "B", 11); pdf.set_x(15); pdf.cell(0, 8, "Evidence Check:", ln=True)
            pdf.set_font("Helvetica", "", 11)
            for q in content.get('questions', []):
                q_str = clean_text(q.get('q', ''))
                a_str = clean_text(q.get('a', ''))
                pdf.set_x(15); pdf.multi_cell(0, 7, f"Q: {q_str}")
                if is_key: 
                    pdf.set_text_color(200,0,0); pdf.set_x(15); pdf.multi_cell(0, 7, f"A: {a_str}"); pdf.set_text_color(0,0,0); pdf.ln(2)
                else: 
                    pdf.ln(8)

        elif a_type == "Nonsense Word Fluency":
            words = content.get('words', [])[:21]
            pdf.set_font("Helvetica", "B", 24)
            for i, word in enumerate(words):
                if i % 3 == 0: pdf.set_x(15)
                pdf.cell(60, 20, clean_text(word), 1, 1 if (i + 1) % 3 == 0 else 0, 'C')
            tasks = content.get('detective_task', [])
            if tasks:
                pdf.ln(10); pdf.set_font("Helvetica", "B", 14); pdf.set_x(15); pdf.cell(0, 8, "DETECTIVE TASK:", ln=True)
                pdf.set_font("Helvetica", "", 12)
                for task in tasks:
                    pdf.set_x(15); pdf.multi_cell(0, 6, clean_text(task))

        elif a_type == "Word Bank Sort":
            cats = list(content.get('sort_cats', {}).keys())
            if cats:
                all_words = []
                for cat_words in content['sort_cats'].values(): all_words.extend([clean_text(w) for w in cat_words])
                random.shuffle(all_words)
                pdf.set_font("Helvetica", "", 13)
                pdf.set_x(15); pdf.multi_cell(0, 8, "Word Bank:  " + "   |   ".join(all_words)); pdf.ln(5)
                w = 180 / len(cats)
                
                pdf.set_font("Helvetica", "B", 9) 
                pdf.set_x(15)
                for c in cats: pdf.cell(w, 10, clean_text(c)[:20], 1, 0, 'C')
                pdf.ln(); pdf.set_font("Helvetica", "", 12)
                
                if not is_key:
                    for _ in range(6):
                        pdf.set_x(15)
                        for _ in cats: pdf.cell(w, 12, "", 1, 0)
                        pdf.ln()
                else:
                    max_r = max([len(content['sort_cats'][c]) for c in cats])
                    pdf.set_text_color(200, 0, 0)
                    for r in range(max_r):
                        pdf.set_x(15)
                        for c in cats:
                            lst = content['sort_cats'][c]
                            pdf.cell(w, 10, clean_text(lst[r]) if r < len(lst) else "", 1, 0, 'C')
                        pdf.ln()
                    pdf.set_text_color(0, 0, 0)

        elif a_type == "Sentence Match":
            l, r = content.get('match_l', []), content.get('match_r', [])
            dr = r if is_key else random.sample(r, len(r))
            for i in range(len(l)):
                pdf.set_x(15)
                pdf.set_font("Helvetica", "", 10) 
                pdf.cell(85, 10, clean_text(l[i])[:50], 0, 0)
                pdf.set_font("Courier", "", 10); pdf.cell(10, 10, ".......", 0, 0, 'C')
                if is_key: pdf.set_text_color(200, 0, 0)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(85, 10, clean_text(dr[i])[:50] if i < len(dr) else "", 0, 1, 'R')
                pdf.set_text_color(0, 0, 0)

        elif a_type == "Sound Mapping":
            for word in content.get('map_words', []):
                pdf.set_x(15)
                pdf.set_font("Helvetica", "B", 14); pdf.cell(50, 12, f"{clean_text(word)} -> ", 0, 0, 'R')
                if is_key:
                    pdf.set_text_color(200, 0, 0); pdf.cell(60, 12, "(Break word into phonemes)", 0, 1); pdf.set_text_color(0, 0, 0)
                else:
                    pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 1)
                pdf.ln(2)

        elif a_type == "Detective Riddle Cards":
            cards = content.get('riddles', [])[:8]
            xs, ys = 15, 45 
            c_w, c_h = 85, 45 
            for i, r in enumerate(cards):
                col = i % 2
                row = i // 2
                x = xs + (col * 95)
                y = ys + (row * 50) 
                pdf.rect(x, y, c_w, c_h)
                pdf.set_xy(x+2, y+2); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 5, f"Riddle #{i+1}")
                pdf.set_xy(x+2, y+8); pdf.set_font("Helvetica", "", 9)
                
                clue_str = f"Clue 1: {clean_text(r.get('clue1',''))}\nClue 2: {clean_text(r.get('clue2',''))}\nClue 3: {clean_text(r.get('clue3',''))}"
                pdf.multi_cell(c_w-4, 4.5, clue_str)
                
                if is_key:
                    pdf.set_xy(x, y + c_h - 7); pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(200,0,0)
                    pdf.cell(c_w, 6, f"Ans: {clean_text(r.get('ans',''))}", 0, 0, 'C'); pdf.set_text_color(0,0,0)

    return bytes(pdf.output())

# --- 9. DOWNLOADS SECTION ---
with col_res:
    st.header("📥 Downloads")
    
    if not st.session_state.final_json:
        # THE EMPTY STATE
        st.markdown("""
        <div class='empty-state'>
            <h3 style='margin:0; color:#94a3b8; font-size:1.1rem;'>No packets yet</h3>
            <p style='font-size: 13px; margin-top:5px;'>Your finished PDFs will appear here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # THE SUCCESS STATE
        st.markdown("""
        <div class='success-card'>
            <h3 style='margin:0; color:#166534; font-size:1.3rem;'>🎉 Results Ready!</h3>
            <p style='font-size: 14px; color:#15803d; margin-top:5px; margin-bottom:0;'>Your WIN Time packet was generated successfully. Download your files below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        spdf = render_pdf(st.session_state.final_json, False)
        tpdf = render_pdf(st.session_state.final_json, True)
        
        st.download_button("📘 Download Student Packet", spdf, "Student_Worksheet.pdf", use_container_width=True, type="primary")
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) # Tiny spacer
        st.download_button("🗝️ Download Teacher Key", tpdf, "Teacher_Key.pdf", use_container_width=True, type="primary")
        
        # CELEBRATION SCRIPT
        if st.session_state.just_generated:
            anim_type = random.choice(["balloons", "snow", "school", "stars"])
            
            if anim_type == "balloons":
                st.balloons()
                js_injection = ""
            elif anim_type == "snow":
                st.snow()
                js_injection = ""
            elif anim_type == "school":
                js_injection = "createEmojiShower(['📚', '🍎', '✏️', '🎓', '🚌']);"
            else:
                js_injection = "createEmojiShower(['⭐', '🌟', '✨', '🚀', '💡']);"
            
            components.html(f"""
                <script>
                    window.parent.scrollTo({{top: window.parent.document.body.scrollHeight, behavior: 'smooth'}});
                    
                    function createEmojiShower(emojis) {{
                        const container = window.parent.document.createElement('div');
                        container.style.position = 'fixed';
                        container.style.top = '0';
                        container.style.left = '0';
                        container.style.width = '100vw';
                        container.style.height = '100vh';
                        container.style.pointerEvents = 'none';
                        container.style.zIndex = '99999';
                        window.parent.document.body.appendChild(container);

                        for (let i = 0; i < 60; i++) {{
                            const el = window.parent.document.createElement('div');
                            el.innerText = emojis[Math.floor(Math.random() * emojis.length)];
                            el.style.position = 'absolute';
                            el.style.left = Math.random() * 100 + 'vw';
                            el.style.top = '-50px';
                            el.style.fontSize = (Math.random() * 24 + 16) + 'px';
                            el.style.transition = 'transform ' + (Math.random() * 2 + 2) + 's linear, top ' + (Math.random() * 2 + 2) + 's linear';
                            container.appendChild(el);

                            setTimeout(() => {{
                                el.style.top = '120vh';
                                el.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';
                            }}, 50);
                        }}
                        setTimeout(() => container.remove(), 4500);
                    }}
                    {js_injection}
                </script>
            """, height=0)
            st.session_state.just_generated = False
