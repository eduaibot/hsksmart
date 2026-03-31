import streamlit as st
import random
import json
import os
from datetime import datetime

DB_FILE = "notebooks_v4.json"

# --- 5 THEME GRADIENT MẶC ĐỊNH OCEAN BLUE ---
THEMES = {
    "Ocean Blue (G)": {"bg": "#f0f9ff", "main": "#0ea5e9", "text": "#0c4a6e", "border": "#bae6fd", "grad": "linear-gradient(135deg, #e0f2fe 0%, #7dd3fc 100%)"},
    "Sunset Glow (G)": {"bg": "#fff7ed", "main": "#f97316", "text": "#7c2d12", "border": "#fed7aa", "grad": "linear-gradient(135deg, #ffedd5 0%, #fdba74 100%)"},
    "Deep Forest (G)": {"bg": "#f0fdf4", "main": "#22c55e", "text": "#14532d", "border": "#bbf7d0", "grad": "linear-gradient(135deg, #dcfce7 0%, #86efac 100%)"},
    "Royal Purple (G)": {"bg": "#faf5ff", "main": "#a855f7", "text": "#581c87", "border": "#e9d5ff", "grad": "linear-gradient(135deg, #f3e8ff 0%, #d8b4fe 100%)"},
    "Midnight (G)": {"bg": "#f8fafc", "main": "#334155", "text": "#0f172a", "border": "#e2e8f0", "grad": "linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)"}
}

if 'theme_name' not in st.session_state: st.session_state.theme_name = "Ocean Blue (G)"
if 'editing_nb' not in st.session_state: st.session_state.editing_nb = None

t = THEMES[st.session_state.theme_name]
st.set_page_config(page_title="HSK Smart Drill", layout="centered")

# --- CSS CUSTOM ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; font-family: 'Inter', sans-serif; }}
    div[data-testid="stExpander"], .stAlert, div[data-testid="stForm"], .result-card, .edit-box {{
        background: white !important; border: 1px solid {t['border']} !important;
        border-radius: 15px !important; padding: 15px !important; margin-bottom: 10px;
    }}
    .question-container {{ 
        background: {t['grad']} !important; border-left: 8px solid {t['main']} !important; 
        text-align: center; border-radius: 20px; padding: 40px; margin-bottom: 20px;
    }}
    .stButton > button {{ background-color: {t['main']} !important; color: white !important; border-radius: 10px !important; }}
    .stTextInput input {{ text-align: center; border-radius: 10px !important; }}
    .stTextArea textarea {{ text-align: left !important; border-radius: 10px !important; font-family: monospace; }}
    </small></style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def parse_data(raw_text):
    words = []
    for line in raw_text.strip().split('\n'):
        if not line.strip(): continue
        # Tách dựa trên dấu gạch ngang " - "
        parts = [p.strip() for p in line.split('-')]
        # Nếu dòng bắt đầu bằng số thứ tự (như ví dụ của Hùng), ta bỏ qua phần tử đầu tiên
        if parts[0].isdigit(): parts = parts[1:]
        
        if len(parts) >= 3:
            words.append({
                'hz': parts[0], 
                'py': parts[1], 
                'vn': " - ".join(parts[2:]), # Hỗ trợ nghĩa có chứa dấu gạch ngang
                'score': 0, 
                'attempts': 0
            })
    return words

def format_to_text(words_list):
    # Trả về định dạng: STT - Hán - Pinyin - Nghĩa
    return "\n".join([f"{i+1} - {w['hz']} - {w['py']} - {w['vn']}" for i, w in enumerate(words_list)])

