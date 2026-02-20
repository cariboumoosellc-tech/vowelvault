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

# ==========================================
# 🎨 BRANDING SECTION
# ==========================================
APP_NAME = "WIN Time Phonics Builder"
APP_EMOJI = "🎯" 
SIDEBAR_TITLE = "🏫 WIN Time Architect"
FOOTER_TEXT = "🚀 WIN Time Phonics Builder v18.0"

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon=APP_EMOJI)
# ==========================================

# --- 2. PHONICS DATABASE & DESCRIPTIONS ---
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
    "Nonsense Word Fluency": "🧪 21 pseudo-words with a custom Detective Task at the bottom.",
    "Word Bank Sort": "📊 Word Sort: A Word Bank and columns to categorize words.",
    "Sentence Match": "🔗 Sentence Match: 5 sentence halves to connect.",
    "Sound Mapping": "🟦 Mapping: Segment words into phoneme boxes.",
    "Detective Riddle Cards": "🔍 8 cards per page with 3 logic clues each.",
    "Mystery Grid (Color-by-Code)": "🎨 A FULL-PAGE 8x8 Aztec/Quilt geometric coloring grid."
}

# --- 3. CUSTOM UI STYLING & PDF HELPERS ---
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
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        border: none !important;
        font-weight: bold !important;
        transition: transform 0.2s;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

def generate_tracker_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "Skill Mastery Tracker", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Student Name: _________________________________", ln=True, align="L")
    pdf.ln(3)
    pdf.set_fill_color(220, 230, 245) 
    pdf.cell(100, 10, " Phonics Skill", 1, 0, 'L', fill=True)
    pdf.cell(30, 10, "Practice", 1, 0, 'C', fill=True)
    pdf.cell(30, 10, "Pass-Off", 1, 0, 'C', fill=True)
    pdf.cell(30, 10, "Initials", 1, 1, 'C', fill=True)
    
    skills = [
        ("Letter Names & Sounds", False), ("Short Vowels (CVC)", False),
        ("Consonant Blends (2-letter)", False), ("Three-Letter Blends", False),
        ("Digraphs (sh, ch, th, wh, ck, ng)", False), ("Complex Consonants", False),
        ("Final Blends", False), ("Silent e (CVCe)", False),
        ("Vowel Teams (ai, ea, oa, ee)", False), ("Unpredictable Vowel Teams", False),
        ("R-Controlled Vowels", False), ("Diphthongs (oi, oy, ou, ow)", False),
        ("MULTISYLLABLE WORDS", True), ("   - closed/closed", False),
        ("   - silent e", False), ("   - open", False), ("   - vowel team", False),
        ("   - consonant le", False), ("   - vowel r", False),
        ("INFLECTIONAL ENDINGS", True), ("   - ed", False), ("   - ing", False),
        ("   - s", False), ("   - es", False), ("   - er", False), ("   - est", False),
        ("High-Frequency Words", False)
    ]
    
    row_count = 0
    for skill, is_header in skills:
        if is_header:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(235, 235, 235) 
            pdf.cell(190, 8, f" {skill}", 1, 1, 'L', fill=True)
            row_count = 0 
        else:
            pdf.set_font("Helvetica", "", 10)
            fill = (row_count % 2 == 0)
            if fill: pdf.set_fill_color(250, 250, 250)
            else: pdf.set_fill_color(255, 255, 255)
            pdf.cell(100, 8, f" {skill}", 1, 0, 'L', fill=fill)
            pdf.cell(30, 8, "", 1, 0, 'C', fill=fill)
            pdf.cell(30, 8, "", 1, 0, 'C', fill=fill)
            pdf.cell(30, 8, "", 1, 1, 'C', fill=fill)
            row_count += 1
    return bytes(pdf.output())

def get_color_rgb(color_name):
    c = str(color_name).lower().strip()
    if "red" in c: return (255, 153, 153), (0, 0, 0)
    if "blue" in c: return (153, 204, 255), (0, 0, 0)
    if "yellow" in c: return (255, 255, 153), (0, 0, 0)
    if "green" in c: return (153, 255, 153), (0, 0, 0)
    if "orange" in c: return (255, 204, 153), (0, 0, 0)
    if "purple" in c: return (204, 153, 255), (0, 0, 0)
    if "pink" in c: return (255, 153, 204), (0, 0, 0)
    if "brown" in c: return (204, 178, 153), (0, 0, 0)
    if "black" in c: return (80, 80, 80), (255, 255, 255) 
    if "gray" in c or "grey" in c: return (200, 200, 200), (0, 0, 0)
    return (255, 255, 255), (0, 0, 0) 

