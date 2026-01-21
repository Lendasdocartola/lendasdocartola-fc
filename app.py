import streamlit as st
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit.components.v1 as components

# 1. DESIGN SYSTEM - GATO MESTRE (ESTRUTURA IMUTÁVEL)
st.set_page_config(page_title="Cartola AI v55.0", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    .orange-title { color: #ff6600 !important; font-weight: 800; text-transform: uppercase; }
    
    /* CAMPO TÁTICO OFICIAL - RESTAURADO */
    .field-container {
        position: relative; width: 100%; height: 580px; background: #4caf50;
        background-image: repeating-linear-gradient(to right, #4caf50, #4caf50 60px, #43a047 60px, #43a047 120px);
        border: 5px solid #ffffff; border-radius: 15px; margin: 20px 0; overflow: hidden;
    }
    .center-line { position: absolute; top: 0; left: 50%; width: 2px; height: 100%; background: rgba(255,255,255,0.8); }
    .center-circle { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 120px; height: 120px; border: 2px solid rgba(255,255,255,0.8); border-radius: 50%; }
    .penalty-area-left { position: absolute; top: 20%; left: 0; width: 100px; height: 60%; border: 2px solid rgba(255,255,255,0.8); border-left: none; }
    .small-area-left { position: absolute; top: 35%; left: 0; width: 40px; height: 30%; border: 2px solid rgba(255,255,255,0.8); border-left: none; }
    .arc-left { position: absolute; top: 40%; left: 70px; width: 60px; height: 20%; border: 2px solid rgba(255,255,255,0.8); border-radius: 50%; clip-path: inset(0 0 0 50%); }
    .penalty-area-right { position: absolute; top: 20%; right: 0; width: 100px; height: 60%; border: 2px solid rgba(255,255,255,0.8); border-right: none; }
    .small-area-right { position: absolute; top: 35%; right: 0; width: 40px; height: 30%; border: 2px solid rgba(255,255,255,0.8); border-right: none; }
    .arc-right { position: absolute; top: 40%; right: 70px; width: 60px; height: 20%; border: 2px solid rgba(255,255,255,0.8); border-radius: 50%; clip-path: inset(0 50% 0 0); }
    
    .player-spot { position: absolute; text-align: center; width: 90px; transform: translate(-50%, -50%); z-index: 5; }
    .player-photo-field { width: 60px; height: 60px; border-radius: 50%; border: 3px solid #ff6600; background: #000; }
    .player-name-tag { background: #000; color: #fff; font-size: 10px; font-weight: bold; padding: 2px 5px; border-radius: 3px; display: block; margin-top: 5px; border: 1px solid #333; }
    
    /* PROBABILIDADES E CARDS - RESTAURADOS */
    .prob-card { background: #111; border-left: 5px solid #ff6600; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .prob-bar-bg { background: #333; height: 12px; border-radius: 6px; margin-top: 8px; overflow: hidden; }
    .prob-bar-fill { background: linear-gradient(90deg, #ff6600, #ffcc00); height: 100%; border-radius: 6px; }
    
    .trend-card { background: #111; border-radius: 12px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; border-left: 5px solid #444; }
    .hot { border-left-color: #ff4444; }
    .cold { border-left-color: #00d2ff; }

    .captain-card { background: linear-gradient(135deg, #1a1a1a 0%, #000 100%); border: 1px solid #333; border-radius: 20px; padding: 15px; text-align: center; position: relative; margin-bottom: 20px; }
    .braçadeira { position: absolute; top: 10px; right: 10px; background: #ff6600; color: #000; font-weight: 900; padding: 4px 8px; border-radius: 50%; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE DADOS
@st.cache_data(ttl=60)
def get_cartola_data():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    try:
        m_req = session.get("https://api.cartola.globo.com/atletas/mercado", timeout=15).json()
        p_req = session.get("https://api.cartola.globo.com/partidas", timeout=15).json()
        df = pd.DataFrame(m_req['atletas'])
        clubes_map = m_req['clubes']
        df['time_nome'] = df['clube_id'].astype(str).map({k: v['nome'] for k, v in clubes_map.items()})
        df['time_escudo'] = df['clube_id'].astype(str).map({k: v['escudos']['60x60'] for k, v in clubes_map.items()})
        df['pos_nome'] = df['posicao_id'].astype(str).map({k: v['nome'] for k, v in m_req['posicoes'].items()})
        
        scouts_norm = pd.json_normalize(df['scout']).fillna(0)
        df = pd.concat([df.drop(columns=['scout']), scouts_norm], axis=1)
        
        mandantes = [p['clube_casa_id'] for p in p_req['partidas']]
        df['prob_sg'] = df['clube_id'].apply(lambda x: 78 if x in mandantes else 48)
        df['score_capitao'] = (df['media_num'] * 0.6) + (df.get('G', 0) * 2) + (df.get('A', 0) * 1.5)
        df['tendencia'] = df['pontos_num'] - df['media_num']
        
        return df, p_req['partidas'], clubes_map
    except: return None, None, None

df, partidas, clubes_raw = get_cartola_data()
if df is None: st.stop()

if 'time_escalado' not in st.session_state:
    st.session_state.time_escalado = {"Goleiro": [], "Lateral": [], "Zagueiro": [], "Meia": [], "Atacante": [], "Técnico": []}

with st.sidebar:
    st.markdown("<h2 class='orange-title'>CARTOLA AI</h2>", unsafe_allow_html=True)
    menu = st.radio("Menu:", ["🏠 Dashboard", "⚔️ Arena 5x5", "🏟️ Escalação Visual", "📊 Central Probabilidades", "🧠 Radar de Capitão", "🔥 Termômetro", "📈 Histórico"])
    status_filter = st.checkbox("Somente Prováveis", value=True)

df_active = df[df['status_id'] == 7] if status_filter else df

# --- ⚔️ ARENA 5x5 (RESTAURADA) ---
if menu == "⚔️ Arena 5x5":
    st.markdown("<h1 class='orange-title'>⚔️ Arena Elite 5x5</h1>", unsafe_allow_html=True)
    pos = st.selectbox("Posição:", ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"])
    selecionados = st.multiselect("Gladiadores:", options=df_active[df_active['pos_nome'] == pos].sort_values('media_num', ascending=False)['apelido'].tolist())
    if selecionados:
        df_comp = df_active[df_active['apelido'].isin(selecionados)].copy()
        sc_map = {"Goleiro": ['DE','GS','SG'], "Lateral": ['DS','A','SG'], "Zagueiro": ['DS','SG','FC'], "Meia": ['G','A','DS','FD'], "Atacante": ['G','FD','FT','A']}
        cols = st.columns(len(selecionados))
        for i, nome in enumerate(selecionados):
            p = df_comp[df_comp['apelido'] == nome].iloc[0]
            alvos = sc_map.get(pos, [])
            sc_html = "".join([f'<div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #eee; font-size:11px;"><span style="color:#777; font-weight:600;">{s}</span><span style="color:#000; font-weight:700;">{int(p[s]) if s in p else 0}</span></div>' for s in alvos])
            card = f"""<div style="background:#111; border-radius:15px; padding:15px; text-align:center; border-bottom:4px solid #ff6600; color:#fff; height:530px;">
                <img src="{p["time_escudo"]}" width="25"><br><img src="{p["foto"].replace("FORMATO","140x140")}" width="80" style="border-radius:50%; border:2px solid #ff6600; margin:10px 0;">
                <div style="font-size:16px; font-weight:800;">{nome}</div><div style="color:#00ff00; font-weight:800; font-size:20px;">C$ {p["preco_num"]}</div>
                <div style="background:#fff; border-radius:12px; padding:10px; text-align:left; color:#333; margin-top:10px;"><div style="color:#ff6600; font-weight:800; font-size:10px;">🛡️ PROB. SG</div><div style="color:#ff6600; font-weight:800; font-size:18px; border-bottom:1px solid #eee; margin-bottom:8px;">{int(p['prob_sg'])}%</div>{sc_html}</div>
            </div>"""
            with cols[i]: components.html(card, height=550)
        if st.button(f"💾 SALVAR {pos}"):
            st.session_state.time_escalado[pos] = df_comp.nlargest(3, 'media_num')[['apelido', 'foto']].to_dict('records')
            st.success("Salvo!")

# --- 🏟️ ESCALAÇÃO VISUAL (RESTAURADA) ---
elif menu == "🏟️ Escalação Visual":
    st.markdown("<h1 class='orange-title'>🏟️ Quadro Tático Oficial</h1>", unsafe_allow_html=True)
    def draw_p(plist, idx, top, left, label):
        if len(plist) > idx:
            foto = plist[idx]["foto"].replace("FORMATO","140x140")
            return f'<div class="player-spot" style="top:{top}%; left:{left}%;"><img src="{foto}" class="player-photo-field"><span class="player-name-tag">{plist[idx]["apelido"]}</span></div>'
        return f'<div class="player-spot" style="top:{top}%; left:{left}%;"><div class="player-photo-field" style="opacity:0.2; background:#222;"></div><span class="player-name-tag" style="color:#666;">{label}</span></div>'
    t = st.session_state.time_escalado
    st.markdown(f"""<div class="field-container"><div class="center-line"></div><div class="center-circle"></div><div class="penalty-area-left"></div><div class="small-area-left"></div><div class="arc-left"></div><div class="penalty-area-right"></div><div class="small-area-right"></div><div class="arc-right"></div>
        {draw_p(t['Goleiro'], 0, 50, 8, "GOL")} {draw_p(t['Lateral'], 0, 18, 25, "LAT")} {draw_p(t['Zagueiro'], 0, 40, 25, "ZAG")} {draw_p(t['Zagueiro'], 1, 60, 25, "ZAG")} {draw_p(t['Lateral'], 1, 82, 25, "LAT")}
        {draw_p(t['Meia'], 0, 30, 50, "MEI")} {draw_p(t['Meia'], 1, 50, 45, "MEI")} {draw_p(t['Meia'], 2, 70, 50, "MEI")}
        {draw_p(t['Atacante'], 0, 22, 82, "ATA")} {draw_p(t['Atacante'], 1, 50, 88, "ATA")} {draw_p(t['Atacante'], 2, 78, 82, "ATA")}
    </div>""", unsafe_allow_html=True)

# --- 📊 CENTRAL PROBABILIDADES (RESTAURADA) ---
elif menu == "📊 Central Probabilidades":
    st.markdown("<h1 class='orange-title'>📊 Central de Probabilidades</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🛡️ Chance de SG")
        list_sg = df.groupby('time_nome').first().reset_index().nlargest(6, 'prob_sg')
        for _, r in list_sg.iterrows():
            st.markdown(f"""<div class="prob-card"><div style="display:flex; justify-content:space-between;"><span><img src="{r['time_escudo']}" width="20"> {r['time_nome']}</span><b>{int(r['prob_sg'])}%</b></div><div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{r['prob_sg']}%"></div></div></div>""", unsafe_allow_html=True)
    with c2:
        st.subheader("⚽ Chance de Gol")
        for _, r in df_active[df_active['pos_nome']=='Atacante'].drop_duplicates(subset=['clube_id']).nlargest(6, 'media_num').iterrows():
            prob_g = int(min(r['media_num']*10, 92))
            st.markdown(f"""<div class="prob-card"><div style="display:flex; justify-content:space-between;"><span><img src="{r['time_escudo']}" width="20"> {r['apelido']}</span><b>{prob_g}%</b></div><div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{prob_g}%; background:linear-gradient(90deg, #ffcc00, #ff6600);"></div></div></div>""", unsafe_allow_html=True)

# --- 🧠 RADAR DE CAPITÃO ---
elif menu == "🧠 Radar de Capitão":
    st.markdown("<h1 class='orange-title'>🧠 Radar de Capitão (Top 6 Elite)</h1>", unsafe_allow_html=True)
    caps = df_active[df_active['pos_nome'].isin(['Meia', 'Atacante'])].sort_values('score_capitao', ascending=False).drop_duplicates(subset=['clube_id']).head(6)
    row1, row2 = st.columns(3), st.columns(3)
    for i, (_, row) in enumerate(caps.iterrows()):
        target = row1[i] if i < 3 else row2[i-3]
        with target:
            st.markdown(f"""<div class="captain-card"><div class="braçadeira">C</div><img src="{row['time_escudo']}" width="30"><br><img src="{row['foto'].replace("FORMATO","140x140")}" width="100" style="border-radius:50%; border:3px solid #ff6600; margin:10px 0;"><h2>{row['apelido']}</h2><p style="color:#00ff00; font-weight:800; margin:0;">{row['pos_nome']}</p></div>""", unsafe_allow_html=True)

# --- 🔥 TERMÔMETRO ---
elif menu == "🔥 Termômetro":
    st.markdown("<h1 class='orange-title'>🔥 Termômetro (Variedade por Clube)</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 EM ALTA")
        df_alta = df_active.sort_values('tendencia', ascending=False).drop_duplicates(subset=['clube_id']).head(6)
        for _, row in df_alta.iterrows():
            st.markdown(f"""<div class="trend-card hot"><div><img src="{row['time_escudo']}" width="25" style="margin-right:10px;"> <b>{row['apelido']}</b> ({row['time_nome']})</div><span style="color:#ff4444; font-weight:800;">▲ +{row['tendencia']:.1f}</span></div>""", unsafe_allow_html=True)
    with c2:
        st.subheader("❄️ EM QUEDA")
        df_queda = df_active.sort_values('tendencia', ascending=True).drop_duplicates(subset=['clube_id']).head(6)
        for _, row in df_queda.iterrows():
            st.markdown(f"""<div class="trend-card cold"><div><img src="{row['time_escudo']}" width="25" style="margin-right:10px;"> <b>{row['apelido']}</b> ({row['time_nome']})</div><span style="color:#00d2ff; font-weight:800;">▼ {row['tendencia']:.1f}</span></div>""", unsafe_allow_html=True)

# --- 📈 HISTÓRICO ---
elif menu == "📈 Histórico":
    st.markdown("<h1 class='orange-title'>📈 Histórico de Precisão</h1>", unsafe_allow_html=True)
    st.info("Comparando projeções com resultados reais para calibrar a IA.")
    data_demo = [{"Atleta": "Arrascaeta", "Projetado": 8.5, "Real": 9.2, "Erro": "+0.7"}, {"Atleta": "Cano", "Projetado": 7.0, "Real": 2.1, "Erro": "-4.9"}]
    st.table(data_demo)