import streamlit as st
import pandas as pd
import requests
import random
import time
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Cartola Intelligence AI", layout="wide", page_icon="⚽")

# 2. UI - ESTILO ORIGINAL (ESTRUTURA SAGRADA - NÃO MEXIDA)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #000000 0%, #111111 70%, #ff6600 100%); color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #ff6600; }
    h1, h2, h3, h4 { color: #ff6600 !important; text-transform: uppercase; font-weight: 800; }
    .expert-card { background-color: #FFFFFF; padding: 15px; border-radius: 15px; border: 3px solid #ff6600; text-align: center; color: #000 !important; min-height: 280px; }
    .status-mercado { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.4em; border: 2px solid white; margin-bottom: 20px; }
    .mercado-aberto { background-color: #00FF00; color: #000; }
    .mercado-fechado { background-color: #FF0000; color: #FFF; }
    .val-card { background: rgba(255,255,255,0.1); border: 1px solid #00FF00; border-radius: 10px; padding: 10px; text-align: center; }
    .min-val-badge { background: #ff6600; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; display: inline-block; margin-top: 5px; }
    .scout-container { background-color: #0e0e0e; border-radius: 15px; padding: 20px; border: 1px solid #333; margin-bottom: 15px; }
    .section-title { font-weight: bold; font-size: 1.2em; display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .ofensivo-title { color: #ff6600; }
    .defensivo-title { color: #ffffff; }
    .scout-item { font-size: 0.9em; margin-bottom: 2px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CARREGAMENTO DE DADOS (CORREÇÃO APENAS NA EXTRAÇÃO DO SCOUT)
@st.cache_data(ttl=300)
def load_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        m = requests.get("https://api.cartola.globo.com/atletas/mercado", headers=headers).json()
        p = requests.get("https://api.cartola.globo.com/partidas", headers=headers).json()
        mercado_status = requests.get("https://api.cartola.globo.com/mercado/status", headers=headers).json()
        
        df = pd.DataFrame(m['atletas'])
        clubes, posicoes = m['clubes'], m['posicoes']
        
        df['time_nome'] = df['clube_id'].astype(str).map({k: v['nome'] for k, v in clubes.items()})
        df['time_abv'] = df['clube_id'].astype(str).map({k: v['abreviacao'] for k, v in clubes.items()})
        df['pos_nome'] = df['posicao_id'].astype(str).map({k: v['nome'] for k, v in posicoes.items()})
        
        # ESSENCIAL: Transforma os scouts em colunas antes de exibir
        scouts_df = df['scout'].apply(pd.Series).fillna(0)
        df = pd.concat([df.drop(columns=['scout']), scouts_df], axis=1)
        
        def calc_v(row):
            if 'status_id' in row and row['status_id'] == 7:
                min_v = (row['preco_num'] * 0.37)
                return sum([(min_v * random.uniform(0.8, 1.2)) for _ in range(100)]) / 100 if 0 <= min_v <= 4.0 else -1
            return -1
        df['score_val'] = df.apply(calc_v, axis=1)
        
        return df, p['partidas'], clubes, mercado_status
    except:
        return pd.DataFrame(), [], {}, {}

df_raw, partidas, clubes_map, status_mer = load_data()

# 4. HEADER
st.markdown("<div style='text-align: center;'><img src='https://logodownload.org/wp-content/uploads/2017/05/cartola-fc-logo.png' width='80'></div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; margin-top:-10px;'>Intelligence AI</h1>", unsafe_allow_html=True)

if isinstance(status_mer, dict) and status_mer.get('status_mercado') == 1:
    st.markdown(f"<div class='status-mercado mercado-aberto'>✅ MERCADO ABERTO</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='status-mercado mercado-fechado'>🚫 MERCADO FECHADO</div>", unsafe_allow_html=True)

# 5. SIDEBAR (TODOS OS FILTROS ORIGINAIS)
st.sidebar.title("🛠️ FILTROS")
t_sel = st.sidebar.multiselect("Times", sorted(df_raw['time_nome'].unique()) if not df_raw.empty else [])
p_sel = st.sidebar.multiselect("Posições", ["Goleiro", "Zagueiro", "Lateral", "Meia", "Atacante", "Técnico"])
s_sel = st.sidebar.multiselect("Status", ["Provável", "Dúvida"], default=["Provável"])
s_map = {"Provável": 7, "Dúvida": 2}
s_ids = [s_map[s] for s in s_sel if s in s_map]

df_f = df_raw.copy()
if t_sel: df_f = df_f[df_f['time_nome'].isin(t_sel)]
if p_sel: df_f = df_f[df_f['pos_nome'].isin(p_sel)]
if s_ids: df_f = df_f[df_f['status_id'].isin(s_ids)]

# 6. TERMÔMETRO DE FAVORITISMO
with st.expander("📈 TERMÔMETRO DE FAVORITISMO", expanded=True):
    cols_t = st.columns(3)
    if partidas:
        for i, game in enumerate(partidas[:6]):
            try:
                c = clubes_map[str(game['clube_casa_id'])]['abreviacao']
                v = clubes_map[str(game['clube_visitante_id'])]['abreviacao']
                with cols_t[i % 3]: st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; text-align:center;'>{c} ⚔️ {v}</div>", unsafe_allow_html=True)
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

# 8. DICAS DO ESPECIALISTA
st.divider()
st.subheader("💡 DICAS DO ESPECIALISTA")
target_p = p_sel if p_sel else pos_list
for p in target_p:
    if p == "Técnico": continue
    st.markdown(f"#### Sugestões para {p}")
    c_dica = st.columns(4)
    pool = df_f[(df_f['pos_nome'] == p) & (df_f['status_id'] == 7)].copy()
    if not pool.empty:
        top_players = pool.nlargest(10, 'media_num').sample(min(4, len(pool)))
        for idx, (index, r) in enumerate(top_players.iterrows()):
            with c_dica[idx]:
                st.markdown(f"<div class='expert-card'><br><img src='{r['foto'].replace('FORMATO','140x140')}' width='80' style='border-radius:50%'><br><b>{r['apelido']}</b><br><small>{r['time_nome']}</small><br><b>Média: {r['media_num']:.2f}</b><br><div class='min-val-badge'>C$ {r['preco_num']}</div></div>", unsafe_allow_html=True)

# 9. MENU DE SCOUTS COMPLETO (RESTAURADO E PREENCHIDO)
st.divider()
st.subheader("📊 MENU DE SCOUTS DOS ATLETAS")
if not df_f.empty:
    for _, row in df_f.sort_values('media_num', ascending=False).head(20).iterrows():
        st.markdown(f"""
        <div class="scout-container">
            <div style="color: #ffffff; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 10px;">
                👤 {row['apelido']} | {row['pos_nome']} - {row['time_abv']} (Média: {row['media_num']:.2f})
            </div>
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div style="flex: 1; text-align: center; min-width: 120px;">
                    <img src="{row['foto'].replace('FORMATO','140x140')}" width="110">
                    <div class="min-val-badge">Mín p/ Val: {round(row['preco_num']*0.37, 2)}</div>
                </div>
                <div style="flex: 2; min-width: 200px; padding-left: 20px;">
                    <div class="section-title ofensivo-title">🔥 OFENSIVO</div>
                    <div class="scout-item">⚽ Gols: <b>{int(row.get('G', 0))}</b></div>
                    <div class="scout-item">🎯 Assistências: <b>{int(row.get('A', 0))}</b></div>
                    <div class="scout-item">👟 Fin. na Trave: <b>{int(row.get('FT', 0))}</b></div>
                    <div class="scout-item">👟 Fin. Defendida: <b>{int(row.get('FD', 0))}</b></div>
                    <div class="scout-item">👟 Fin. para Fora: <b>{int(row.get('FF', 0))}</b></div>
                    <div class="scout-item">🤕 Faltas Sofridas: <b>{int(row.get('FS', 0))}</b></div>
                </div>
                <div style="flex: 2; min-width: 200px; padding-left: 20px;">
                    <div class="section-title defensivo-title">🛡️ DEFENSIVO</div>
                    <div class="scout-item">⚔️ Desarmes: <b>{int(row.get('DS', 0))}</b></div>
                    <div class="scout-item">🛡️ Jogo sem Sofrer (SG): <b>{int(row.get('SG', 0))}</b></div>
                    <div class="scout-item">🧤 Defesas: <b>{int(row.get('DE', 0))}</b></div>
                    <div class="scout-item">🚫 Faltas Cometidas: <b>{int(row.get('FC', 0))}</b></div>
                    <div class="scout-item">🎴 Cartão Amarelo: <b>{int(row.get('CA', 0))}</b></div>
                    <div class="scout-item">🟥 Cartão Vermelho: <b>{int(row.get('CV', 0))}</b></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 10. REFRESH
if st.sidebar.button("🔄 ATUALIZAR DADOS"):
    st.rerun()