# --- 4. THE ARCHITECT SIDEBAR ---
with st.sidebar:
    st.title(SIDEBAR_TITLE)
    grade = st.selectbox("Grade (Interest)", ["1st", "2nd", "3rd", "4th+"])
    r_level = st.select_slider("Difficulty", options=["Beginning", "Intermediate", "Advanced"])
    sel_cat = st.selectbox("Phonics Category", list(PHONICS_MENU.keys()))
    sel_targets = st.multiselect("Specific Targets", PHONICS_MENU[sel_cat], default=[PHONICS_MENU[sel_cat][0]])
    st.divider()
    add_type = st.selectbox("Activity", list(ACTIVITY_INFO.keys()))
    add_nonsense = st.checkbox("Include Nonsense Words", value=(add_type in ["Nonsense Word Fluency", "Mystery Grid (Color-by-Code)"]))
    
    if st.button("➕ Add to Plan", use_container_width=True):
        st.session_state.build_queue.append({
            "type": add_type, "nonsense": add_nonsense, "id": str(uuid.uuid4()),
            "cat": sel_cat, "sounds": sel_targets
        })

    if st.button("🎲 Choose For Me", use_container_width=True):
        st.session_state.build_queue = []
        grade_logic = {
            "1st": ["CVC (Short Vowels)", "Consonant Digraphs", "Consonant Blends"],
            "2nd": ["Magic E (CVCe)", "Vowel r", "Predictable Vowel Teams"],
            "3rd": ["Variant Vowel Teams", "Multisyllable", "Endings"],
            "4th+": ["Multisyllable", "Endings", "Mixed Review (All Types)"]
        }
        chosen_acts = list(ACTIVITY_INFO.keys())
        random.shuffle(chosen_acts)
        chosen_acts = chosen_acts[:5] 
        
        for act in chosen_acts:
            auto_cat = random.choice(grade_logic[grade])
            auto_target = [random.choice(PHONICS_MENU[auto_cat])]
            is_nonsense = (act in ["Nonsense Word Fluency", "Mystery Grid (Color-by-Code)"] and random.choice([True, False]))
            st.session_state.build_queue.append({
                "type": act, "nonsense": is_nonsense, 
                "id": str(uuid.uuid4()), "cat": auto_cat, "sounds": auto_target
            })
        st.rerun()

    if st.button("🗑️ Clear Plan", use_container_width=True):
        st.session_state.build_queue = []
        st.session_state.final_json = None
        st.rerun()
    st.divider()
    st.caption(FOOTER_TEXT)

# --- 4.5 MAIN APP HEADER & DOWNLOAD TRACKER ---
h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.title("Welcome to WIN Time Phonics! 🏫")
    st.markdown("Build targeted, data-driven phonics interventions in seconds.")
with h_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("📋 Download Free Skill Tracker", generate_tracker_pdf(), "WIN_Time_Skill_Tracker.pdf", "application/pdf", use_container_width=True, type="primary")
st.divider()

# --- 5. MAIN BUILDER ---
col_plan, col_res = st.columns([1.5, 1])

