import streamlit as st
import pandas as pd
import requests
import random
import time
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Cartola Intelligence AI", layout="wide", page_icon="⚽")

# 2. UI - ESTILO ORIGINAL (ESTRUTURA SAGRADA)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #111111 70%, #ff6600 100%); color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #ff6600; }
    h1, h2, h3, h4 { color: #ff6600 !important; text-transform: uppercase; font-weight: 800; }
    .expert-card { background-color: #FFFFFF; padding: 15px; border-radius: 15px; border: 3px solid #ff6600; text-align: center; color: #000 !important; min-height: 250px; }
    .status-mercado { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.4em; border: 2px solid white; margin-bottom: 20px; }
    .mercado-aberto { background-color: #00FF00; color: #000; }
    .mercado-fechado { background-color: #FF0000; color: #FFF; }
    .val-card { background: rgba(255,255,255,0.1); border: 1px solid #00FF00; border-radius: 10px; padding: 10px; text-align: center; }
    .min-val-badge { background: #ff6600; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; display: inline-block; margin-top: 5px; }
    .scout-card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 15px; border-left: 5px solid #ff6600; }
    </style>
    """, unsafe_allow_html=True)

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=300)
def load_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        m = requests.get("https://api.cartola.globo.com/atletas/mercado", headers=headers).json()
        p = requests.get("https://api.cartola.globo.com/partidas", headers=headers).json()
        mercado = requests.get("https://api.cartola.globo.com/mercado/status", headers=headers).json()
        df = pd.DataFrame(m['atletas'])
        clubes, posicoes = m['clubes'], m['posicoes']
        df['time_nome'] = df['clube_id'].astype(str).map({k: v['nome'] for k, v in clubes.items()})
        df['time_escudo'] = df['clube_id'].astype(str).map({k: v['escudos']['60x60'] for k, v in clubes.items()})
        df['pos_nome'] = df['posicao_id'].astype(str).map({k: v['nome'] for k, v in posicoes.items()})
        df['time_abv'] = df['clube_id'].astype(str).map({k: v['abreviacao'] for k, v in clubes.items()})
        
        def calc_v(row):
            if 'status_id' in row and row['status_id'] == 7:
                min_v = (row['preco_num'] * 0.37)
                return sum([(min_v * random.uniform(0.8, 1.2)) for _ in range(100)]) / 100 if 0 <= min_v <= 4.0 else -1
            return -1
        df['score_val'] = df.apply(calc_v, axis=1)
        return df, p['partidas'], clubes, mercado
    except: return pd.DataFrame(), [], {}, {}

df_raw, partidas, clubes_map, status_mer = load_data()

# 4. HEADER
st.markdown("<div style='text-align: center;'><img src='https://logodownload.org/wp-content/uploads/2017/05/cartola-fc-logo.png' width='80'></div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; margin-top:-10px;'>Intelligence AI</h1>", unsafe_allow_html=True)

if isinstance(status_mer, dict) and status_mer.get('status_mercado') == 1:
    st.markdown(f"<div class='status-mercado mercado-aberto'>✅ MERCADO ABERTO</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='status-mercado mercado-fechado'>🚫 MERCADO FECHADO</div>", unsafe_allow_html=True)

# 5. SIDEBAR
st.sidebar.title("🛠️ FILTROS")
t_sel = st.sidebar.multiselect("Times", sorted(df_raw['time_nome'].unique()) if not df_raw.empty else [])
p_sel = st.sidebar.multiselect("Posições", ["Goleiro", "Zagueiro", "Lateral", "Meia", "Atacante", "Técnico"])
s_sel = st.sidebar.multiselect("Status", ["Provável", "Dúvida"], default=["Provável"])
s_map = {"Provável": 7, "Dúvida": 2}
s_ids = [s_map[s] for s in s_sel]

df_f = df_raw.copy()
if t_sel: df_f = df_f[df_f['time_nome'].isin(t_sel)]
if p_sel: df_f = df_f[df_f['pos_nome'].isin(p_sel)]
if s_ids and 'status_id' in df_f.columns: df_f = df_f[df_f['status_id'].isin(s_ids)]

# 6. TERMÔMETRO
with st.expander("📈 TERMÔMETRO DE FAVORITISMO", expanded=True):
    cols_t = st.columns(3)
    for i, game in enumerate(partidas[:6]):
        try:
            c_abv, f_abv = clubes_map[str(game['clube_casa_id'])]['abreviacao'], clubes_map[str(game['clube_visitante_id'])]['abreviacao']
            with cols_t[i % 3]: st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; text-align:center;'>{c_abv} ⚔️ {f_abv}</div>", unsafe_allow_html=True)
        except: pass

# 7. TOP 5 VALORIZAÇÃO
st.divider()
st.subheader("🚀 TOP 5 PARA VALORIZAR")
pos_list = ["Goleiro", "Zagueiro", "Lateral", "Meia", "Atacante"]
tabs_v = st.tabs(pos_list)
for i, p_tab in enumerate(pos_list):
    with tabs_v[i]:
        if not df_f.empty:
            top_v = df_f[(df_f['pos_nome'] == p_tab) & (df_f['score_val'] > 0)].nlargest(5, 'score_val')
            cv = st.columns(5)
            for j, (idx, r) in enumerate(top_v.iterrows()):
                cv[j].markdown(f"<div class='val-card'><img src='{r['foto'].replace('FORMATO','140x140')}' width='50'><br><b>{r['apelido']}</b><br><small>Mín: {round(r['preco_num']*0.37,1)}</small></div>", unsafe_allow_html=True)

# 8. 💡 DICAS DO ESPECIALISTA (4 SUGESTÕES SEM RÓTULOS)
st.divider()
st.subheader("💡 DICAS DO ESPECIALISTA")
target_p = p_sel if p_sel else pos_list
for p in target_p:
    st.markdown(f"#### Sugestões para {p}")
    c_dica = st.columns(4)
    pool = df_f[(df_f['pos_nome'] == p) & (df_f['status_id'] == 7)].copy() if 'status_id' in df_f.columns else pd.DataFrame()
    
    if not pool.empty:
        selecionados_ids = []
        # Seleciona 4 jogadores de destaque sem usar categorias fixas que confundem
        top_players = pool.nlargest(10, 'media_num').sample(4) if len(pool) >= 4 else pool.nlargest(4, 'media_num')
        
        for idx, (index, r) in enumerate(top_players.iterrows()):
            with c_dica[idx]:
                st.markdown(f"""
                <div class='expert-card'>
                    <br>
                    <img src='{r['foto'].replace('FORMATO','140x140')}' width='80' style='border-radius:50%'><br>
                    <b>{r['apelido']}</b><br>
                    <small>{r['time_nome']}</small><br>
                    <b>Média: {r['media_num']:.2f}</b><br>
                    <div class='min-val-badge'>C$ {r['preco_num']}</div>
                </div>
                """, unsafe_allow_html=True)

# 9. 📊 SCOUTS DETALHADOS & CARDS
st.divider()
st.subheader("📊 SCOUTS DETALHADOS & CARDS")
if not df_f.empty:
    sc_df = pd.concat([df_f.drop(columns=['scout']), df_f['scout'].apply(pd.Series).fillna(0)], axis=1)
    for _, row in sc_df.sort_values('media_num', ascending=False).iterrows():
        with st.expander(f"👤 {row['apelido']} | {row['pos_nome']} - {row['time_abv']} (Média: {row['media_num']:.2f})"):
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1:
                st.image(row['foto'].replace('FORMATO','140x140'), width=120)
                st.markdown(f"<div class='min-val-badge'>Mín p/ Val: {round(row['preco_num']*0.37,2)}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("### 🔥 OFENSIVO")
                if row['pos_nome'] != 'Goleiro':
                    st.write(f"⚽ Gols: **{row.get('G', 0)}** | 🎯 Assist: **{row.get('A', 0)}**")
                    st.write(f"👟 Finalizações: **{int(row.get('FT',0)+row.get('FD',0)+row.get('FF',0))}**")
                st.write(f"🟨 CA: **{row.get('CA', 0)}** | 🟥 CV: **{row.get('CV', 0)}**")
                st.write(f"🤕 Faltas Sofridas: **{row.get('FS', 0)}**")
            with c3:
                st.markdown("### 🛡️ DEFENSIVO")
                if row['pos_nome'] == 'Goleiro':
                    st.write(f"🧤 Defesas: **{row.get('DE', 0)}** | ⚽ GS: **{row.get('GS', 0)}**")
                    st.write(f"🧤 Pênalti Defendido: **{row.get('DP', 0)}**")
                else:
                    st.write(f"⚔️ Desarmes: **{row.get('DS', 0)}**")
                    if row['pos_nome'] in ['Zagueiro', 'Lateral']:
                        st.write(f"🛡️ SG: **{row.get('SG', 0)}**")
                st.write(f"🚫 Faltas Cometidas: **{row.get('FC', 0)}**")

# 10. REFRESH MANUAL
st.sidebar.divider()
if st.sidebar.button("🔄 ATUALIZAR DADOS"):
    st.rerun()