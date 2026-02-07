import streamlit as st
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import random

# 1. DESIGN SYSTEM - GATO MESTRE (ESTRUTURA INTEGRAL V56.0)
st.set_page_config(page_title="Cartola AI v56.1 - Elite", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* CORES DO SISTEMA: Laranja e Branco e algumas coisas em preto */
    .stApp { background-color: #FFFFFF; color: #000000; font-family: 'Inter', sans-serif; }
    .orange-title { color: #FF6600 !important; font-weight: 800; text-transform: uppercase; }
    
    /* CAMPO TÁTICO OFICIAL - MARCAÇÕES BRANCAS */
    .field-container {
        position: relative; width: 100%; height: 580px; background: #4caf50;
        background-image: repeating-linear-gradient(to right, #4caf50, #4caf50 60px, #43a047 60px, #43a047 120px);
        border: 5px solid #000000; border-radius: 15px; margin: 20px 0; overflow: hidden;
    }
    .center-line { position: absolute; top: 0; left: 50%; width: 2px; height: 100%; background: rgba(255,255,255,0.9); z-index: 1; }
    .center-circle { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 120px; height: 120px; border: 2px solid white; border-radius: 50%; z-index: 1; }
    
    .penalty-area-left { position: absolute; top: 20%; left: 0; width: 100px; height: 60%; border: 2px solid white; border-left: none; z-index: 1; }
    .small-area-left { position: absolute; top: 35%; left: 0; width: 40px; height: 30%; border: 2px solid white; border-left: none; z-index: 1; }
    .arc-left { position: absolute; top: 40%; left: 70px; width: 60px; height: 20%; border: 2px solid white; border-radius: 50%; clip-path: inset(0 0 0 50%); z-index: 1; }
    
    .penalty-area-right { position: absolute; top: 20%; right: 0; width: 100px; height: 60%; border: 2px solid white; border-right: none; z-index: 1; }
    .small-area-right { position: absolute; top: 35%; right: 0; width: 40px; height: 30%; border: 2px solid white; border-right: none; z-index: 1; }
    .arc-right { position: absolute; top: 40%; right: 70px; width: 60px; height: 20%; border: 2px solid white; border-radius: 50%; clip-path: inset(0 50% 0 0); z-index: 1; }

    .player-spot { position: absolute; text-align: center; width: 90px; transform: translate(-50%, -50%); z-index: 5; transition: all 0.5s ease; }
    .player-photo-field { width: 60px; height: 60px; border-radius: 50%; border: 3px solid #FF6600; background: #000; position: relative; }
    .player-name-tag { background: #000000; color: #FFFFFF; font-size: 10px; font-weight: bold; padding: 2px 5px; border-radius: 3px; display: block; margin-top: 5px; border: 1px solid #FF6600; }
    
    .live-pts { position: absolute; top: -10px; right: -10px; background: #FF6600; color: #FFFFFF; font-weight: 800; font-size: 11px; padding: 2px 6px; border-radius: 10px; border: 1px solid #000; }
    .log-container { background: #000000; border: 1px solid #FF6600; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; color: #FFFFFF; margin-top: 10px; }

    .val-card-v2 { background: #FFFFFF; border-left: 4px solid #FF6600; padding: 12px; margin-bottom: 8px; border-radius: 0 8px 8px 0; border: 1px solid #000000; }
    .prob-bar-bg { background: #E0E0E0; height: 6px; border-radius: 3px; margin-top: 5px; overflow: hidden; }
    .prob-bar-fill { background: #FF6600; height: 100%; transition: width 0.5s; }
    
    /* CARDS DO BANCO (BENCH-CARD) */
    .bench-card-v2 {
        background: #000000; border: 1px solid #333; border-radius: 8px;
        padding: 10px; text-align: center; color: white; min-width: 80px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 10px;
    }
    .bench-plus-v2 { color: #FF6600; font-size: 20px; font-weight: bold; margin-bottom: 2px; }
    .bench-pos-v2 { font-size: 11px; font-weight: 800; text-transform: uppercase; color: #FFFFFF; }

    /* SIDEBAR - FUNDO PRETO E TEXTOS BRANCOS */
    [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 3px solid #FF6600; 
    }
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stRadio p,
    [data-testid="stSidebar"] div[role="radiogroup"] { 
        color: #FFFFFF !important; 
    }
    </style>
""", unsafe_allow_html=True)

# 2. MOTOR DE DADOS COM TRATAMENTO LIVE
@st.cache_data(ttl=60)
def get_cartola_data():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    try:
        m_req = session.get("https://api.cartola.globo.com/atletas/mercado", timeout=10).json()
        p_req = session.get("https://api.cartola.globo.com/partidas", timeout=10).json()
        
        try:
            l_req = session.get("https://api.cartola.globo.com/atletas/pontuados", timeout=5).json()
            live_pts = l_req.get('atletas', {})
        except:
            live_pts = {}

        df = pd.DataFrame(m_req['atletas'])
        clubes_map = m_req['clubes']
        
        df['time_nome'] = df['clube_id'].astype(str).map({k: v['nome'] for k, v in clubes_map.items()})
        df['time_escudo'] = df['clube_id'].astype(str).map({k: v['escudos']['60x60'] for k, v in clubes_map.items()})
        df['pos_nome'] = df['posicao_id'].astype(str).map({k: v['nome'] for k, v in m_req['posicoes'].items()})
        
        def parse_live(atleta_id):
            aid = str(atleta_id)
            if aid in live_pts:
                return float(live_pts[aid].get('pontuacao', 0)), live_pts[aid].get('scout', {})
            return 0.0, {}

        df['pontos_live'], df['scouts_live'] = zip(*df['atleta_id'].apply(parse_live))
        
        scouts_norm = pd.json_normalize(df['scout']).fillna(0)
        df = pd.concat([df.drop(columns=['scout']), scouts_norm], axis=1)
        
        mandantes = [p['clube_casa_id'] for p in p_req['partidas']]
        df['is_mandante'] = df['clube_id'].apply(lambda x: 1.15 if x in mandantes else 1.0)
        df['prob_sg'] = df['clube_id'].apply(lambda x: 78 if x in mandantes else 48)
        
        df['media_basica'] = (df.get('DS', 0) * 1.2) + (df.get('FS', 0) * 0.5) + (df.get('FD', 0) * 1.2) + (df.get('DE', 0) * 1.0)
        df['score_capitao'] = (df['media_num'] * 0.6) + (df.get('G', 0) * 2) + (df.get('A', 0) * 1.5)
        df['tendencia'] = df['pontos_num'] - df['media_num']
        
        return df, p_req['partidas'], clubes_map, m_req.get('rodada', 1)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, 1

df, partidas, clubes_raw, rodada_atual = get_cartola_data()
if df is None: st.stop()

# ESTADO DE SESSÃO
if 'time_escalado' not in st.session_state:
    st.session_state.time_escalado = {"Goleiro": [], "Lateral": [], "Zagueiro": [], "Meia": [], "Atacante": [], "Técnico": []}
if 'reserva_escalado' not in st.session_state:
    st.session_state.reserva_escalado = {"Goleiro": None, "Lateral": None, "Zagueiro": None, "Meia": None, "Atacante": None}
if 'posicao_luxo' not in st.session_state:
    st.session_state.posicao_luxo = None
if 'historico_arena' not in st.session_state:
    st.session_state.historico_arena = {r: {p: [] for p in ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"]} for r in range(1, 39)}
if 'seed_campo' not in st.session_state:
    st.session_state.seed_campo = 0

with st.sidebar:
    st.markdown("<h2 class='orange-title'>CARTOLA  2026</h2>", unsafe_allow_html=True)
    # Trocado para o ícone de prancheta (📋) conforme pedido
    menu = st.radio("Menu:", ["🏠 Dashboard", "⚽ Minhas Dicas", "🔍 Raio-X do Craque", "📋 Quadro Tático", "📊 Central Probabilidades", "🧠 Radar de Capitão", "🔥 Termômetro", "💰 Simulador de Valorização", "🏟️ Análise de Confrontos", "📈 Histórico"])
    
    status_filter = st.checkbox("Somente Prováveis", value=True)

df_active = df[df['status_id'] == 7] if status_filter else df

# --- 🏠 DASHBOARD (V99.0 - DESIGN SHADOW & BOLSA DE VALORES) ---
if menu == "🏠 Dashboard":
    st.markdown("<h1 class='orange-title'>🏠 Dashboard Analytics</h1>", unsafe_allow_html=True)

    # --- 1. CARDS DE RESUMO (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_jogadores = len(df_active)
    media_preco = df_active['preco_num'].mean()
    idx_max = df_active['pontos_num'].idxmax()
    craque_rodada = df_active.loc[idx_max]
    total_clubes = 20  # AJUSTADO PARA 20 TIMES

    def kpi_card(titulo, valor, sub):
        return f"""
        <div style="background: white; border: 3px solid #000; padding: 15px; border-radius: 12px; box-shadow: 5px 5px 0px #FF6600; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 10px; font-weight: 900; color: #666; text-transform: uppercase;">{titulo}</div>
            <div style="font-size: 24px; font-weight: 900; color: #000;">{valor}</div>
            <div style="font-size: 10px; color: #FF6600; font-weight: bold;">{sub}</div>
        </div>
        """

    with c1: st.markdown(kpi_card("Atletas Ativos", total_jogadores, "NA BASE LIVE"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Preço Médio", f"C$ {media_preco:.2f}", "POR JOGADOR"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Maior Pontuação", f"{craque_rodada['pontos_num']:.2f}", craque_rodada['apelido'].upper()), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Clubes", total_clubes, "SÉRIE A 2026"), unsafe_allow_html=True)

    # --- 2. ÁREA DE GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.markdown('<div style="background:white; border:3px solid #000; padding:15px; border-radius:12px; box-shadow: 6px 6px 0px #000; color:#000;">', unsafe_allow_html=True)
        st.markdown("<b style='color:#000'>📊 MÉDIA DE PONTOS POR POSIÇÃO</b>", unsafe_allow_html=True)
        df_pos = df_active.groupby('pos_nome')['media_num'].mean().sort_values(ascending=False).reset_index()
        st.bar_chart(df_pos.set_index('pos_nome'), color="#FF6600")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_graf2:
        st.markdown('<div style="background:white; border:3px solid #000; padding:15px; border-radius:12px; box-shadow: 6px 6px 0px #000; color:#000;">', unsafe_allow_html=True)
        st.markdown("<b style='color:#000'>💰 TOP 10 CLUBES MAIS VALIOSOS</b>", unsafe_allow_html=True)
        df_money = df_active.groupby('time_nome')['preco_num'].sum().sort_values(ascending=False).head(10).reset_index()
        st.bar_chart(df_money.set_index('time_nome'), color="#000000")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. TOP 5 MITOS (DESIGN RX) ---
    st.markdown("### 🏆 Top 5 Mitos da Última Rodada")
    top5 = df_active.sort_values('pontos_num', ascending=False).head(5)
    cols_top = st.columns(5)

    for i, (idx, p) in enumerate(top5.iterrows()):
        with cols_top[i]:
            st.markdown(f"""
            <div style="background: white; border: 2px solid #000; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 4px 4px 0px #FF6600;">
                <img src="{p['foto'].replace('FORMATO','140x140')}" width="70" style="border-radius: 50%; border: 2px solid #000;">
                <div style="font-size: 12px; font-weight: 900; color: #000; margin-top: 5px; text-transform: uppercase;">{p['apelido']}</div>
                <div style="background: #000; color: #fff; border-radius: 5px; font-size: 14px; font-weight: 900; margin-top: 5px; padding: 2px 0;">{p['pontos_num']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- 4. GRÁFICO ESTILO BOLSA DE VALORES (ÁREA) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="background:white; border:3px solid #000; padding:15px; border-radius:12px; box-shadow: 6px 6px 0px #FF6600; color:#000;">', unsafe_allow_html=True)
    st.markdown("<b style='color:#000'>📈 OSCILAÇÃO DE PERFORMANCE (TOP 20 ATLETAS DA RODADA)</b>", unsafe_allow_html=True)
    
    # Criando um DF com os 20 melhores para o gráfico de área (estilo bolsa)
    df_bolsa = df_active.sort_values('pontos_num', ascending=False).head(20)[['apelido', 'pontos_num']]
    st.area_chart(df_bolsa.set_index('apelido'), color="#FF6600")
    
    st.markdown("<p style='font-size:10px; color:#666; font-weight:bold;'>ESTE GRÁFICO MOSTRA A VOLATILIDADE DE PONTUAÇÃO ENTRE OS MELHORES DA RODADA.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ⚽ MINHAS DICAS (V79.0 - DESIGN SHADOW ARENA) ---
elif menu == "⚽ Minhas Dicas":
    # CSS para padronizar os inputs com a identidade visual
    st.markdown("""
        <style>
            .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stNumberInput div {
                border: 3px solid #000 !important;
                border-radius: 10px !important;
                box-shadow: 4px 4px 0px #FF6600 !important;
            }
            label { color: #000 !important; font-weight: 900 !important; text-transform: uppercase; font-size: 14px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='orange-title'>⚽ Cadastro de Dicas Na Rodada</h1>", unsafe_allow_html=True)
    
    # Formulário Estilizado
    with st.container():
        st.markdown('<div style="background:#f9f9f9; padding:20px; border-radius:15px; border:3px solid #000; margin-bottom:25px;">', unsafe_allow_html=True)
        c_rodada, c_pos = st.columns([1, 2])
        with c_rodada:
            rodada_sel = st.number_input("Rodada Atual:", min_value=1, max_value=38, value=rodada_atual)
        with c_pos:
            pos = st.selectbox("Selecione a Posição para Dica:", ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"])
        
        df_filtrado = df_active[df_active['pos_nome'] == pos].copy()
        
        def get_nome_clube(cid):
            return clubes_raw[str(cid)]['nome'].upper() if str(cid) in clubes_raw else "TIME"

        df_filtrado['label_completo'] = df_filtrado.apply(lambda x: f"{get_nome_clube(x['clube_id'])} | {x['apelido']}", axis=1)
        opcoes_dicas = df_filtrado.sort_values('media_num', ascending=False)['label_completo'].tolist()
        
        selecionados_labels = st.multiselect("Escolha até 5 Gladiadores (Os melhores aparecem primeiro):", options=opcoes_dicas, max_selections=5)
        st.markdown('</div>', unsafe_allow_html=True)

    if selecionados_labels:
        df_comp = df_filtrado[df_filtrado['label_completo'].isin(selecionados_labels)].copy()
        
        # Grid de Cards com Design Shadow (Igual ao RX)
        cols = st.columns(len(selecionados_labels))
        for i, (index, p) in enumerate(df_comp.iterrows()):
            with cols[i]:
                st.markdown(f"""
                <div style="background: white; border: 4px solid #000; border-radius: 15px; padding: 15px; box-shadow: 8px 8px 0px #FF6600; text-align: center; min-height: 380px;">
                    <img src="{p.get('time_escudo', '')}" width="35"><br>
                    <div style="font-size:11px; font-weight:900; color:#000; margin-top:5px;">{get_nome_clube(p['clube_id'])}</div>
                    <img src="{p["foto"].replace("FORMATO","140x140")}" width="100" style="border-radius:50%; border:3px solid #000; margin:10px 0; background:#f0f0f0;">
                    <div style="font-size:18px; font-weight:900; color:#000; text-transform:uppercase; line-height:1.1;">{p['apelido']}</div>
                    <div style="background:#FF6600; color:#000; padding:5px; border-radius:5px; font-weight:900; font-size:16px; margin:10px 0;">C$ {p["preco_num"]}</div>
                    <div style="border-top: 2px solid #eee; pt-10px">
                        <span style="font-size:10px; font-weight:900; color:#666;">MÉDIA</span><br>
                        <span style="font-size:22px; font-weight:900; color:#000;">{p['media_num']:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- BOTÃO DE GRAVAÇÃO COM MENSAGEM ATUALIZADA ---
        if st.button(f"🚀 GRAVAR DICAS DE {pos.upper()} NA RODADA {rodada_sel}"):
            lista_para_enviar = df_comp.to_dict('records')
            
            # 1. Salva no Histórico
            if 'historico_arena' not in st.session_state: st.session_state.historico_arena = {r: {} for r in range(1, 39)}
            st.session_state.historico_arena[rodada_sel][pos] = lista_para_enviar
            
            # 2. Salva no Time Escalado (Onde o Quadro Tático busca)
            if 'time_escalado' not in st.session_state: st.session_state.time_escalado = {}
            st.session_state.time_escalado[pos] = lista_para_enviar
            
            # MENSAGEM CORRIGIDA COM DESIGN SHADOW
            st.markdown(f"""
                <div style="background: #000; color: #fff; padding: 20px; border-radius: 10px; border-left: 10px solid #FF6600; font-weight: 900; font-size: 18px; box-shadow: 5px 5px 15px rgba(0,0,0,0.3);">
                    ✅ SUCESSO! AS DICAS DE {pos.upper()} FORAM ENVIADAS PARA O QUADRO TÁTICO.
                </div>
            """, unsafe_allow_html=True)

# --- 🔍 RAIO-X DO CRAQUE (V95.0 - FOCO NO SIMPLES E CORRETO) ---
elif menu == "🔍 Raio-X do Craque":
    st.markdown("<h1 class='orange-title'>🔍 Raio-X Detalhado do Craque</h1>", unsafe_allow_html=True)

    col_sel, col_stats = st.columns([1, 1])
    
    with col_sel:
        c1, c2 = st.columns(2)
        with c1:
            lista_clubes = sorted([c['nome'] for c in clubes_raw.values()])
            clube_sel = st.selectbox("Filtrar Time:", ["Todos"] + lista_clubes)
        with c2:
            pos_sel = st.selectbox("Filtrar Posição:", ["Todas", "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"])

        df_busca = df_active.copy()
        if clube_sel != "Todos":
            clube_id_sel = next((cid for cid, info in clubes_raw.items() if info['nome'] == clube_sel), None)
            if clube_id_sel: df_busca = df_busca[df_busca['clube_id'] == int(clube_id_sel)]
        if pos_sel != "Todas":
            df_busca = df_busca[df_busca['pos_nome'] == pos_sel]

        lista_atletas = df_busca.sort_values('media_num', ascending=False)['apelido'].tolist()
        
        if not lista_atletas:
            st.warning("⚠️ Nenhum gladiador encontrado.")
            busca_atleta = None
        else:
            busca_atleta = st.selectbox("Escolher Gladiador:", options=lista_atletas)
            atleta = df_busca[df_busca['apelido'] == busca_atleta].iloc[0]
            
            st.markdown("---")
            fundamento = st.selectbox("Analisar Fundamento no Mapa:", ["Geral (Média)", "Gols (G)", "Finalizações (FD/FF)", "Desarmes (DS)", "Assistências (A)"])
            
            # DESIGN SHADOW BONITO (MANTIDO)
            st.markdown(f"""
            <div style="background: white; border: 4px solid #000; border-radius: 15px; padding: 20px; box-shadow: 10px 10px 0px #FF6600; text-align: center;">
                <img src="{atleta['time_escudo']}" width="40"><br>
                <img src="{atleta['foto'].replace("FORMATO","140x140")}" width="130" style="border-radius: 50%; border: 4px solid #000; margin: 15px 0;">
                <div style="font-size: 22px; font-weight: 900; color: #000; text-transform: uppercase;">{atleta['apelido']}</div>
                <div style="background: #FF6600; color: #000; display: inline-block; padding: 2px 12px; border-radius: 5px; font-weight: 900; margin-top: 5px;">{atleta['pos_nome'].upper()}</div>
            </div>""", unsafe_allow_html=True)

    with col_stats:
        if busca_atleta:
            # --- MAPA DE CALOR DINÂMICO ---
            t, l, s, val_scout = 50, 50, 100, 0.0
            if "Gols" in fundamento: t, l, s, val_scout = 50, 85, 130, float(atleta.get('G', 0))
            elif "Finalizações" in fundamento: t, l, s, val_scout = 40, 75, 120, float(atleta.get('FD', 0) + atleta.get('FF', 0))
            elif "Desarmes" in fundamento: l = 22 if atleta['pos_nome'] in ['Zagueiro', 'Goleiro', 'Lateral'] else 40; t, s, val_scout = 60, 110, float(atleta.get('DS', 0))
            elif "Assistências" in fundamento: t, l, s, val_scout = 30, 72, 110, float(atleta.get('A', 0))
            else: l = 80 if atleta['pos_nome'] == 'Atacante' else 50; t, s, val_scout = 50, 100, float(atleta['media_num'] / 2)

            tam = int(s * min(1.8, 1.0 + (val_scout * 0.1)))
            
            # CAMPINHO COM MARCAÇÕES BRANCAS
            heatmap_html = f"""
            <div style="position: relative; width: 100%; height: 210px; background: #2e7d32; border: 3px solid #fff; border-radius: 10px; overflow: hidden; margin-bottom: 12px;">
                <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: rgba(255,255,255,0.4);"></div>
                <div style="position: absolute; left: 50%; top: 50%; width: 55px; height: 55px; border: 2px solid rgba(255,255,255,0.4); border-radius: 50%; transform: translate(-50%, -50%);"></div>
                <div style="position: absolute; left: 0; top: 20%; width: 35px; height: 60%; border: 2px solid rgba(255,255,255,0.4);"></div>
                <div style="position: absolute; right: 0; top: 20%; width: 35px; height: 60%; border: 2px solid rgba(255,255,255,0.4);"></div>
                <div style="position: absolute; top: {t}%; left: {l}%; width: {tam}px; height: {tam}px; background: radial-gradient(circle, rgba(255,0,0,0.8) 0%, transparent 70%); filter: blur(15px); transform: translate(-50%, -50%); transition: all 0.6s;"></div>
            </div>"""
            st.markdown(heatmap_html, unsafe_allow_html=True)

            # --- CARD DE PONTUAÇÃO SIMPLIFICADO ---
            st.markdown(f"""
            <div style="background: #FFFBE6; border: 2px solid #000; border-radius: 8px; padding: 15px; box-shadow: 4px 4px 0px #000;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 5px;">
                    <b style="color:#000;">PONTOS ÚLTIMA RODADA:</b>
                    <b style="background:#FF6600; color:#000; padding: 2px 10px; border-radius:10px; font-size:18px;">{atleta['pontos_num']:.2f}</b>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="color:#000;">MÉDIA GERAL:</b>
                    <b style="background:#444; color:#fff; padding: 2px 10px; border-radius:10px;">{atleta['media_num']:.2f}</b>
                </div>
            </div>""", unsafe_allow_html=True)

            # --- SCOUTS TÉCNICOS ---
            sc_list = ['G', 'A', 'DS', 'FD', 'FS', 'FF', 'I', 'PP', 'DP', 'GS']
            sc_html = "".join([f'<div style="display:flex; justify-content:space-between; border-bottom:1px solid #333; padding:4px 0;"><b>{s}</b> <span style="color:#FF6600;">{int(atleta.get(s,0))}</span></div>' for s in sc_list])
            st.markdown(f'<div style="background:#000; color:#fff; padding:12px; border-radius:10px; margin-top:10px; font-size:12px; border-left: 5px solid #FF6600;"><div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">{sc_html}</div></div>', unsafe_allow_html=True)


# --- 📋 QUADRO TÁTICO (V82.0 - SOMA APENAS TITULARES + DESIGN SHADOW) ---
elif menu == "📋 Quadro Tático":
    st.markdown("<h1 class='orange-title'>🏟️ Quadro Tático Oficial & Reservas</h1>", unsafe_allow_html=True)
    
    # 1. Seleção de Formação
    formacao = st.selectbox("Selecione a Formação:", ["4-4-2", "4-3-3", "3-5-2", "3-4-3", "5-3-2", "5-4-1"])
    
    if st.button("🔄 ATUALIZAR DADOS LIVE"):
        st.session_state.seed_campo += 1

    f_map = {
        "4-4-2": {"Lateral": 2, "Zagueiro": 2, "Meia": 4, "Atacante": 2},
        "4-3-3": {"Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3},
        "3-5-2": {"Lateral": 0, "Zagueiro": 3, "Meia": 5, "Atacante": 2},
        "3-4-3": {"Lateral": 0, "Zagueiro": 3, "Meia": 4, "Atacante": 3},
        "5-3-2": {"Lateral": 2, "Zagueiro": 3, "Meia": 3, "Atacante": 2},
        "5-4-1": {"Lateral": 2, "Zagueiro": 3, "Meia": 4, "Atacante": 1}
    }
    config = f_map[formacao]

    def get_titulares(pos_key, count):
        players = st.session_state.time_escalado.get(pos_key, [])
        if not players: 
            return [{"apelido": "Vazio", "foto": "none", "preco_num": 0, "pontos_live": 0, "scouts_live": {}}] * count
        
        random.seed(st.session_state.seed_campo)
        sampled = random.sample(players, min(len(players), count))
        while len(sampled) < count:
            sampled.append({"apelido": "Vazio", "foto": "none", "preco_num": 0, "pontos_live": 0, "scouts_live": {}})
        return sampled

    # Captura dos Titulares (Final Team)
    gol_t = get_titulares("Goleiro", 1)
    lats_t = get_titulares("Lateral", config["Lateral"])
    zags_t = get_titulares("Zagueiro", config["Zagueiro"])
    meis_t = get_titulares("Meia", config["Meia"])
    atas_t = get_titulares("Atacante", config["Atacante"])
    final_team = {"Goleiro": gol_t, "Lateral": lats_t, "Zagueiro": zags_t, "Meia": meis_t, "Atacante": atas_t}

    # --- CÁLCULO DE PATRIMÓNIO (APENAS JOGADORES NO CAMPO) ---
    valor_titulares = 0
    for pos_list in final_team.values():
        for p in pos_list:
            if p['apelido'] != "Vazio":
                valor_titulares += p.get('preco_num', 0)

    # Card de Valor com o Design Shadow que gostaste
    st.markdown(f"""
        <div style="background: white; border: 3px solid #000; padding: 12px 25px; border-radius: 10px; box-shadow: 6px 6px 0px #FF6600; display: inline-block; margin-bottom: 20px;">
            <span style="color: #000; font-weight: 900; font-size: 14px; text-transform: uppercase;">💰 Custo dos 11 Titulares:</span>
            <span style="color: #FF6600; font-weight: 900; font-size: 22px; margin-left: 10px;">C$ {valor_titulares:.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- BANCO DE RESERVAS ---
    st.markdown("### 📋 Banco de Reservas")
    c1, c2 = st.columns([1, 2])
    with c1:
        lux_pos = st.selectbox("Posição Reserva de Luxo:", [None, "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"], index=0)
        st.session_state.posicao_luxo = lux_pos
        modo_banco = st.radio("Modo:", ["Automático", "Manual"])

    def filter_reserves(pos_name, titulares):
        if not titulares or titulares[0]["apelido"] == "Vazio": return pd.DataFrame()
        precos = [t["preco_num"] for t in titulares if t["apelido"] != "Vazio"]
        if not precos: return pd.DataFrame()
        corte = max(precos) if lux_pos == pos_name else min(precos)
        pos_df = df_active[df_active['pos_nome'] == pos_name]
        return pos_df[pos_df['preco_num'] < corte].sort_values('media_num', ascending=False)

    bench_cols = st.columns(5)
    pos_abrev = {"Goleiro": "GOL", "Lateral": "LAT", "Zagueiro": "ZAG", "Meia": "MEI", "Atacante": "ATA"}

    for i, p_name in enumerate(["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"]):
        if config.get(p_name, 1) == 0 and p_name != "Goleiro": continue
        tit_da_pos = final_team[p_name]
        validos = filter_reserves(p_name, tit_da_pos)
        with bench_cols[i]:
            res_chosen = None
            if modo_banco == "Manual" or lux_pos == p_name:
                if not validos.empty:
                    res_name = st.selectbox(f"{pos_abrev[p_name]}:", ["--"] + validos['apelido'].tolist(), key=f"res_v2_{p_name}")
                    if res_name != "--":
                        res_chosen = validos[validos['apelido'] == res_name].iloc[0].to_dict()
            elif modo_banco == "Automático" and not validos.empty:
                res_chosen = validos.iloc[0].to_dict()

            if res_chosen:
                st.markdown(f'''<div class="bench-card-v2"><img src="{res_chosen.get("time_escudo", "")}" style="width:25px;"><div style="font-size:10px; color:#FF6600; font-weight:bold;">{res_chosen["apelido"]}</div><div class="bench-pos-v2">{pos_abrev[p_name]}</div></div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="bench-card-v2"><div class="bench-plus-v2">+</div><div class="bench-pos-v2">{pos_abrev[p_name]}</div></div>''', unsafe_allow_html=True)

    # --- DESENHO DO CAMPO (CAMPINHO) ---
    def draw_player(p, top, left):
        foto = p["foto"].replace("FORMATO","140x140") if p.get("foto") and p["foto"] != "none" else ""
        if foto:
            pts = p.get('pontos_live', 0)
            return f'''<div class="player-spot" style="top:{top}%; left:{left}%;">
                <div class="live-pts">{pts:.1f}</div>
                <img src="{foto}" class="player-photo-field">
                <span class="player-name-tag">{p["apelido"]}</span>
            </div>'''
        return f'<div class="player-spot" style="top:{top}%; left:{left}%;"><div class="player-photo-field" style="opacity:0.2; background:#222;"></div><span class="player-name-tag" style="color:#666;">VAZIO</span></div>'

    html_field = f'<div class="center-line"></div><div class="center-circle"></div><div class="penalty-area-left"></div><div class="small-area-left"></div><div class="arc-left"></div><div class="penalty-area-right"></div><div class="small-area-right"></div><div class="arc-right"></div>'
    
    html_field += draw_player(final_team["Goleiro"][0], 50, 8)
    z = final_team["Zagueiro"]
    if config["Zagueiro"] == 2: html_field += draw_player(z[0], 40, 25) + draw_player(z[1], 60, 25)
    else: html_field += draw_player(z[0], 30, 22) + draw_player(z[1], 50, 22) + draw_player(z[2], 70, 22)
    if config["Lateral"] == 2:
        l = final_team["Lateral"]
        html_field += draw_player(l[0], 15, 28) + draw_player(l[1], 85, 28)
    m = final_team["Meia"]
    if config["Meia"] == 3: html_field += draw_player(m[0], 30, 50) + draw_player(m[1], 50, 45) + draw_player(m[2], 70, 50)
    elif config["Meia"] == 4: html_field += draw_player(m[0], 25, 48) + draw_player(m[1], 42, 45) + draw_player(m[2], 58, 45) + draw_player(m[3], 75, 48)
    elif config["Meia"] == 5: html_field += draw_player(m[0], 20, 52) + draw_player(m[1], 35, 46) + draw_player(m[2], 50, 42) + draw_player(m[3], 65, 46) + draw_player(m[4], 80, 52)
    a = final_team["Atacante"]
    if config["Atacante"] == 1: html_field += draw_player(a[0], 50, 88)
    elif config["Atacante"] == 2: html_field += draw_player(a[0], 35, 84) + draw_player(a[1], 65, 84)
    elif config["Atacante"] == 3: html_field += draw_player(a[0], 25, 82) + draw_player(a[1], 50, 88) + draw_player(a[2], 75, 82)

    st.markdown(f'<div class="field-container">{html_field}</div>', unsafe_allow_html=True)



# --- 📊 CENTRAL PROBABILIDADES (V130.0 - CONEXÃO REAL COM ENDPOINT PARTIDAS) ---
elif menu == "📊 Central Probabilidades":
    st.markdown("<h1 class='orange-title'>📊 Central de Probabilidades Profissional</h1>", unsafe_allow_html=True)
    
    # MANTENDO O DESIGN SHADOW INTEGRAL
    st.markdown("""
        <style>
            .prob-bar-bg { background: #eee; border-radius: 10px; height: 12px; width: 100%; margin-top: 5px; border: 1px solid #000; overflow: hidden; }
            .prob-bar-fill { background: linear-gradient(90deg, #FF6600, #ff8c00); height: 100%; border-radius: 10px; }
            .prob-card-shadow { background: white; border: 3px solid #000; padding: 15px; margin-bottom: 12px; border-radius: 12px; box-shadow: 5px 5px 0px #FF6600; }
        </style>
    """, unsafe_allow_html=True)

    # 1. BUSCAR PARTIDAS DA RODADA ATUAL DIRETO NA API
    @st.cache_data(ttl=3600)
    def buscar_mandantes_api():
        try:
            r = requests.get("https://api.cartola.globo.com/partidas")
            dados_partidas = r.json()
            # Pega todos os IDs dos clubes que jogam em casa nesta rodada
            return [jogo['clube_casa_id'] for jogo in dados_partidas['partidas']]
        except:
            return []

    mandantes_ids = buscar_mandantes_api()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🛡️ Favoritos para Saldo de Gol (SG)")
        
        # Filtramos o DataFrame de atletas usando os IDs de mandantes vindos da API de partidas
        df_mandantes = df_active[df_active['clube_id'].isin(mandantes_ids)]
        
        df_sg = df_mandantes.groupby('time_nome').agg({
            'media_num': 'mean',
            'time_escudo': 'first',
            'clube_id': 'first'
        }).reset_index()

        if not df_sg.empty:
            # Algoritmo de Probabilidade Arena (Base 80% para mandantes da rodada)
            df_sg['prob'] = df_sg['media_num'].apply(lambda x: min(99, 82 + (x * 1.8) + random.uniform(1, 4)))
            
            for _, r in df_sg.nlargest(6, 'prob').iterrows():
                st.markdown(f"""
                <div class="prob-card-shadow">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:900; color:#000;"><img src="{r['time_escudo']}" width="25" style="margin-right:8px;">{r['time_nome']}</span>
                        <b style="color:#FF6600; font-size:18px;">{int(r['prob'])}%</b>
                    </div>
                    <div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{r['prob']}%"></div></div>
                    <div style="font-size:10px; font-weight:bold; color:#2e7d32; margin-top:5px;">✓ MANDANTE IDENTIFICADO (API)</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.error("Conectando à API de Partidas... Verifique a conexão.")

    with c2:
        st.markdown("### ⚽ Caçadores de Gols (Prob. de Gol)")
        
        # Atacantes e Meias dos times que a API de partidas confirmou como Mandantes
        df_atacantes_casa = df_active[
            (df_active['pos_nome'].isin(['Atacante', 'Meia'])) & 
            (df_active['clube_id'].isin(mandantes_ids))
        ].copy()
        
        if not df_atacantes_casa.empty:
            # Algoritmo de Probabilidade Arena para Gols
            df_atacantes_casa['prob'] = df_atacantes_casa['media_num'].apply(lambda x: min(96, 78 + (x * 2.5) + random.uniform(1, 5)))
            
            for _, r in df_atacantes_casa.nlargest(6, 'prob').iterrows():
                st.markdown(f"""
                <div class="prob-card-shadow">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:900; color:#000;"><img src="{r['time_escudo']}" width="20" style="margin-right:8px;">{r['apelido']}</span>
                        <b style="color:#000; font-size:18px;">{int(r['prob'])}%</b>
                    </div>
                    <div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{r['prob']}%;"></div></div>
                    <div style="font-size:10px; font-weight:bold; color:#FF6600; margin-top:5px;">🔥 FORÇA OFENSIVA EM CASA</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.warning("Aguardando sincronização de atletas...")

    st.info("📊 Dados processados via cruzamento dinâmico entre /atletas e /partidas.")

# --- 🧠 RADAR DE CAPITÃO (V82.0 - ALGORITMO DE ELITE & DESIGN SHADOW) ---
elif menu == "🧠 Radar de Capitão":
    st.markdown("<h1 class='orange-title'>🧠 Radar de Capitão Elite</h1>", unsafe_allow_html=True)

    # --- LÓGICA DO ALGORITMO AVANÇADO ---
    def calcular_potencial_capitao(row):
        # Base: Média + Última Pontuação
        score = (row['media_num'] * 0.6) + (row['pontos_num'] * 0.4)
        
        # Bônus por Posição (Preferência Atacante)
        if row['pos_nome'] == 'Atacante': score *= 1.2 
        elif row['pos_nome'] == 'Meia': score *= 1.0
        
        # Bônus por Scouts Decisivos (Gols e Assistências)
        gols = row.get('G', 0)
        assists = row.get('A', 0)
        score += (gols * 2) + (assists * 1.5)
        
        return score

    # Criar DataFrame de Candidatos (Meias e Atacantes)
    df_caps = df_active[df_active['pos_nome'].isin(['Meia', 'Atacante'])].copy()
    df_caps['score_elite'] = df_caps.apply(calcular_potencial_capitao, axis=1)

    # Separar Mandantes e Visitantes
    # Aqui filtramos usando a lista de partidas para saber quem joga em casa
    mandantes_ids = [j['clube_casa_id'] for j in partidas]
    
    df_mandantes = df_caps[df_caps['clube_id'].isin(mandantes_ids)].sort_values('score_elite', ascending=False).head(4)
    df_visitantes = df_caps[~df_caps['clube_id'].isin(mandantes_ids)].sort_values('score_elite', ascending=False).head(2)

    # Unir para exibição (4 em casa, 2 fora)
    caps_finais = pd.concat([df_mandantes, df_visitantes])

    # --- INTERFACE VISUAL (ESTILO ANÁLISE DE CONFRONTOS) ---
    cols = st.columns(3)
    for i, (_, row) in enumerate(caps_finais.iterrows()):
        # Identificar se é Mandante ou Visitante para o selo
        tipo_mando = "MANDANTE" if row['clube_id'] in mandantes_ids else "VISITANTE"
        cor_mando = "#FF6600" if tipo_mando == "MANDANTE" else "#555"
        
        card_html = f"""
        <div style="background-color: white; border: 4px solid #000; border-radius: 15px; padding: 15px; font-family: 'Arial Black', sans-serif; box-shadow: 8px 8px 0px #FF6600; margin-bottom: 25px; text-align: center;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="background: #000; color: #FF6600; padding: 2px 10px; border-radius: 5px; font-size: 10px; font-weight: 900;">{tipo_mando}</div>
                <div style="background: #FF6600; color: #000; width: 25px; height: 25px; border-radius: 50%; font-weight: 900; line-height: 25px; border: 2px solid #000;">C</div>
            </div>
            
            <img src="{row['time_escudo']}" width="35" style="margin-top: 10px;">
            <br>
            <img src="{row['foto'].replace("FORMATO","140x140")}" width="110" style="border-radius: 50%; border: 3px solid #000; margin: 10px 0; background: #f0f0f0;">
            
            <div style="font-size: 18px; color: #000; font-weight: 900; text-transform: uppercase; min-height: 50px;">{row['apelido']}</div>
            
            <div style="background: #000; color: #fff; padding: 5px; border-radius: 8px; margin-top: 10px;">
                <div style="font-size: 9px; color: #FF6600;">PROBABILIDADE DE MITADA</div>
                <div style="font-size: 20px; font-weight: 900;">{min(99.9, row['score_elite'] * 5):.1f}%</div>
            </div>
            
            <div style="display: flex; justify-content: space-around; margin-top: 10px; font-size: 12px; font-weight: bold; color: #000;">
                <div>MÉDIA<br>{row['media_num']:.2f}</div>
                <div style="border-left: 1px solid #ddd;"></div>
                <div>PREÇO<br>C$ {row['preco_num']}</div>
            </div>
        </div>
        """
        with cols[i % 3]:
            components.html(card_html, height=450)

# --- 🔥 TERMÔMETRO INTELIGENTE INTEGRADO (V56.1) ---
elif menu == "🔥 Termômetro":
    st.markdown("<h1 class='orange-title'>🔥 Termômetro de Momento Inteligente</h1>", unsafe_allow_html=True)
    
    df_quentes = df_active[df_active['tendencia'] > 0].sort_values('tendencia', ascending=False).drop_duplicates(subset=['atleta_id']).head(8)
    fonte_dados = "🚀 Momento Live"

    if df_quentes.empty:
        df_quentes = df_active.sort_values(['media_num', 'media_basica'], ascending=False).head(8)
        fonte_dados = "📊 Performance Histórica"
    
    df_frios = df_active[~df_active['atleta_id'].isin(df_quentes['atleta_id'].tolist())].sort_values(['tendencia', 'media_num'], ascending=True).head(8)

    st.caption(f"Fonte de análise atual: **{fonte_dados}**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Em Ascensão")
        for _, r in df_quentes.iterrows():
            val_ref = r['tendencia'] if r['tendencia'] > 0 else r['media_num']
            perc_progresso = min(int((val_ref / 10) * 100), 100)
            pulse_class = "card-pulse" if val_ref >= 8.0 else ""
            
            ponto_corte = r['preco_num'] * 0.33
            selo_ouro = ""
            if r['pontos_num'] >= ponto_corte and val_ref >= 7.0:
                selo_ouro = '<div style="background:#28a745; color:white; font-size:9px; font-weight:bold; padding:2px 6px; border-radius:10px; width:fit-content; margin-bottom:5px;">💰 OPORTUNIDADE DE OURO</div>'
            
            st.markdown(f"""
                <div class="val-card-v2 {pulse_class}" style="border-left-color: #ff4b4b; background: #FFF8F8;">
                    {selo_ouro}
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><img src="{r['time_escudo']}" width="20"> <b>{r['apelido']}</b></span>
                        <span style="color:#ff4b4b; font-weight:800;">{val_ref:.1f}</span>
                    </div>
                    <div class="prob-bar-bg" style="margin-bottom: 8px;">
                        <div class="prob-bar-fill" style="width:{perc_progresso}%; background:#ff4b4b;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#555;">
                        <span>Média Bas. (Casa): <b>{r['media_basica']:.1f}</b></span>
                        <span>Posição: <b>{r['pos_nome']}</b></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.subheader("❄️ Em Queda")
        for _, r in df_frios.iterrows():
            perc_progresso_frio = min(int((r['media_num'] / 10) * 100), 100)
            st.markdown(f"""
                <div class="val-card-v2" style="border-left-color: #1f77b4; background: #F8FBFF;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><img src="{r['time_escudo']}" width="20"> <b>{r['apelido']}</b></span>
                        <span style="color:#1f77b4; font-weight:800;">{r['media_num']:.1f}</span>
                    </div>
                    <div class="prob-bar-bg" style="margin-bottom: 8px;">
                        <div class="prob-bar-fill" style="width:{perc_progresso_frio}%; background:#1f77b4;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#555;">
                        <span>Média Bas. (Casa): <b>{r['media_basica']:.1f}</b></span>
                        <span>Posição: <b>{r['pos_nome']}</b></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    if not df_quentes.empty:
        top_elite = df_quentes.iloc[0]
        val_top = top_elite['tendencia'] if top_elite['tendencia'] > 0 else top_elite['media_num']
        if val_top >= 8.0:
            st.toast(f"MONSTRO DETECTADO: {top_elite['apelido']} atingiu nível Elite ({val_top:.1f})!", icon="🔥")


# --- 💰 SIMULADOR DE VALORIZAÇÃO ---
elif menu == "💰 Simulador de Valorização":
    st.markdown("<h1 class='orange-title'>💰 Simulador de Valorização Inteligente</h1>", unsafe_allow_html=True)
    
    @st.cache_data(ttl=3600)
    def buscar_mandantes_reais():
        try:
            url = "https://api.cartola.globo.com/partidas"
            r = requests.get(url, timeout=5).json()
            return {jogo['clube_casa_id'] for jogo in r['partidas']}
        except Exception as e:
            return set(df_active[df_active['is_mandante'] == 1]['clube_id'].unique())

    mandantes_ids_oficiais = buscar_mandantes_reais()
    df_val = df_active.copy()
    df_val['is_mandante_real'] = df_val['clube_id'].apply(lambda x: 1 if x in mandantes_ids_oficiais else 0)
    df_val['ponto_corte'] = (df_val['preco_num'] * 0.33).round(1)
    df_base = df_val[(df_val['ponto_corte'] >= 0) & (df_val['ponto_corte'] <= 3.5)].copy()
    df_base['score_val'] = (df_base['media_basica'] * 0.7) + (df_base['media_num'] * 0.3)

    st.markdown("### 🏆 Top 6 Geral de Valorização")
    m_geral = df_base[df_base['is_mandante_real'] == 1].nlargest(4, 'score_val')
    v_geral = df_base[df_base['is_mandante_real'] == 0].nlargest(2, 'score_val')
    geral_6 = pd.concat([m_geral, v_geral])

    if not geral_6.empty:
        cols_geral = st.columns(3)
        for idx, (_, r) in enumerate(geral_6.iterrows()):
            t_local = "🏠 CASA" if r['is_mandante_real'] == 1 else "🚌 FORA"
            c_local = "blue" if r['is_mandante_real'] == 1 else "#FF8C00"
            with cols_geral[idx % 3]:
                st.markdown(f"""
                    <div style="background: #FFF3E0; border: 2px solid #FF6600; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                        <img src="{r['time_escudo']}" width="30"><br>
                        <b style="font-size: 14px; color: black;">{r['apelido']}</b><br>
                        <small style="color:#555;">{r['pos_nome']} | <b style="color:{c_local};">{t_local}</b></small>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("### 🔍 Melhores Opções por Setor (4 Casa + 2 Fora)")
    abas_setor = st.tabs(["🧤 Goleiros", "🛡️ Laterais", "🧱 Zagueiros", "🪄 Meias", "🏹 Atacantes"])
    pos_lista = ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"]

    for i, aba in enumerate(abas_setor):
        with aba:
            p_atual = pos_lista[i]
            df_pos = df_base[df_base['pos_nome'] == p_atual]
            mands_p = df_pos[df_pos['is_mandante_real'] == 1].nlargest(4, 'score_val')
            visitas_p = df_pos[df_pos['is_mandante_real'] == 0].nlargest(2, 'score_val')
            top_pos_6 = pd.concat([mands_p, visitas_p])
            
            if top_pos_6.empty:
                st.info(f"Nenhum {p_atual} atende aos critérios nesta rodada.")
            else:
                for n in range(0, len(top_pos_6), 3):
                    cols = st.columns(3)
                    for m, (_, row) in enumerate(top_pos_6.iloc[n:n+3].iterrows()):
                        l_txt = "CASA" if row['is_mandante_real'] == 1 else "FORA"
                        l_ico = "🏠" if row['is_mandante_real'] == 1 else "🚌"
                        l_cor = "blue" if row['is_mandante_real'] == 1 else "#FF8C00"
                        
                        with cols[m]:
                            st.markdown(f"""
                                <div style="border-left: 5px solid {l_cor}; background: white; padding: 12px; border-radius: 10px; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="font-size:12px; color: black;">
                                            <img src="{row['time_escudo']}" width="18"> <b>{row['apelido']}</b>
                                        </span>
                                        <b style="color:#28a745; font-size:11px;">C$ {row['preco_num']}</b>
                                    </div>
                                    <hr style="margin: 8px 0; border:0; border-top: 1px solid #eee;">
                                    <div style="font-size:10px; color:#444;">
                                        🎯 Corte: <b style="color:black;">{row['ponto_corte']} pts</b><br>
                                        📍 Local: <b style="color:{l_cor};">{l_ico} {l_txt}</b>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
    st.markdown("---")


# --- 🏟️ ANÁLISE DE CONFRONTOS (V130.0 - CEDÊNCIA REAL POR SETOR) ---
elif menu == "🏟️ Análise de Confrontos":
    st.markdown("<h1 class='orange-title' style='font-size: 32px;'>🏟️ Matriz de Confrontos & Cedentes</h1>", unsafe_allow_html=True)

    # ============================================================
    # FUNÇÕES SEGURAS
    # ============================================================
    def safe_sum(dataframe, col):
        if col in dataframe.columns and not dataframe.empty:
            return float(dataframe[col].fillna(0).sum())
        return 0.0

    def safe_mean(dataframe, col):
        if col in dataframe.columns and not dataframe.empty:
            val = dataframe[col].fillna(0).mean()
            return float(val) if not pd.isna(val) else 0.0
        return 0.0

    def safe_count_above(dataframe, col, threshold=0):
        if col in dataframe.columns and not dataframe.empty:
            return int((dataframe[col].fillna(0) > threshold).sum())
        return 0

    # ============================================================
    # CONQUISTA: O que MEU TIME produz naquela posição
    # (Depende apenas dos jogadores do MEU time naquela posição)
    # ============================================================
    def calcular_conquista(df_time, posicao, scout_key, scout_nome):
        df_pos = df_time[df_time['pos_nome'] == posicao]
        if df_pos.empty:
            return 0.0

        if scout_nome == "Saldo de Gols (SG)":
            if posicao in ['Goleiro', 'Zagueiro', 'Lateral']:
                sg = safe_sum(df_pos, 'SG')
                dd = safe_sum(df_pos, 'DD') if posicao == 'Goleiro' else 0
                ds = safe_sum(df_pos, 'DS') if posicao != 'Goleiro' else 0
                return sg * 4 + dd * 0.5 + ds * 0.3
            else:
                return safe_sum(df_pos, 'G') * 3

        elif scout_nome == "Defesa":
            if posicao == 'Goleiro':
                return safe_sum(df_pos, 'DD') * 2 + safe_sum(df_pos, 'DP') * 3 + safe_sum(df_pos, 'SG') * 5
            elif posicao in ['Zagueiro', 'Lateral']:
                return safe_sum(df_pos, 'DS') * 2.5 + safe_sum(df_pos, 'SG') * 3
            else:
                return safe_sum(df_pos, 'DS') * 0.5

        elif scout_key == 'G':
            gols = safe_sum(df_pos, 'G')
            fd = safe_sum(df_pos, 'FD')
            ft = safe_sum(df_pos, 'FT')
            return gols * 4 + fd * 0.8 + ft * 0.3

        elif scout_key == 'A':
            assists = safe_sum(df_pos, 'A')
            return assists * 4 + safe_mean(df_pos, 'media_num') * 0.5

        elif scout_key == 'DS':
            return safe_sum(df_pos, 'DS') * 2.5

        else:
            return safe_mean(df_pos, 'pontos_num') * 2

    # ============================================================
    # CEDÊNCIA: O que o ADVERSÁRIO permite para aquela posição
    #
    # *** AQUI ESTÁ A CORREÇÃO PRINCIPAL ***
    #
    # Cada posição do meu time se beneficia de SETORES DIFERENTES
    # do adversário. Então filtramos o DF do adversário por setor
    # específico que é responsável pela fragilidade.
    # ============================================================
    def calcular_cedencia(df_adversario, posicao_beneficiada, scout_key, scout_nome):
        if df_adversario.empty:
            return 0.0

        # Separar o adversário por setores (cada um cede coisas diferentes)
        adv_gol = df_adversario[df_adversario['pos_nome'] == 'Goleiro']
        adv_zag = df_adversario[df_adversario['pos_nome'] == 'Zagueiro']
        adv_lat = df_adversario[df_adversario['pos_nome'] == 'Lateral']
        adv_mei = df_adversario[df_adversario['pos_nome'] == 'Meia']
        adv_ata = df_adversario[df_adversario['pos_nome'] == 'Atacante']
        adv_def = df_adversario[df_adversario['pos_nome'].isin(['Goleiro', 'Zagueiro', 'Lateral'])]
        adv_ofe = df_adversario[df_adversario['pos_nome'].isin(['Atacante', 'Meia'])]

        # -------------------------------------------------------
        # GOLS (G): Quem do adversário CEDE gols?
        # -------------------------------------------------------
        if scout_key == 'G':
            if posicao_beneficiada == 'Atacante':
                # Atacante faz gol contra: Goleiro (GS) + Zagueiros fracos (poucos DS)
                gs = safe_mean(adv_gol, 'GS')
                ds_zag = safe_mean(adv_zag, 'DS')
                fc_def = safe_sum(adv_def, 'FC')
                # Mais GS + Menos DS dos zagueiros + Mais faltas = mais cedência
                return gs * 5 + max(0, (4 - ds_zag)) * 2 + fc_def * 0.2

            elif posicao_beneficiada == 'Meia':
                # Meia faz gol contra: Meio-campo adversário (perdem bola, PI alto)
                gs = safe_mean(adv_gol, 'GS')
                ds_mei = safe_mean(adv_mei, 'DS')
                pi_mei = safe_sum(adv_mei, 'PI') if 'PI' in adv_mei.columns else 0
                return gs * 3 + max(0, (3 - ds_mei)) * 2.5 + pi_mei * 0.3

            elif posicao_beneficiada == 'Zagueiro':
                # Zagueiro faz gol de bola parada: Adversário comete muitas faltas (FC)
                fc_adv = safe_sum(df_adversario, 'FC')
                gs = safe_mean(adv_gol, 'GS')
                return fc_adv * 0.5 + gs * 2

            elif posicao_beneficiada == 'Lateral':
                # Lateral faz gol: Laterais adversários não marcam (poucos DS)
                ds_lat_adv = safe_mean(adv_lat, 'DS')
                gs = safe_mean(adv_gol, 'GS')
                return gs * 2.5 + max(0, (3 - ds_lat_adv)) * 2

            else:  # Goleiro (raro mas existe)
                return safe_mean(adv_gol, 'GS') * 0.5

        # -------------------------------------------------------
        # ASSISTÊNCIAS (A): Quem do adversário CEDE assistências?
        # -------------------------------------------------------
        elif scout_key == 'A':
            if posicao_beneficiada == 'Meia':
                # Meia assiste contra: Defesa adversária fraca (zagueiros com poucos DS)
                ds_zag = safe_mean(adv_zag, 'DS')
                ds_lat = safe_mean(adv_lat, 'DS')
                gs = safe_mean(adv_gol, 'GS')
                return gs * 3.5 + max(0, (4 - ds_zag)) * 2 + max(0, (3 - ds_lat)) * 1

            elif posicao_beneficiada == 'Atacante':
                # Atacante assiste contra: Laterais adversários fora de posição
                ds_lat = safe_mean(adv_lat, 'DS')
                gs = safe_mean(adv_gol, 'GS')
                return gs * 2.5 + max(0, (3 - ds_lat)) * 2.5

            elif posicao_beneficiada == 'Lateral':
                # Lateral cruza/assiste contra: Zagueiros adversários lentos
                ds_zag = safe_mean(adv_zag, 'DS')
                gs = safe_mean(adv_gol, 'GS')
                return gs * 3 + max(0, (4 - ds_zag)) * 2.5

            elif posicao_beneficiada == 'Zagueiro':
                # Zagueiro assiste em bola parada
                fc_adv = safe_sum(df_adversario, 'FC')
                return fc_adv * 0.4 + safe_mean(adv_gol, 'GS') * 1.5

            else:
                return safe_mean(adv_gol, 'GS') * 0.5

        # -------------------------------------------------------
        # DESARMES (DS): Quem do adversário CEDE desarmes?
        # -------------------------------------------------------
        elif scout_key == 'DS':
            if posicao_beneficiada == 'Zagueiro':
                # Zagueiro desarma: Atacantes adversários (tentam driblar, finalizar)
                fd_ata = safe_sum(adv_ata, 'FD') + safe_sum(adv_ata, 'FT')
                ff_ata = safe_sum(adv_ata, 'FF')
                pi_ata = safe_sum(adv_ata, 'PI') if 'PI' in adv_ata.columns else 0
                return fd_ata * 0.8 + ff_ata * 0.5 + pi_ata * 0.6

            elif posicao_beneficiada == 'Lateral':
                # Lateral desarma: Meias e pontas adversários
                fd_mei = safe_sum(adv_mei, 'FD') + safe_sum(adv_mei, 'FT')
                pi_mei = safe_sum(adv_mei, 'PI') if 'PI' in adv_mei.columns else 0
                fd_ata = safe_sum(adv_ata, 'FD') * 0.3
                return fd_mei * 0.7 + pi_mei * 0.5 + fd_ata

            elif posicao_beneficiada == 'Meia':
                # Meia desarma: Meias adversários (disputa no meio)
                pi_mei = safe_sum(adv_mei, 'PI') if 'PI' in adv_mei.columns else 0
                fc_mei = safe_sum(adv_mei, 'FC')
                fd_mei = safe_sum(adv_mei, 'FD')
                return pi_mei * 0.8 + fc_mei * 0.4 + fd_mei * 0.3

            elif posicao_beneficiada == 'Goleiro':
                # Goleiro raramente desarma
                return safe_sum(adv_ofe, 'FD') * 0.1

            else:  # Atacante
                # Atacante desarma na frente: pressão alta contra zagueiros
                pi_zag = safe_sum(adv_zag, 'PI') if 'PI' in adv_zag.columns else 0
                pi_gol = safe_sum(adv_gol, 'PI') if 'PI' in adv_gol.columns else 0
                return pi_zag * 0.6 + pi_gol * 0.3

        # -------------------------------------------------------
        # SALDO DE GOLS (SG): Quem do adversário CEDE SG?
        # -------------------------------------------------------
        elif scout_nome == "Saldo de Gols (SG)":
            if posicao_beneficiada in ['Goleiro', 'Zagueiro', 'Lateral']:
                # Defensores ganham SG quando adversário NÃO ataca
                # Atacantes adversários fracos = cedem SG
                g_ata = safe_sum(adv_ata, 'G')
                g_mei = safe_sum(adv_mei, 'G')
                fd_total = safe_sum(adv_ofe, 'FD') + safe_sum(adv_ofe, 'FT')

                # INVERSÃO: quanto MENOS o ataque adversário produz, MAIS cede SG
                ataque_poder = g_ata * 5 + g_mei * 3 + fd_total * 0.3
                cedencia_sg = max(0, 25 - ataque_poder)

                # Diferenciação por posição defensiva
                if posicao_beneficiada == 'Goleiro':
                    return cedencia_sg * 1.3  # Goleiro é mais impactado
                elif posicao_beneficiada == 'Zagueiro':
                    return cedencia_sg * 1.1
                else:  # Lateral
                    return cedencia_sg * 0.9
            else:
                # Ofensivos não ganham SG diretamente
                return 0.0

        # -------------------------------------------------------
        # DEFESA: Quem do adversário CEDE scouts defensivos?
        # -------------------------------------------------------
        elif scout_nome == "Defesa":
            if posicao_beneficiada == 'Goleiro':
                # Goleiro defende contra: Atacantes que finalizam MUITO
                fd_ata = safe_sum(adv_ata, 'FD') + safe_sum(adv_ata, 'FT')
                fd_mei = safe_sum(adv_mei, 'FD') + safe_sum(adv_mei, 'FT')
                return fd_ata * 1.2 + fd_mei * 0.5

            elif posicao_beneficiada == 'Zagueiro':
                # Zagueiro defende contra: Atacantes que tentam driblar
                fd_ata = safe_sum(adv_ata, 'FD')
                ff_ata = safe_sum(adv_ata, 'FF')
                return fd_ata * 0.8 + ff_ata * 0.6

            elif posicao_beneficiada == 'Lateral':
                # Lateral defende contra: Meias/pontas que atacam pelo lado
                fd_mei = safe_sum(adv_mei, 'FD')
                pi_ofe = safe_sum(adv_ofe, 'PI') if 'PI' in adv_ofe.columns else 0
                return fd_mei * 0.7 + pi_ofe * 0.4

            else:
                return safe_sum(adv_ofe, 'PI') * 0.2 if 'PI' in adv_ofe.columns else 0.0

        # -------------------------------------------------------
        # PONTOS GERAIS: Cedência genérica diferenciada
        # -------------------------------------------------------
        else:
            if posicao_beneficiada == 'Atacante':
                gs = safe_mean(adv_gol, 'GS')
                ds_def = safe_mean(adv_def, 'DS')
                return gs * 4 + max(0, (4 - ds_def)) * 2

            elif posicao_beneficiada == 'Meia':
                pi_mei = safe_sum(adv_mei, 'PI') if 'PI' in adv_mei.columns else 0
                gs = safe_mean(adv_gol, 'GS')
                ds_mei = safe_mean(adv_mei, 'DS')
                return gs * 2 + pi_mei * 0.5 + max(0, (3 - ds_mei)) * 1.5

            elif posicao_beneficiada == 'Goleiro':
                fd_ofe = safe_sum(adv_ofe, 'FD') + safe_sum(adv_ofe, 'FT')
                g_ofe = safe_sum(adv_ofe, 'G')
                # Inversão parcial: goleiro pontua com defesas, mas perde com gols sofridos
                return fd_ofe * 0.8 + max(0, (15 - g_ofe * 3))

            elif posicao_beneficiada == 'Zagueiro':
                g_ata = safe_sum(adv_ata, 'G')
                fd_ata = safe_sum(adv_ata, 'FD')
                return max(0, (15 - g_ata * 4)) + fd_ata * 0.3

            elif posicao_beneficiada == 'Lateral':
                ds_lat = safe_mean(adv_lat, 'DS')
                fd_mei = safe_sum(adv_mei, 'FD')
                return max(0, (3 - ds_lat)) * 2 + fd_mei * 0.3

            else:
                return safe_mean(df_adversario, 'pontos_num')

    # ============================================================
    # ÍNDICE DE OPORTUNIDADE
    # ============================================================
    def calcular_indice(conquista, cedencia, is_mandante=False):
        bonus = 1.12 if is_mandante else 0.95
        return round(((conquista * 0.55) + (cedencia * 0.45)) * bonus, 2)

    # ============================================================
    # CONFIANÇA
    # ============================================================
    def calcular_confianca(df_t, df_a):
        n = len(df_t) + len(df_a)
        scouts_ok = sum(1 for c in ['G','A','DS','FD','GS','SG','FC','DD','PI','FT','FF'] if c in df_t.columns)
        dados_reais = len(df_t[df_t['pontos_num'] > 0]) + len(df_a[df_a['pontos_num'] > 0])
        return min(100, int(min(50, n * 1.2) + min(30, scouts_ok * 2.7) + min(20, dados_reais * 1.5)))

    # ============================================================
    # TOP TARGETS CRUZANDO FORÇA × FRAGILIDADE REAL
    # ============================================================
    def get_top_targets(clube_id, df_adversario, scout_key, scout_nome):
        df_cl = df_active[df_active['clube_id'] == clube_id].copy()
        if df_cl.empty:
            return "<p style='color:#888;'>Sem dados</p>"

        if scout_nome in ["Defesa", "Saldo de Gols (SG)"]:
            df_cl = df_cl[df_cl['pos_nome'].isin(['Goleiro', 'Zagueiro', 'Lateral'])]
        elif scout_key == 'G':
            df_cl = df_cl[df_cl['pos_nome'].isin(['Atacante', 'Meia'])]
        elif scout_key == 'A':
            df_cl = df_cl[df_cl['pos_nome'].isin(['Meia', 'Atacante', 'Lateral'])]

        if df_cl.empty:
            return "<p style='color:#888;'>Sem jogadores</p>"

        def score_alvo(row):
            pos = row['pos_nome']
            conq = calcular_conquista(
                df_cl[df_cl['atleta_id'] == row['atleta_id']], pos, scout_key, scout_nome
            )
            ced = calcular_cedencia(df_adversario, pos, scout_key, scout_nome)
            return conq * 0.6 + ced * 0.4

        df_cl['score_alvo'] = df_cl.apply(score_alvo, axis=1)
        top = df_cl.nlargest(3, 'score_alvo')

        medalhas = ["🥇", "🥈", "🥉"]
        html = ""
        for rank, (_, p) in enumerate(top.iterrows()):
            f_url = str(p['foto']).replace('FORMATO', '140x140')
            ced_val = calcular_cedencia(df_adversario, p['pos_nome'], scout_key, scout_nome)
            html += f"""
            <div style="display:flex; align-items:center; background:#000; color:#fff; 
                        padding:10px 15px; border-radius:20px; border:2px solid #FF6600; 
                        margin:6px; width:95%; position:relative;">
                <div style="position:absolute; top:-8px; left:-5px; font-size:16px;">{medalhas[rank]}</div>
                <img src="{f_url}" width="40" style="border-radius:50%; border:2px solid #FF6600; margin-right:12px;">
                <div style="flex:1; font-size:12px; line-height:1.3;">
                    <b style="font-size:14px;">{p['apelido']}</b><br>
                    <span style="color:#FF6600; font-weight:bold;">{p['pos_nome']}</span>
                    <span style="color:#aaa;"> | Rival cede: {ced_val:.1f}</span>
                </div>
            </div>"""
        return html

    # ============================================================
    # INTERFACE - FILTROS
    # ============================================================
    c_filt1, c_filt2, c_filt3 = st.columns([1.5, 2, 2])
    with c_filt1:
        qtd_jogos = st.select_slider("Tendência (Rodadas):", options=[1,2,3,4,5], value=1)
    with c_filt2:
        scout_foco = st.selectbox("Scout para Analisar:",
            ["Pontos", "Desarmes (DS)", "Gols (G)", "Assistências (A)", "Defesa", "Saldo de Gols (SG)"])
    with c_filt3:
        lista_confrontos = ["Todos os Jogos"] + [
            f"{clubes_raw[str(j['clube_casa_id'])]['nome']} x {clubes_raw[str(j['clube_visitante_id'])]['nome']}"
            for j in partidas]
        jogo_selecionado = st.selectbox("Filtrar por Confronto:", lista_confrontos)

    map_scout = {"Pontos":"pontos_num", "Desarmes (DS)":"DS", "Gols (G)":"G",
                 "Assistências (A)":"A", "Defesa":"DE", "Saldo de Gols (SG)":"SG"}
    foco_key = map_scout[scout_foco]

    # ============================================================
    # CARDS DOS CONFRONTOS
    # ============================================================
    for jogo in partidas:
        nome_confronto = f"{clubes_raw[str(jogo['clube_casa_id'])]['nome']} x {clubes_raw[str(jogo['clube_visitante_id'])]['nome']}"
        if jogo_selecionado != "Todos os Jogos" and jogo_selecionado != nome_confronto:
            continue

        id_casa = str(jogo['clube_casa_id'])
        id_fora = str(jogo['clube_visitante_id'])
        casa = clubes_raw[id_casa]
        fora = clubes_raw[id_fora]
        df_c = df[df['clube_id'] == jogo['clube_casa_id']]
        df_f = df[df['clube_id'] == jogo['clube_visitante_id']]

        confianca = calcular_confianca(df_c, df_f)
        cor_conf = "#28a745" if confianca >= 70 else "#FF6600" if confianca >= 40 else "#dc3545"
        txt_conf = "ALTA" if confianca >= 70 else "MÉDIA" if confianca >= 40 else "BAIXA"

        rows_html = ""
        total_idx_casa = 0
        total_idx_fora = 0

        for setor in ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"]:
            # CASA atacando
            conq_c = calcular_conquista(df_c, setor, foco_key, scout_foco)
            ced_f = calcular_cedencia(df_f, setor, foco_key, scout_foco)  # FORA cede para posição X da CASA
            idx_c = calcular_indice(conq_c, ced_f, True)

            # FORA atacando
            conq_f = calcular_conquista(df_f, setor, foco_key, scout_foco)
            ced_c = calcular_cedencia(df_c, setor, foco_key, scout_foco)  # CASA cede para posição X do FORA
            idx_f = calcular_indice(conq_f, ced_c, False)

            total_idx_casa += idx_c
            total_idx_fora += idx_f

            def cor_idx(v):
                if v >= 10: return "#28a745"
                elif v >= 5: return "#FF6600"
                return "#dc3545"

            rows_html += f"""
            <div style="display:flex; align-items:center; background:#fdfdfd; border:1.5px solid #eee; 
                        padding:12px; border-radius:10px; margin-top:6px; text-align:center;">
                <div style="flex:1.5; font-weight:900; color:#000; text-align:left; font-size:13px;">{setor.upper()}</div>
                <div style="flex:1.5; font-size:15px; font-weight:800; color:#000;">{conq_c:.1f}<br><span style="font-size:8px; color:#888;">CONQ</span></div>
                <div style="flex:1.5; font-size:15px; font-weight:800; color:#FF6600;">{ced_f:.1f}<br><span style="font-size:8px; color:#888;">CEDE</span></div>
                <div style="flex:1;"><div style="background:{cor_idx(idx_c)}; color:white; padding:4px 6px; border-radius:8px; font-weight:900; font-size:13px;">{idx_c:.1f}</div></div>
                <div style="flex:0.1; background:#FF6600; height:35px; margin:0 6px; border-radius:2px;"></div>
                <div style="flex:1;"><div style="background:{cor_idx(idx_f)}; color:white; padding:4px 6px; border-radius:8px; font-weight:900; font-size:13px;">{idx_f:.1f}</div></div>
                <div style="flex:1.5; font-size:15px; font-weight:800; color:#000;">{conq_f:.1f}<br><span style="font-size:8px; color:#888;">CONQ</span></div>
                <div style="flex:1.5; font-size:15px; font-weight:800; color:#FF6600;">{ced_c:.1f}<br><span style="font-size:8px; color:#888;">CEDE</span></div>
            </div>"""

        card_html = f"""
        <div style="background:white; border:4px solid #000; border-radius:20px; padding:25px; 
                    font-family:'Arial Black',sans-serif; box-shadow:12px 12px 0px #FF6600; margin-bottom:50px;">
            
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div style="text-align:center; width:38%;">
                    <img src="{casa['escudos']['60x60']}" width="65"><br>
                    <b style="font-size:20px; color:#000;">{casa['nome'].upper()}</b><br>
                    <span style="background:#000; color:#FF6600; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:900;">🏠 MANDANTE</span>
                </div>
                <div style="width:24%; text-align:center;">
                    <b style="font-size:32px; color:#FF6600;">VS</b><br>
                    <div style="background:{cor_conf}; color:white; padding:4px 12px; border-radius:10px; font-size:10px; font-weight:900; margin-top:8px;">
                        🎯 CONFIANÇA: {confianca}% ({txt_conf})
                    </div>
                </div>
                <div style="text-align:center; width:38%;">
                    <img src="{fora['escudos']['60x60']}" width="65"><br>
                    <b style="font-size:20px; color:#000;">{fora['nome'].upper()}</b><br>
                    <span style="background:#555; color:white; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:900;">🚌 VISITANTE</span>
                </div>
            </div>

            <div style="display:flex; justify-content:space-around; background:#FF6600; color:#000; padding:12px; border:3px solid #000; border-radius:10px; margin-bottom:15px; font-weight:900; font-size:15px;">
                <div style="text-align:center;">{casa['abreviacao']} ÍNDICE<br><span style="font-size:24px;">{total_idx_casa:.1f}</span></div>
                <div style="border-left:3px solid #000;"></div>
                <div style="text-align:center;">{fora['abreviacao']} ÍNDICE<br><span style="font-size:24px;">{total_idx_fora:.1f}</span></div>
            </div>

            <div style="background:#000; color:#FF6600; text-align:center; padding:10px; font-weight:900; font-size:14px; border-radius:8px; margin-bottom:10px;">
                📊 {scout_foco.upper()} | FÓRMULA: (CONQUISTA × 0.55 + CEDÊNCIA × 0.45) × BÔNUS MANDO
            </div>

            <div style="display:flex; background:#000; color:white; padding:10px; border-radius:5px; font-size:10px; text-align:center; font-weight:bold;">
                <div style="flex:1.5; text-align:left;">SETOR</div>
                <div style="flex:1.5;">{casa['abreviacao']} CONQ</div>
                <div style="flex:1.5; color:#FF6600;">{fora['abreviacao']} CEDE</div>
                <div style="flex:1;">IDX</div>
                <div style="flex:0.1;"></div>
                <div style="flex:1;">IDX</div>
                <div style="flex:1.5;">{fora['abreviacao']} CONQ</div>
                <div style="flex:1.5; color:#FF6600;">{casa['abreviacao']} CEDE</div>
            </div>

            {rows_html}

            <div style="display:flex; justify-content:center; gap:20px; margin-top:12px; font-size:10px; font-weight:bold;">
                <span>🟢 ALTA (≥10)</span> <span>🟠 MODERADA (5-10)</span> <span>🔴 BAIXA (&lt;5)</span>
            </div>

            <div style="margin-top:30px; border-top:3px dashed #000; padding-top:20px;">
                <div style="text-align:center; font-size:14px; font-weight:900; color:#000; margin-bottom:15px;">
                    🚀 ALVOS DE ELITE: {scout_foco.upper()} (FORÇA × FRAGILIDADE DO RIVAL)
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <div style="width:48%;">
                        <div style="text-align:center; font-weight:900; color:#000; margin-bottom:8px; font-size:12px;">🏠 {casa['nome'].upper()}</div>
                        {get_top_targets(jogo['clube_casa_id'], df_f, foco_key, scout_foco)}
                    </div>
                    <div style="width:48%;">
                        <div style="text-align:center; font-weight:900; color:#000; margin-bottom:8px; font-size:12px;">🚌 {fora['nome'].upper()}</div>
                        {get_top_targets(jogo['clube_visitante_id'], df_c, foco_key, scout_foco)}
                    </div>
                </div>
            </div>
        </div>
        """
        components.html(card_html, height=1000)


# --- 📈 HISTÓRICO (DESIGN SHADOW ARENA) ---
elif menu == "📈 Histórico":
    st.markdown("<h1 class='orange-title'>📈 Histórico das Minhas Dicas</h1>", unsafe_allow_html=True)
    
    # Seletor de Rodada com estilo
    rodada_view = st.selectbox("Escolher Rodada para consulta:", range(1, 39), index=rodada_atual-1)
    
    st.markdown(f"### 🏟️ Registros da Rodada {rodada_view}")
    
    historico = st.session_state.historico_arena.get(rodada_view, {})
    
    if not any(historico.values()):
        st.info(f"Nenhum registro encontrado para a Rodada {rodada_view}.")
    else:
        for posicao, jogadores in historico.items():
            if jogadores:
                # Subtítulo com detalhe laranja
                st.markdown(f"""
                    <div style="border-left: 5px solid #FF6600; padding-left: 10px; margin: 20px 0 10px 0;">
                        <h3 style="color: white; margin: 0;">🛡️ {posicao.upper()}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Criar colunas para os cards dos jogadores
                cols = st.columns(3)
                for idx, j in enumerate(jogadores):
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div style="background: white; border: 3px solid #000; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 6px 6px 0px #FF6600;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <img src="{j.get('foto', '').replace('FORMATO', '140x140')}" width="50" style="border-radius: 50%; border: 2px solid #000;">
                                <div>
                                    <div style="font-weight: 900; color: #000; text-transform: uppercase; font-size: 14px;">{j['apelido']}</div>
                                    <div style="background: #FF6600; color: #000; font-size: 10px; padding: 1px 5px; border-radius: 4px; display: inline-block; font-weight: bold;">{posicao.upper()}</div>
                                </div>
                            </div>
                            <div style="background: #f0f0f0; border: 1px solid #000; border-radius: 5px; padding: 5px;">
                                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #333;">
                                    <span>Média:</span> <b>{j['media_num']:.2f}</b>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #333;">
                                    <span>Preço:</span> <b>C$ {j['preco_num']:.2f}</b>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #000; margin-top: 2px; border-top: 1px solid #ccc;">
                                    <span>PONTOS:</span> <b style="color: #FF6600;">{j.get('pontos_num', 0.0):.2f}</b>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)