with col_plan:
    st.header("📝 Worksheet Plan")
    if not st.session_state.build_queue:
        st.info("Queue is empty. Build a plan manually or click 'Choose For Me'!")
    else:
        for i in range(0, len(st.session_state.build_queue), 4):
            cols = st.columns(4)
            for j in range(4):
                idx = i + j
                if idx < len(st.session_state.build_queue):
                    item = st.session_state.build_queue[idx]
                    with cols[j]:
                        display_name = "Story & Q's" if item['type'] == "Decodable Story" else item['type'].replace("Mystery Grid ", "")
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
            with st.spinner("AI is crafting rigorous content... this may take up to 30 seconds..."):
                seed = random.randint(1, 1000000)
                all_targets = set()
                for item in st.session_state.build_queue:
                    all_targets.update(item['sounds'])
                targets_text = ", ".join(list(all_targets))
                
                prompt = f"""
                You are an OG Reading Specialist. Create a {grade} worksheet ({r_level} level) targeting {targets_text}.
                Plan: {st.session_state.build_queue}.
                
                STRICT RULES:
                1. RIGOR ENGINE: If grade is 3rd/4th+ or level is Intermediate/Advanced, you MUST use rigorous, multi-syllabic academic vocabulary. DO NOT use simple words like 'cat' or 'brave'. 
                2. STORIES: 3+ paragraphs. Keep it concise so it fits on one page. Comprehension questions MUST include 'q' and 'a'.
                3. JSON SAFETY: Do NOT use double quotes (") inside your stories or strings. Use single quotes (') for dialogue. NO MARKDOWN ASTERISKS.
                4. Nonsense Fluency must be exactly 21 pseudo-words with a 2-step "detective_task" array. ZERO PROFANITY.
                5. Provide exactly 8 distinct riddles. Sort categories MUST be EXTREMELY short. Match halves must fit side-by-side.
                6. MYSTERY GRID (Color-by-Code): Choose EXACTLY 3 or 4 distinct standard colors. Map each color to a specific phonics rule/target. Generate an array of EXACTLY 8 unique words for EACH color.
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
                         "questions": [ {{"q": "q?", "a": "a"}} ],
                         "words": ["pseudo1", "etc"],
                         "detective_task": ["1. Task one"],
                         "sort_cats": {{"Cat1": ["w1"], "Cat2": ["w2"]}},
                         "match_l": ["Left 1"], "match_r": ["Right 1"],
                         "map_words": ["w1", "w2"],
                         "riddles": [ {{"clue1": "c1", "clue2": "c2", "clue3": "c3", "ans": "a"}} ],
                         "mystery_grid": {{
                            "legend": {{"Red": "target 1", "Blue": "target 2", "Green": "target 3"}},
                            "color_words": {{"Red": ["w1","w2","w3","w4","w5","w6","w7","w8"], "Blue": ["w1","w2","w3","w4","w5","w6","w7","w8"], "Green": ["w1","w2","w3","w4","w5","w6","w7","w8"]}}
                         }}
                      }} 
                    }} 
                  ] 
                }}
                Seed: {seed}
                """
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    # FIX: Increased output tokens so large packets don't get cut off!
                    response = model.generate_content(
                        prompt, 
                        generation_config={
                            "response_mime_type": "application/json",
                            "max_output_tokens": 8192 
                        }
                    )
                    st.session_state.final_json = json.loads(response.text)
                    st.session_state.scroll_up = True
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("⚠️ The AI wrote so much that it lost its place! Please click Generate again.")
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.error("🚦 The AI is moving too fast. Please wait a few seconds and click Generate again.")
                    else:
                        st.error(f"⚠️ An error occurred during generation: {str(e)}")