def create_smart_quiz(selected_words):
    quiz = []
    for w in selected_words:
        sc = w.get('score', 0)
        att = w.get('attempts', 0)
        # Logic Hard-words: Sai nhiều/Chưa học hiện nhiều lần
        repeat = 3 if sc < 0 else (2 if att == 0 else 1)
        forms = [
            {'q': w['vn'].capitalize(), 'a': w['hz'], 'f': w},
            {'q': w['hz'], 'a': w['vn'].capitalize(), 'f': w},
        ]
        quiz.extend(random.sample(forms, min(repeat, len(forms))))
    random.shuffle(quiz)
    return quiz

if 'notebooks' not in st.session_state: st.session_state.notebooks = load_data()
if 'mode' not in st.session_state: st.session_state.mode = "manage"

# --- UI QUẢN LÝ ---
if st.session_state.mode == "manage":
    st.title("🚀 HSK Smart Drill")
    
    with st.expander("🎨 Cài đặt & Thêm mới"):
        c_th, c_add = st.columns(2)
        with c_th:
            theme_choice = st.selectbox("Chọn Theme:", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_name))
            if theme_choice != st.session_state.theme_name:
                st.session_state.theme_name = theme_choice; st.rerun()
        with c_add:
            n_name = st.text_input("Tên sổ tay:")
            n_data = st.text_area("Dữ liệu (STT - Hán - Pinyin - Nghĩa):", height=68)
            if st.button("Lưu Sổ Tay"):
                if n_name and n_data:
                    st.session_state.notebooks[n_name] = {'words': parse_data(n_data), 'fav': False, 'updated_at': datetime.now().isoformat()}
                    save_data(st.session_state.notebooks); st.rerun()

    if st.session_state.notebooks:
        # Sắp xếp: Yêu thích lên đầu -> Thời gian
        sorted_nbs = sorted(
            st.session_state.notebooks.items(), 
            key=lambda x: (
                bool(x[1].get('fav', False)), 
                str(x[1].get('updated_at') or '')
            ), 
            reverse=True
        )
        
        for idx, (name, info) in enumerate(sorted_nbs, 1):
            words = info['words']
            total_att = sum(w.get('attempts', 0) for w in words)
            correct_sc = sum(max(0, w.get('score', 0)) for w in words)
            win_rate = (correct_sc / total_att * 100) if total_att > 0 else 0
            
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2.2, 0.4, 0.4, 0.4, 0.4])
                
                # Hiển thị STT, Tên và số lượng từ
                is_fav = "⭐ " if info.get('fav') else ""
                is_good = " 🔥 Tốt" if win_rate > 65 else ""
                c1.markdown(f"**{idx}. {is_fav}{name}** ({len(words)} từ) <small style='color:orange'>{is_good}</small>", unsafe_allow_html=True)
                
                if c2.button("📖", key=f"st_{name}", help="Học"):
                    st.session_state.update({"qs": create_smart_quiz(words), "curr_nb": name, "mode": "study", "idx": 0, "answered": False})
                    st.rerun()
                if c3.button("⚙️", key=f"ed_{name}", help="Sửa"):
                    st.session_state.editing_nb = name; st.rerun()
                if c4.button("🌟" if info.get('fav') else "⭐", key=f"fv_{name}"):
                    st.session_state.notebooks[name]['fav'] = not info.get('fav')
                    save_data(st.session_state.notebooks); st.rerun()
                if c5.button("🗑️", key=f"dl_{name}"):
                    del st.session_state.notebooks[name]; save_data(st.session_state.notebooks); st.rerun()

                # BOX CHỈNH SỬA TÊN & ND (Giữ đúng định dạng Hùng yêu cầu)
                if st.session_state.editing_nb == name:
                    with st.form(f"f_edit_{name}"):
                        new_n = st.text_input("Sửa tên thư mục:", value=name)
                        new_d = st.text_area("Sửa nội dung (STT - Hán - Pinyin - Nghĩa):", value=format_to_text(words), height=250)
                        ec1, ec2 = st.columns(2)
                        if ec1.form_submit_button("Lưu thay đổi ✅"):
                            if new_n != name: st.session_state.notebooks.pop(name)
                            st.session_state.notebooks[new_n] = {'words': parse_data(new_d), 'fav': info.get('fav'), 'updated_at': datetime.now().isoformat()}
                            save_data(st.session_state.notebooks); st.session_state.editing_nb = None; st.rerun()
                        if ec2.form_submit_button("Hủy ❌"):
                            st.session_state.editing_nb = None; st.rerun()

                # CHIA SET & TRẠNG THÁI
                with st.expander("Phân tích chi tiết & Chia Set"):
                    chunk = st.select_slider("Số từ mỗi Set:", options=[5, 10, 20], key=f"sl_{name}")
                    for i in range(0, len(words), chunk):
                        subset = words[i : i + chunk]
                        states = []
                        for w in subset:
                            # Logic: ⚪ Chưa học | 🔴 Cần xem kĩ (Sai nhiều/Chưa vững) | 🟢 Đã ổn
                            if w.get('attempts', 0) == 0: states.append("⚪")
                            elif w.get('score', 0) < 0: states.append("🔴")
                            else: states.append("🟢")
                        
                        sc1, sc2 = st.columns([3, 1])
                        sc1.write(f"Set {i//chunk + 1} ({i+1}-{min(i+chunk, len(words))}): {' '.join(states)}")
                        if sc2.button(f"Học Set {i//chunk + 1}", key=f"sub_{name}_{i}"):
                            st.session_state.update({"qs": create_smart_quiz(subset), "curr_nb": name, "mode": "study", "idx": 0, "answered": False})
                            st.rerun()
            st.divider()

