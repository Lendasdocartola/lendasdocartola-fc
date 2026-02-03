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
    st.markdown("<h2 class='orange-title'>CARTOLA AI</h2>", unsafe_allow_html=True)
    # Trocado para o ícone de prancheta (📋) conforme pedido
    menu = st.radio("Menu:", ["🏠 Dashboard", "⚽ Minhas Dicas", "🔍 Raio-X do Craque", "📋 Quadro Tático", "📊 Central Probabilidades", "🧠 Radar de Capitão", "🔥 Termômetro", "💰 Simulador de Valorização", "🏟️ Análise de Confrontos", "📈 Histórico"])
    
    status_filter = st.checkbox("Somente Prováveis", value=True)

df_active = df[df['status_id'] == 7] if status_filter else df

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.markdown("<h1 class='orange-title'>🏠 Painel Analítico</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        avg_pos = df_active.groupby('pos_nome')['media_num'].mean().reset_index()
        fig1 = px.bar(avg_pos, x='pos_nome', y='media_num', title="Eficiência por Posição", template="plotly_white", color_discrete_sequence=['#ff6600'])
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        top_clubes = df_active.groupby('time_nome')['media_num'].sum().nlargest(6).reset_index()
        fig2 = px.pie(top_clubes, values='media_num', names='time_nome', title="Potência por Clube", hole=.4, template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)


# --- ⚽ MINHAS DICAS (V78.0 - SINCRONIZAÇÃO COM ESCALAÇÃO VISUAL) ---
elif menu == "⚽ Minhas Dicas":
    st.markdown("""
        <style>
            .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stNumberInput div {
                border: 2px solid #FF6600 !important;
                background-color: #f9f9f9 !important;
            }
            label { color: #000 !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='orange-title'>⚽ Cadastro de Dicas Na Rodada</h1>", unsafe_allow_html=True)
    
    c_rodada, c_pos = st.columns([1, 2])
    with c_rodada:
        rodada_sel = st.number_input("Rodada:", min_value=1, max_value=38, value=rodada_atual)
    with c_pos:
        pos = st.selectbox("Posição:", ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"])
    
    df_filtrado = df_active[df_active['pos_nome'] == pos].copy()
    
    def get_nome_clube(cid):
        return clubes_raw[str(cid)]['nome'].upper() if str(cid) in clubes_raw else "TIME"

    df_filtrado['label_completo'] = df_filtrado.apply(lambda x: f"{get_nome_clube(x['clube_id'])} | {x['apelido']}", axis=1)
    opcoes_dicas = df_filtrado.sort_values('media_num', ascending=False)['label_completo'].tolist()
    
    selecionados_labels = st.multiselect("Selecione até 5 Gladiadores para suas Dicas:", options=opcoes_dicas, max_selections=5)
    
    if selecionados_labels:
        df_comp = df_filtrado[df_filtrado['label_completo'].isin(selecionados_labels)].copy()
        
        # Exibição dos Cards (Design Shadow)
        cols = st.columns(len(selecionados_labels))
        for i, (index, p) in enumerate(df_comp.iterrows()):
            card = f"""
            <div style="background:#000; border-radius:15px; padding:15px; text-align:center; border-bottom:5px solid #ff6600; color:#fff; height:500px; border: 1px solid #eee;">
                <img src="{p.get('time_escudo', '')}" width="30"><br>
                <div style="font-size:10px; font-weight:bold; color:#FF6600;">{get_nome_clube(p['clube_id'])}</div>
                <img src="{p["foto"].replace("FORMATO","140x140")}" width="80" style="border-radius:50%; border:2px solid #ff6600; margin:10px 0;">
                <div style="font-size:16px; font-weight:800;">{p['apelido']}</div>
                <div style="color:#FF6600; font-weight:800; font-size:20px;">C$ {p["preco_num"]}</div>
                <div style="background:#fff; border-radius:10px; padding:10px; text-align:left; color:#333; margin-top:10px;">
                    <div style="color:#000; font-weight:800; font-size:10px;">MÉDIA</div>
                    <div style="color:#ff6600; font-weight:800; font-size:18px;">{p['media_num']:.2f}</div>
                </div>
            </div>"""
            with cols[i]: components.html(card, height=520)
        
        # --- BOTÃO DE GRAVAÇÃO CORRIGIDO PARA ENVIAR PARA ESCALAÇÃO VISUAL ---
        if st.button(f"💾 ENVIAR PARA ESCALAÇÃO VISUAL - R{rodada_sel}"):
            # Prepara os dados no formato que a Escalação Visual entende
            lista_para_enviar = df_comp.to_dict('records')
            
            # 1. Salva no Histórico
            if 'historico_arena' not in st.session_state: st.session_state.historico_arena = {}
            if rodada_sel not in st.session_state.historico_arena: st.session_state.historico_arena[rodada_sel] = {}
            st.session_state.historico_arena[rodada_sel][pos] = lista_para_enviar
            
            # 2. Salva no Time Escalado (Onde a Escalação Visual busca)
            if 'time_escalado' not in st.session_state: st.session_state.time_escalado = {}
            st.session_state.time_escalado[pos] = lista_para_enviar
            
            st.success(f"✅ Sucesso! Os jogadores de {pos} agora aparecerão no menu Escalação Visual.")

# --- RAIO-X DO CRAQUE ---
elif menu == "🔍 Raio-X do Craque":
    st.markdown("<h1 class='orange-title'>🔍 Raio-X do Craque</h1>", unsafe_allow_html=True)
    atleta = st.selectbox("Escolha o Atleta:", df_active['apelido'].sort_values())
    p = df_active[df_active['apelido'] == atleta].iloc[0]
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.image(p['foto'].replace("FORMATO","140x140"), width=180)
        st.markdown(f"### {p['apelido']}")
        st.image(p['time_escudo'], width=50)
        st.metric("Média", p['media_num'])
        st.metric("Preço", f"C$ {p['preco_num']}")
    with c2:
        st.subheader("📊 Atributos")
        radar_data = pd.DataFrame(dict(r=[p.get('G',0)*3, p.get('A',0)*3, p.get('DS',0), p.get('FS',0), p.get('FD',0)], theta=['Gols','Assis','Desarmes','Faltas S','Finaliz.']))
        fig_radar = px.line_polar(radar_data, r='r', theta='theta', line_close=True, template="plotly_white", color_discrete_sequence=['#ff6600'])
        st.plotly_chart(fig_radar, use_container_width=True)
    with c3:
        st.subheader("🗺️ Mapa de Calor de Scouts")
        z = np.zeros((10, 10))
        if p['pos_nome'] == 'Atacante': z[7:10, 3:7] += p.get('G',0) + p.get('FD',0)
        elif p['pos_nome'] == 'Meia': z[4:8, 2:8] += p.get('A',0) + p.get('DS',0)
        elif p['pos_nome'] == 'Zagueiro': z[1:4, 2:8] += p.get('DS',0) + p.get('FC',0)
        else: z[0:2, 4:6] += p.get('DE',0)
        fig_heat = px.imshow(z, color_continuous_scale='Oranges', aspect="auto", template="plotly_white")
        st.plotly_chart(fig_heat, use_container_width=True)

# --- 📋 QUADRO TÁTICO (V81.0 - CÓDIGO COMPLETO E CORRIGIDO) ---
elif menu == "📋 Quadro Tático":
    st.markdown("<h1 class='orange-title'>🏟️ Quadro Tático Oficial & Reservas</h1>", unsafe_allow_html=True)
    
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
        
        # Mantém a consistência dos jogadores selecionados
        random.seed(st.session_state.seed_campo)
        sampled = random.sample(players, min(len(players), count))
        while len(sampled) < count:
            sampled.append({"apelido": "Vazio", "foto": "none", "preco_num": 0, "pontos_live": 0, "scouts_live": {}})
        return sampled

    gol_t = get_titulares("Goleiro", 1)
    lats_t = get_titulares("Lateral", config["Lateral"])
    zags_t = get_titulares("Zagueiro", config["Zagueiro"])
    meis_t = get_titulares("Meia", config["Meia"])
    atas_t = get_titulares("Atacante", config["Atacante"])

    st.markdown("### 📋 Banco de Reservas")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        lux_pos = st.selectbox("Posição Escolhida para Reserva de Luxo:", [None, "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"], index=0)
        st.session_state.posicao_luxo = lux_pos
        modo_banco = st.radio("Modo:", ["Automático", "Manual"])

    def filter_reserves(pos_name, titulares):
        if not titulares or titulares[0]["apelido"] == "Vazio": return pd.DataFrame()
        precos = [t["preco_num"] for t in titulares if t["apelido"] != "Vazio"]
        if not precos: return pd.DataFrame()
        corte = max(precos) if lux_pos == pos_name else min(precos)
        pos_df = df_active[df_active['pos_nome'] == pos_name]
        return pos_df[pos_df['preco_num'] < corte].sort_values('media_num', ascending=False)

    log_substituicao = []
    final_team = {"Goleiro": gol_t, "Lateral": lats_t, "Zagueiro": zags_t, "Meia": meis_t, "Atacante": atas_t}

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
                    res_name = st.selectbox(f"Reserva {pos_abrev[p_name]}:", ["--"] + validos['apelido'].tolist(), key=f"res_v2_{p_name}")
                    if res_name != "--":
                        res_chosen = validos[validos['apelido'] == res_name].iloc[0].to_dict()
            elif modo_banco == "Automático" and not validos.empty:
                res_chosen = validos.iloc[0].to_dict()

            if res_chosen:
                st.markdown(f'''
                    <div class="bench-card-v2">
                        <img src="{res_chosen.get("time_escudo", "")}" style="width:25px;">
                        <div style="font-size:10px; color:#FF6600; font-weight:bold; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">{res_chosen["apelido"]}</div>
                        <div class="bench-pos-v2">{pos_abrev[p_name]}</div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                    <div class="bench-card-v2">
                        <div class="bench-plus-v2">+</div>
                        <div class="bench-pos-v2">{pos_abrev[p_name]}</div>
                    </div>
                ''', unsafe_allow_html=True)

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

    html_field = f"""
        <div class="center-line"></div>
        <div class="center-circle"></div>
        <div class="penalty-area-left"></div>
        <div class="small-area-left"></div>
        <div class="arc-left"></div>
        <div class="penalty-area-right"></div>
        <div class="small-area-right"></div>
        <div class="arc-right"></div>
    """
    
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


# --- 🏟️ ANÁLISE DE CONFRONTOS (V72.0 - TOTALIZADORES POR TIME & DESIGN SHADOW) ---
elif menu == "🏟️ Análise de Confrontos":
    st.markdown("<h1 class='orange-title' style='font-size: 32px;'>🏟️ Matriz de Confrontos & Cedentes</h1>", unsafe_allow_html=True)
    
    c_filt1, c_filt2, c_filt3 = st.columns([1.5, 2, 2])
    with c_filt1:
        qtd_jogos = st.select_slider("Tendência (Rodadas):", options=[1, 2, 3, 4, 5], value=1)
    with c_filt2:
        scout_foco = st.selectbox("Escolha o Scout para Analisar:", 
                                 ["Pontos", "Desarmes (DS)", "Gols (G)", "Assistências (A)", "Defesa", "Saldo de Gols (SG)"])
    with c_filt3:
        lista_confrontos = ["Todos os Jogos"] + [f"{clubes_raw[str(j['clube_casa_id'])]['nome']} x {clubes_raw[str(j['clube_visitante_id'])]['nome']}" for j in partidas]
        jogo_selecionado = st.selectbox("Filtrar por Confronto:", lista_confrontos)

    map_scout = {"Pontos": "pontos_num", "Desarmes (DS)": "DS", "Gols (G)": "G", "Assistências (A)": "A", "Defesa": "DE", "Saldo de Gols (SG)": "SG"}
    foco_key = map_scout[scout_foco]

    for jogo in partidas:
        nome_confronto = f"{clubes_raw[str(jogo['clube_casa_id'])]['nome']} x {clubes_raw[str(jogo['clube_visitante_id'])]['nome']}"
        if jogo_selecionado != "Todos os Jogos" and jogo_selecionado != nome_confronto:
            continue

        id_casa = str(jogo['clube_casa_id']); id_fora = str(jogo['clube_visitante_id'])
        casa = clubes_raw[id_casa]; fora = clubes_raw[id_fora]
        df_c = df[df['clube_id'] == jogo['clube_casa_id']]
        df_f = df[df['clube_id'] == jogo['clube_visitante_id']]

        def get_metrics_v72(df_time, df_adv, pos, scout):
            df_pos = df_time[df_time['pos_nome'] == pos]
            if scout == "SG":
                gols_sofridos = df_time[df_time['pos_nome'] == 'Goleiro']['GS'].sum() if not df_time.empty else 1
                prob = 100 if gols_sofridos == 0 else 20
                return prob, prob
            
            conq = df_pos[scout].mean() if scout in df_pos.columns and not df_pos.empty else 0
            def safe_mean(dframe, col):
                return dframe[col].mean() if col in dframe.columns and not dframe.empty else 0
            
            if scout == "G": ced = df_adv[df_adv['pos_nome'] == 'Goleiro']['GS'].mean() if not df_adv.empty else 0
            elif scout == "A": ced = (df_adv[df_adv['pos_nome'] == 'Goleiro']['GS'].mean() if not df_adv.empty else 0) * 0.7
            elif scout == "DS": ced = (safe_mean(df_adv, 'FC') + safe_mean(df_adv, 'PI')) * 0.5
            elif scout == "DE": ced = (safe_mean(df_adv, 'FD') + safe_mean(df_adv, 'FT')) * 0.7
            else: ced = safe_mean(df_adv, 'pontos_num')
            return conq, ced

        # --- CÁLCULO DOS TOTAIS DO TIME ---
        total_conq_casa = df_c[foco_key].sum() if foco_key in df_c.columns else 0
        total_ced_casa = (df_f['FC'].sum() + df_f.get('PI', pd.Series([0])).sum()) * 0.5 if foco_key == "DS" else df_f['pontos_num'].sum() * 0.6
        
        total_conq_fora = df_f[foco_key].sum() if foco_key in df_f.columns else 0
        total_ced_fora = (df_c['FC'].sum() + df_c.get('PI', pd.Series([0])).sum()) * 0.5 if foco_key == "DS" else df_c['pontos_num'].sum() * 0.6

        def get_top_targets_v72(clube_id, scout_key, foco_original):
            df_clv = df_active[df_active['clube_id'] == clube_id]
            if foco_original in ["Defesa", "Saldo de Gols (SG)"]:
                df_clv = df_clv[df_clv['pos_nome'].isin(['Goleiro', 'Zagueiro', 'Lateral'])]
            sort_col = scout_key if scout_key in df_clv.columns else 'media_num'
            top = df_clv.sort_values(by=sort_col, ascending=False).head(3)
            html_res = ""
            for _, p in top.iterrows():
                f_url = str(p['foto']).replace('FORMATO', '140x140')
                html_res += f"""
                <div style="display: flex; align-items: center; background: #000; color: #fff; padding: 8px 15px; border-radius: 20px; border: 2px solid #FF6600; margin: 6px; width: 95%;">
                    <img src="{f_url}" width="35" style="border-radius: 50%; border: 1.5px solid #FF6600; margin-right: 12px;">
                    <div style="font-size: 13px; line-height: 1.2;">
                        <b style="font-size: 14px;">{p['apelido']}</b><br>
                        <span style="color: #FF6600; font-weight: bold;">{p['pos_nome']} | {scout_foco}: {p.get(sort_col, 0):.1f}</span>
                    </div>
                </div>
                """
            return html_res

        rows_html = ""
        for s in ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"]:
            c_conq, f_ced = get_metrics_v72(df_c, df_f, s, foco_key)
            f_conq, c_ced = get_metrics_v72(df_f, df_c, s, foco_key)
            suf = "%" if scout_foco == "Saldo de Gols (SG)" else ""
            rows_html += f"""
            <div style="display: flex; align-items: center; background: #fdfdfd; border: 1.5px solid #eee; padding: 12px; border-radius: 10px; text-align: center; margin-top: 6px;">
                <div style="flex: 1.5; font-weight: 900; color: #000; text-align: left; font-size: 15px;">{s.upper()}</div>
                <div style="flex: 2; font-size: 20px; font-weight: 800;">{c_conq:.1f}{suf}</div>
                <div style="flex: 2; font-size: 20px; color: #FF6600; font-weight: 800;">{f_ced:.1f}{suf}</div>
                <div style="flex: 0.2; background: #FF6600; height: 20px; margin: 0 10px;"></div>
                <div style="flex: 2; font-size: 20px; font-weight: 800;">{f_conq:.1f}{suf}</div>
                <div style="flex: 2; font-size: 20px; color: #FF6600; font-weight: 800;">{c_ced:.1f}{suf}</div>
            </div>
            """

        card_html = f"""
        <div style="background-color: white; border: 4px solid #000; border-radius: 20px; padding: 25px; font-family: 'Arial Black', sans-serif; box-shadow: 12px 12px 0px #FF6600; margin-bottom: 50px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div style="text-align: center; width: 42%;"><img src="{casa['escudos']['60x60']}" width="65"><br><b style="font-size: 20px; color: #000;">{casa['nome'].upper()}</b></div>
                <div style="width: 16%; text-align: center;"><b style="font-size: 32px; color: #FF6600;">VS</b></div>
                <div style="text-align: center; width: 42%;"><img src="{fora['escudos']['60x60']}" width="65"><br><b style="font-size: 20px; color: #000;">{fora['nome'].upper()}</b></div>
            </div>
            
            <div style="display: flex; justify-content: space-around; background: #FF6600; color: #000; padding: 10px; border: 3px solid #000; border-radius: 10px; margin-bottom: 15px; font-weight: 900; font-size: 14px;">
                <div style="text-align: center;">{casa['abreviacao']} TOTAL: {total_conq_casa:.0f}</div>
                <div style="border-left: 3px solid #000;"></div>
                <div style="text-align: center;">{fora['abreviacao']} TOTAL: {total_conq_fora:.0f}</div>
            </div>

            <div style="background: #000; color: #FF6600; text-align: center; padding: 10px; font-weight: 900; font-size: 16px; border-radius: 8px; margin-bottom: 15px;">
                ESTRATEGIA: {scout_foco.upper()}
            </div>

            <div style="display: flex; background: #000; color: white; padding: 12px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">
                <div style="flex: 1.5; text-align: left;">SETOR</div>
                <div style="flex: 2;">{casa['abreviacao']} (CONQ.)</div>
                <div style="flex: 2; color: #FF6600;">{fora['abreviacao']} (CEDE)</div>
                <div style="flex: 0.2;"></div>
                <div style="flex: 2;">{fora['abreviacao']} (CONQ.)</div>
                <div style="flex: 2; color: #FF6600;">{casa['abreviacao']} (CEDE)</div>
            </div>

            {rows_html}

            <div style="margin-top: 30px; border-top: 3px dashed #000; padding-top: 20px;">
                <div style="text-align: center; font-size: 14px; font-weight: 900; color: #000; margin-bottom: 15px; text-transform: uppercase;">🚀 SUGESTÕES DE ELITE PARA {scout_foco}</div>
                <div style="display: flex; justify-content: space-between;">
                    <div style="width: 49%;">{get_top_targets_v72(jogo['clube_casa_id'], foco_key, scout_foco)}</div>
                    <div style="width: 49%;">{get_top_targets_v72(jogo['clube_visitante_id'], foco_key, scout_foco)}</div>
                </div>
            </div>
        </div>
        """
        components.html(card_html, height=900)
# --- 📈 HISTÓRICO ---
elif menu == "📈 Histórico":
    st.markdown("<h1 class='orange-title'>📈 Histórico de Gravações Arena</h1>", unsafe_allow_html=True)
    rodada_view = st.selectbox("Ver Histórico da Rodada:", range(1, 39), index=rodada_atual-1)
    historico = st.session_state.historico_arena[rodada_view]
    for posicao, jogadores in historico.items():
        if jogadores:
            st.subheader(f"🛡️ {posicao}")
            st.table(pd.DataFrame(jogadores)[['apelido', 'media_num', 'preco_num', 'pontos_num']])