# --- 6. BULLETPROOF PDF ENGINE WITH SANITIZER ---
def clean_text(text):
    if not isinstance(text, str): return str(text)
    replacements = {"’": "'", "‘": "'", "“": "'", "”": "'", "–": "-", "—": "--", "…": "...", "**": "", "*": ""}
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
        a_type, content = act['type'], act['content']
        
        # Mystery Grid gets a completely isolated, bordered page
        if a_type == "Mystery Grid (Color-by-Code)":
            pdf.add_page()
            # Thick outer border
            pdf.set_line_width(0.8)
            pdf.rect(10, 10, 190, 277)
            pdf.set_line_width(0.2) 
            
            pdf.set_font("Helvetica", "B", 24)
            pdf.cell(0, 20, "Color-by-Code: Aztec Quilt", ln=True, align="C")
            
            if not is_key:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 10, " Name: ___________________________________", ln=True, align="L")
                pdf.ln(5)
            else:
                pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="C"); pdf.set_text_color(0,0,0)
                pdf.ln(5)

            grid_data = content.get('mystery_grid', {})
            legend = grid_data.get('legend', {})
            color_names = list(legend.keys())
            
            # Print Legend
            pdf.set_font("Helvetica", "B", 11)
            legend_str = "    |    ".join([f"{k}: {v}" for k, v in legend.items()])
            pdf.multi_cell(0, 8, "LEGEND:  " + clean_text(legend_str), align="C")
            pdf.ln(8)
            
            # Hardcoded 8x8 Aztec and Quilt Star Patterns
            patterns = [
                # Aztec Diamond Star (Colors 0, 1, 2)
                [
                    [0, 0, 0, 1, 1, 0, 0, 0],
                    [0, 0, 1, 2, 2, 1, 0, 0],
                    [0, 1, 1, 1, 1, 1, 1, 0],
                    [1, 2, 1, 0, 0, 1, 2, 1],
                    [1, 2, 1, 0, 0, 1, 2, 1],
                    [0, 1, 1, 1, 1, 1, 1, 0],
                    [0, 0, 1, 2, 2, 1, 0, 0],
                    [0, 0, 0, 1, 1, 0, 0, 0]
                ],
                # Woven Quilt Star (Colors 0, 1, 2)
                [
                    [0, 0, 1, 0, 0, 1, 0, 0],
                    [0, 1, 1, 1, 1, 1, 1, 0],
                    [1, 1, 2, 1, 1, 2, 1, 1],
                    [0, 1, 1, 2, 2, 1, 1, 0],
                    [0, 1, 1, 2, 2, 1, 1, 0],
                    [1, 1, 2, 1, 1, 2, 1, 1],
                    [0, 1, 1, 1, 1, 1, 1, 0],
                    [0, 0, 1, 0, 0, 1, 0, 0]
                ],
                # Aztec Step Border (Colors 0, 1, 2, 3)
                [
                    [1, 0, 0, 3, 3, 0, 0, 1],
                    [1, 1, 0, 0, 0, 0, 1, 1],
                    [0, 1, 1, 2, 2, 1, 1, 0],
                    [3, 0, 1, 2, 2, 1, 0, 3],
                    [3, 0, 1, 2, 2, 1, 0, 3],
                    [0, 1, 1, 2, 2, 1, 1, 0],
                    [1, 1, 0, 0, 0, 0, 1, 1],
                    [1, 0, 0, 3, 3, 0, 0, 1]
                ]
            ]
            
            chosen_pattern = random.choice(patterns)
            w_dict = grid_data.get('color_words', {})
            word_trackers = {color: 0 for color in color_names}
            
            # Grid Math: 8x8 Grid, cells are 22mm each
            cell_size = 22
            start_x = (210 - (8 * cell_size)) / 2 
            
            for r in range(8):
                pdf.set_x(start_x)
                for c in range(8):
                    # Ensure color index matches the number of colors generated by the AI
                    color_idx = chosen_pattern[r][c] % max(1, len(color_names))
                    current_color = color_names[color_idx]
                    
                    # Pull next word
                    c_list = w_dict.get(current_color, ["word"])
                    word = clean_text(c_list[word_trackers[current_color] % max(1, len(c_list))])
                    word_trackers[current_color] += 1
                        
                    if is_key:
                        fill_rgb, text_rgb = get_color_rgb(current_color)
                        pdf.set_fill_color(*fill_rgb)
                        pdf.set_text_color(*text_rgb)
                        pdf.set_font("Helvetica", "B", 8) 
                        pdf.cell(cell_size, cell_size, word, 1, 0, 'C', fill=True)
                        pdf.set_text_color(0, 0, 0)
                    else:
                        pdf.set_font("Helvetica", "B", 9)
                        pdf.cell(cell_size, cell_size, word, 1, 0, 'C')
                pdf.ln(cell_size)
            first_page = False 
            continue 

        # Formatting for all other standard activities
        if not first_page: pdf.add_page()
        if is_key and not first_page:
            pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 10, "TEACHER ANSWER KEY", ln=True, align="R"); pdf.set_text_color(0,0,0)
        elif not is_key and not first_page:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, "Name: ___________________________________", ln=True, align="R")
            pdf.ln(2)
        
        first_page = False

        if a_type == "Decodable Story":
            title_text = clean_text(content.get('title', 'Decodable Story'))
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, title_text, ln=True, align="C")
            pdf.set_font("Helvetica", "", 12) 
            for para in content.get('paragraphs', []):
                pdf.set_x(15)
                pdf.multi_cell(0, 6, clean_text(para))
                pdf.ln(3)
            
            pdf.ln(4); pdf.set_font("Helvetica", "B", 14); pdf.cell(0, 8, "Evidence Check", ln=True)
            pdf.set_font("Helvetica", "", 12)
            for q_data in content.get('questions', []):
                q_text = clean_text(q_data.get('q', str(q_data)) if isinstance(q_data, dict) else str(q_data))
                a_text = clean_text(q_data.get('a', 'Refer to text.') if isinstance(q_data, dict) else 'Refer to text.')
                pdf.set_x(15); pdf.set_font("Helvetica", "B", 12); pdf.multi_cell(0, 6, q_text)
                if is_key:
                    pdf.set_x(15); pdf.set_font("Helvetica", "I", 11); pdf.set_text_color(200, 0, 0)
                    pdf.multi_cell(0, 6, f"Answer: {a_text}"); pdf.set_text_color(0, 0, 0); pdf.ln(2)
                else: pdf.ln(6) 

        elif a_type == "Nonsense Word Fluency":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Decoding Drills (Nonsense Words)", ln=True); pdf.ln(5)
            words = content.get('words', [])[:21]
            for i, word in enumerate(words):
                pdf.set_font("Helvetica", "B", 24)
                pdf.cell(60, 20, clean_text(word), 1, (i + 1) % 3 == 0, 'C')
            tasks = content.get('detective_task', [])
            if tasks:
                pdf.ln(10); pdf.set_x(15); pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 8, "DETECTIVE TASK:", ln=True); pdf.set_font("Helvetica", "", 12)
                for task in tasks:
                    pdf.set_x(15); pdf.multi_cell(0, 6, clean_text(task))

        elif a_type == "Word Bank Sort":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Activity: Word Sort", ln=True); pdf.ln(2)
            cats = list(content.get('sort_cats', {}).keys())
            if cats:
                all_words = []
                for cat_words in content['sort_cats'].values(): all_words.extend([clean_text(w) for w in cat_words])
                random.shuffle(all_words)
                pdf.set_font("Helvetica", "", 13)
                pdf.multi_cell(0, 8, "Word Bank:  " + "   |   ".join(all_words)); pdf.ln(5)
                w = 180 / len(cats)
                pdf.set_font("Helvetica", "B", 10) 
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
                pdf.set_x(15); pdf.set_font("Helvetica", "", 11) 
                pdf.cell(85, 10, clean_text(l[i]), 0, 0)
                pdf.set_font("Courier", "", 10); pdf.cell(10, 10, ".......", 0, 0, 'C')
                if is_key: pdf.set_text_color(200, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                pdf.cell(85, 10, clean_text(dr[i]) if i < len(dr) else "", 0, 1, 'R')
                pdf.set_text_color(0, 0, 0)

        elif a_type == "Sound Mapping":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 10, "Sound Mapping", ln=True); pdf.ln(5)
            for word in content.get('map_words', []):
                pdf.set_font("Helvetica", "B", 14); pdf.cell(50, 12, f"{clean_text(word)} -> ", 0, 0, 'R')
                if is_key:
                    pdf.set_text_color(200, 0, 0); pdf.cell(60, 12, "(Break word into phonemes)", 0, 1); pdf.set_text_color(0, 0, 0)
                else:
                    pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 0); pdf.cell(20, 12, "", 1, 1)
                pdf.ln(2)

        elif a_type == "Detective Riddle Cards":
            pdf.set_font("Helvetica", "B", 18); pdf.cell(0, 12, "Detective Riddle Cards", ln=True, align="C")
            cards = content.get('riddles', [])[:8]
            xs, ys = 10, 30; c_w, c_h = 90, 42 
            for i, r in enumerate(cards):
                col, row = i % 2, i // 2
                x, y = xs + (col * 95), ys + (row * 45) 
                pdf.rect(x, y, c_w, c_h)
                pdf.set_xy(x+2, y+2); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 5, f"Riddle #{i+1}")
                pdf.set_xy(x+2, y+8); pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(c_w-4, 4.5, f"Clue 1: {clean_text(r.get('clue1',''))}\nClue 2: {clean_text(r.get('clue2',''))}\nClue 3: {clean_text(r.get('clue3',''))}")
                if is_key:
                    pdf.set_xy(x, y + c_h - 7); pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(200,0,0)
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
            components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
            st.session_state.scroll_up = False

st.markdown("<div class='donation-footer'><h3>☕ Support WIN Time Phonics</h3><p>Keep this free for teachers!</p><a href='https://venmo.com'>Venmo</a> | <a href='https://paypal.me'>PayPal</a></div>", unsafe_allow_html=True)