# --- UI ÔN TẬP ---
else:
    ch, cex = st.columns([5, 1])
    ch.write(f"### {st.session_state.curr_nb.upper()} ({st.session_state.idx+1}/{len(st.session_state.qs)})")
    if cex.button("Thoát"): st.session_state.mode = "manage"; st.rerun()

    if st.session_state.idx < len(st.session_state.qs):
        q = st.session_state.qs[st.session_state.idx]
        st.progress(st.session_state.idx / len(st.session_state.qs))
        st.markdown(f'<div class="question-container"><h1>{q["q"]}</h1></div>', unsafe_allow_html=True)
        
        with st.form(key=f"q_form_{st.session_state.idx}"):
            u_ans = st.text_input("Nhập đáp án:", key=f"ans_{st.session_state.idx}").strip()
            if st.form_submit_button("KIỂM TRA" if not st.session_state.answered else "TIẾP THEO ➡️"):
                if not st.session_state.answered:
                    st.session_state.answered = True
                    is_ok = (q['a'].lower() in u_ans.lower()) or (u_ans.lower() in q['a'].lower() and len(u_ans) > 0)
                    
                    # Cập nhật data gốc
                    nb_name = st.session_state.curr_nb
                    for w in st.session_state.notebooks[nb_name]['words']:
                        if w['hz'] == q['f']['hz']:
                            w['attempts'] = w.get('attempts', 0) + 1
                            w['score'] = w.get('score', 0) + (1 if is_ok else -1)
                    save_data(st.session_state.notebooks)
                    st.session_state.is_correct = is_ok; st.rerun()
                else:
                    st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

        if st.session_state.get('answered'):
            if st.session_state.is_correct: st.success("Giỏi lắm! Đúng rồi.")
            else: st.error(f"Sai rồi. Đáp án đúng là: {q['a'].capitalize()}")
            st.markdown(f"""<div class="result-card" style="text-align: center;">
                <h2 style="margin:0; color: {t['main']}">{q['f']['hz']}</h2>
                <p style="font-size: 1.2rem; margin-top:5px;">[{q['f']['py']}] - {q['f']['vn'].capitalize()}</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.balloons(); st.success("Chúc mừng bạn đã hoàn thành set học này!"); 
        if st.button("QUAY LẠI DANH SÁCH"): st.session_state.mode = "manage"; st.rerun()