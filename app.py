import streamlit as st
import pandas as pd
import requests
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. DESIGN SYSTEM - ESTRUTURA BLINDADA (PRETO E BRANCO/LARANJA)
st.set_page_config(page_title="Cartola AI v12.0", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800 !important; }
    p, span, label { color: #E0E0E0 !important; }
    
    div[data-baseweb="select"] > div { background-color: #151515 !important; border: 1px solid #333 !important; }
    div[data-baseweb="select"] * { color: #ffffff !important; }
    
    .battle-card {
        background: #111111; border: 1px solid #222; border-radius: 16px;
        padding: 18px; text-align: center; border-bottom: 4px solid #ff6600;
    }
    
    .progress-bg { background: #222; border-radius: 10px; width: 100%; height: 8px; margin-top: 5px; }
    .progress-fill { background: #ff6600; height: 8px; border-radius: 10px; }
    .risk-fill { background: linear-gradient(90deg, #ffff00, #ff0000) !important; }

    /* SIMULADOR BOX */
    .simulador-box {
        background: #111; border: 1px dashed #444; border-radius: 12px;
        padding: 20px; margin-top: 20px;
    }
    .score-badge { padding: 5px 15px; border-radius: 20px; font-weight: 800; font-size: 1.2rem; }
    
    .veredito-box {
        background: #ffffff; padding: 20px; border-radius: 12px; 
        border-left: 10px solid #00ff00; margin-top: 25px; text-align: center;
    }
    .veredito-box * { color: #000000 !important; font-weight: bold; }
    .orange-title { color: #ff6600 !important; font-weight: 800; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE DADOS
@st.cache_data(ttl=60)
def get_cartola_data():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        m_data = session.get("https://api.cartola.globo.com/atletas/mercado", headers=headers, timeout=15).json()
        df = pd.DataFrame(m_data['atletas'])
        clubes_raw = m_data['clubes']
        df['time_nome'] = df['clube_id'].astype(str).map({k: v['nome'] for k, v in clubes_raw.items()})
        df['time_escudo'] = df['clube_id'].astype(str).map({k: v['escudos']['60x60'] for k, v in clubes_raw.items()})
        df['pos_nome'] = df['posicao_id'].astype(str).map({k: v['nome'] for k, v in m_data['posicoes'].items()})
        
        sc_df = pd.json_normalize(df['scout']).fillna(0)
        df = pd.concat([df.drop(columns=['scout']), sc_df], axis=1)
        
        for col in ['FC', 'CA', 'GS']:
            if col not in df.columns: df[col] = 0
            
        df['risco_negativo'] = (df['FC'] * 0.5) + (df['CA'] * 2) + (df['GS'] * 2)
        df['score_potencial'] = (df['media_num'] * 0.6) + (df['pontos_num'] * 0.4)
        return df
    except: return None

df = get_cartola_data()
if df is None: st.stop()

# 3. NAVEGAÇÃO
with st.sidebar:
    st.markdown("<h2 class='orange-title'>CARTOLA AI</h2>", unsafe_allow_html=True)
    menu = st.radio("Menu:", ["🏠 Dashboard", "⚔️ Arena 5x5", "📍 Favoritismo"])

# --- ARENA 5x5 COM SIMULADOR ---
if menu == "⚔️ Arena 5x5":
    st.markdown("<h1 class='orange-title'>⚔️ Arena 5x5</h1>", unsafe_allow_html=True)
    
    pos = st.selectbox("Escolha a Posição", ["Técnico", "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"])
    lista_jog = df[df['pos_nome'] == pos].sort_values('media_num', ascending=False)
    selecionados = st.multiselect("Selecione os Gladiadores:", options=lista_jog['apelido'].tolist(), max_selections=5)

    if len(selecionados) >= 2:
        df_comp = lista_jog[lista_jog['apelido'].isin(selecionados)].copy()
        
        # Grid de Cards (Design Travado)
        cols = st.columns(len(selecionados))
        for i, nome in enumerate(selecionados):
            p = df_comp[df_comp['apelido'] == nome].iloc[0]
            with cols[i]:
                st.markdown(f'<div class="battle-card"><img src="{p["time_escudo"]}" width="25"><div class="player-name">{nome}</div><div style="color:#00ff00; font-size:1.2rem;">{p["media_num"]}</div></div>', unsafe_allow_html=True)

        # TABELA TÉCNICA (Protegida)
        st.markdown("### 📊 Comparativo + ⚠️ Risco")
        scouts_alvo = {"Técnico":['media_num','score_potencial'], "Goleiro":['media_num','DE','risco_negativo'], "Lateral":['media_num','DS','A','risco_negativo'], "Zagueiro":['media_num','DS','SG','risco_negativo'], "Meia":['media_num','G','A','risco_negativo'], "Atacante":['media_num','G','FD','risco_negativo']}
        
        for scout in [s for s in scouts_alvo[pos] if s in df_comp.columns]:
            st.write(f"**{scout.replace('media_num','Média').replace('risco_negativo','RISCO')}**")
            max_v = df_comp[scout].max() if df_comp[scout].max() != 0 else 1
            b_cols = st.columns(len(selecionados))
            for i, nome in enumerate(selecionados):
                val = df_comp[df_comp['apelido'] == nome][scout].values[0]
                percent = min((val/max_v)*100, 100) if val > 0 else 0
                cor = "risk-fill" if "risco" in scout else ""
                b_cols[i].markdown(f'<div class="progress-bg"><div class="progress-fill {cor}" style="width:{percent}%;"></div></div>', unsafe_allow_html=True)

        # VEREDITO
        qtd = {"Técnico": 1, "Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3}
        venc_df = df_comp.nlargest(qtd.get(pos, 1), 'score_potencial')
        custo = venc_df['preco_num'].sum()
        escudos_html = "".join([f'<img src="{r["time_escudo"]}" width="25"> {r["apelido"]} &nbsp;' for _, r in venc_df.iterrows()])

        st.markdown(f'<div class="veredito-box"><p>🏆 ESCOLHIDOS AI</p><h2>{escudos_html}</h2><p>CUSTO: C$ {round(custo,2)}</p></div>', unsafe_allow_html=True)

        # --- INOVAÇÃO: SIMULADOR DE PONTUAÇÃO ---
        st.markdown("### 🔮 Simulador de Pontuação AI")
        with st.expander("Clique para ver a Projeção da Rodada", expanded=True):
            s_col1, s_col2, s_col3 = st.columns(3)
            
            # Cálculo de Projeção (Média ajustada por fator de risco e aleatoriedade controlada)
            base_score = venc_df['media_num'].sum()
            risco_total = venc_df['risco_negativo'].mean()
            
            proj_esperada = base_score * 1.1 - (risco_total * 0.2)
            proj_otimista = proj_esperada * 1.4
            proj_pessimista = proj_esperada * 0.6
            
            with s_col1:
                st.markdown(f'<div class="simulador-box" style="border-color:red;">🔴 PESSIMISTA<br><span class="score-badge" style="color:red;">{round(proj_pessimista, 2)} pts</span></div>', unsafe_allow_html=True)
            with s_col2:
                st.markdown(f'<div class="simulador-box" style="border-color:yellow;">🟡 ESPERADO<br><span class="score-badge" style="color:yellow;">{round(proj_esperada, 2)} pts</span></div>', unsafe_allow_html=True)
            with s_col3:
                st.markdown(f'<div class="simulador-box" style="border-color:green;">🟢 OTIMISTA<br><span class="score-badge" style="color:green;">{round(proj_otimista, 2)} pts</span></div>', unsafe_allow_html=True)

    else:
        st.info("Selecione os jogadores para simular a pontuação.")