import base64
import datetime as dt
import io
from html import escape
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import folium
import requests
import streamlit as st
from PIL import Image, ImageOps
from folium import plugins
from streamlit_folium import st_folium

# ==============================================================================
# CONFIGURAÇÃO DE SISTEMA (COCKPIT MOTO HUD)
# ==============================================================================
st.set_page_config(
    page_title="RALLY ROADBOOK // PIÓDÃO 2026",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

try:
    TZ = ZoneInfo("Europe/Lisbon")
except Exception:
    TZ = dt.timezone(dt.timedelta(hours=1))

WEATHER_KEY = st.secrets.get("OPENWEATHER_KEY", "")
ORS_KEY = st.secrets.get("ORS_KEY", "")
SUPA_URL = st.secrets.get("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = st.secrets.get("SUPABASE_KEY", "")

DIAS_SEMANA = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
MESES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

# ==============================================================================
# PLANO DE ROTA (TELEMETRIA E DADOS RALLY)
# ==============================================================================
DIAS = [
    {
        "id": 1,
        "titulo": "Benção e Romance",
        "codigo": "STG-01",
        "data": dt.date(2026, 9, 20),
        "km": 225,
        "min": 150,
        "cor": "#00D2FF",
        "cor_rgb": "0, 210, 255",
        "autoestrada": True,
        "terreno": "AUTOESTRADA A1 / A8",
        "paragens": [
            ("Cascais", 38.6960614, -9.4303646, "09:00"),
            ("Fátima", 39.6324, -8.6713, "10:30"),
            ("Coimbra", 40.2033145, -8.4102573, "15:30"),
        ],
        "horario": [
            ("09:00", "PARTIDA DE CASCAIS", "Via A8/A1 · Saída com depósito cheio"),
            ("10:30", "CHEGADA A FÁTIMA", "Estacionamento motos"),
            ("11:00", "MISSA & BENÇÃO DOS CAPACETES", "Santuário"),
            ("13:00", "ALMOÇO EM FÁTIMA", "Pausa livre"),
            ("14:30", "ARRANQUE RUMO A COIMBRA", "Ligação direta"),
            ("15:30", "CHECK-IN & QUINTA DAS LÁGRIMAS", "Passeio a pé"),
            ("20:00", "JANTAR: QUEBRA O GALHO", "Reservado · 12 min a pé na Alta"),
        ],
        "vistas": ["Santuário de Fátima", "Quinta das Lágrimas", "Alta de Coimbra"],
        "comer": [
            {"quando": "Almoço", "nome": "Em Fátima", "maps": "Restaurantes Fátima"},
            {"quando": "Jantar 20:00", "nome": "Quebra o Galho", "url": "https://www.quebraogalho.com/", "reservado": True,
             "coords": (40.2087486, -8.4282289), "a_pe": "~900 m · 12 min a pé (atravessar ponte e subir na Alta)"},
        ],
        "dormir": {"nome": "Five Senses in Coimbra", "maps": "Five Senses in Coimbra", "reservado": True},
        "combustivel": [],
        "aviso_combustivel": "Áreas de serviço frequentes na A8 e A1. Atestar conforme necessário.",
        "dica": "Tiradas rápidas de autoestrada. Casaco ventilado e tampões de ouvidos essenciais.",
    },
    {
        "id": 2,
        "titulo": "O Refúgio no Xisto",
        "codigo": "STG-02",
        "data": dt.date(2026, 9, 21),
        "km": 95,
        "min": 140,
        "cor": "#FF6B00",
        "cor_rgb": "255, 107, 0",
        "autoestrada": False,
        "terreno": "CURVAS DE SERRA // ESTRADAS DE XISTO",
        "paragens": [
            ("Coimbra", 40.2033145, -8.4102573, "10:30"),
            ("Góis", 40.1572681, -8.1106277, "12:00"),
            ("Fajão", 40.1495149, -7.9222764, "13:30"),
            ("Piódão", 40.2292601, -7.8250288, "16:45"),
        ],
        "horario": [
            ("10:30", "SAÍDA DE COIMBRA", "Rumo à EN110 / Góis"),
            ("12:00", "CHEGADA A GÓIS", "Café à beira do Rio Ceira"),
            ("12:30", "SUBIDA RUMO A FAJÃO", "Início das curvas apertadas"),
            ("13:30", "ALMOÇO: O JUIZ (FAJÃO)", "Chanfana em forno a lenha"),
            ("15:30", "DESCIDA PARA A SERRA DO AÇOR", "Atenção ao piso e gravilha"),
            ("16:45", "CHEGADA AO PIÓDÃO", "Check-in e pôr do sol no anfiteatro"),
            ("19:00", "JANTAR: O FONTINHA", "Reservado · 11 min a pé (levar lanterna)"),
        ],
        "vistas": ["Garganta do Rio Ceira", "Aldeia de Fajão", "Pôr do sol no Piódão"],
        "comer": [
            {"quando": "Almoço", "nome": "O Juiz (Fajão)", "nota": "Chanfana clássica", "maps": "O Juiz Fajão"},
            {"quando": "Jantar 19:00", "nome": "O Fontinha (Piódão)", "reservado": True, "coords": (40.2297396, -7.8249356),
             "a_pe": "~850 m · 11 min a pé do hotel (regresso a subir)"},
        ],
        "dormir": {"nome": "INATEL Piódão Hotel", "maps": "INATEL Piodao Hotel", "reservado": True},
        "combustivel": [
            {"nome": "Galp — Coimbra Sul", "coords": (40.2013031, -8.4086694), "nota": "Atestar antes da serra"},
            {"nome": "Alves Bandeira — Góis", "coords": (40.1554162, -8.1141220), "nota": "ÚLTIMA BOMBA ANTES DA SERRA"},
        ],
        "aviso_combustivel": "⚠️ ATENÇÃO: Não há bombas no Fajão nem no Piódão. Sair de Góis com depósito ATESTATO (100%).",
        "dica": "A temperatura desce drasticamente ao entardecer no Açor. Forro térmico acessível na mala.",
    },
    {
        "id": 3,
        "titulo": "O Vale do Alva, Retiro e SPA",
        "codigo": "STG-03",
        "data": dt.date(2026, 9, 22),
        "km": 175,
        "min": 165,
        "cor": "#00E676",
        "cor_rgb": "0, 230, 118",
        "autoestrada": False,
        "terreno": "VALE DO ALVA (M508/N230) ➔ IC6/IC8 ➔ COSTA",
        "paragens": [
            ("Piódão", 40.2292601, -7.8250288, "09:45"),
            ("Vide", 40.295411, -7.784012, "10:30"),
            ("Ponte das Três Entradas", 40.306915, -7.870779, "10:50"),
            ("Côja", 40.256689, -7.990173, "11:20"),
            ("Casal de S. Simão", 39.9163506, -8.3223319, "12:30"),
            ("Praia da Vieira", 39.8739013, -8.9693060, "16:45"),
        ],
        "horario": [
            ("09:45", "SAÍDA DO PIÓDÃO PELA M508", "Direção norte · encosta remota da serra"),
            ("10:30", "PASSAGEM EM VIDE ➔ ENTRADA NA N230", "Asfalto de sonho colado ao Rio Alva"),
            ("10:50", "PONTE DAS TRÊS ENTRADAS", "Confluência dos rios · curvas lendárias de moto"),
            ("11:20", "PARAGEM EM CÔJA (VALE DO ALVA)", "Secção verdejante · café rápido à beira-rio"),
            ("11:45", "TRANSIÇÃO RÁPIDA VIA IC6 / IC8", "Vias rápidas para despachar transição a sul"),
            ("12:30", "CHEGADA A CASAL DE S. SIMÃO", "Passeio a pé nos Passadiços antes do almoço"),
            ("13:30", "ALMOÇO: VARANDA DO CASAL", "Reservado · vista panorâmica para a serra"),
            ("15:30", "ARRANQUE RUMO À COSTA (IC8)", "Ligação suave para o litoral"),
            ("16:45", "CHEGADA À PRAIA DA VIEIRA", "Direto para o SPA & piscina do Hotel Cristal"),
            ("20:00", "JANTAR: NAU FRÁGIL", "Reservado · 1 min a pé na marginal"),
        ],
        "vistas": ["Estrada M508 (Encosta Norte)", "Curvas da N230 no Rio Alva", "Ponte das Três Entradas", "Passadiços de S. Simão", "Pôr do sol atlântico"],
        "comer": [
            {"quando": "Almoço", "nome": "Varanda do Casal", "maps": "Varanda do Casal Casal de São Simão"},
            {"quando": "Jantar 20:00", "nome": "Nau Frágil", "reservado": True, "coords": (39.875889, -8.971315),
             "a_pe": "~100 m · 1 min a pé do hotel"},
        ],
        "dormir": {"nome": "Hotel Cristal Vieira Praia & SPA", "maps": "Hotel Cristal Vieira Praia SPA", "reservado": True},
        "combustivel": [
            {"nome": "Alves Bandeira — Côja", "coords": (40.2592, -7.9941), "nota": "Bomba na saída de Côja rumo ao IC6"},
            {"nome": "Intermarché — Figueiró dos Vinhos", "coords": (39.9058098, -8.2807051), "nota": "No IC8, ~8 km antes de Casal de S. Simão"},
            {"nome": "Galp — Vieira de Leiria", "coords": (39.8691482, -8.9344074), "nota": "À chegada ao hotel"},
        ],
        "aviso_combustivel": "⛽ Rota do Vale do Alva com bomba garantida em Côja antes de entrar no IC6.",
        "dica": "A N230 entre Vide e a Ponte das Três Entradas é pura diversão motociclística junto ao rio. Em Côja respira fundo e usa o IC6/IC8 para chegar a horas ao almoço.",
    },
    {
        "id": 4,
        "titulo": "Mosteiros, Mar e Muralhas",
        "codigo": "STG-04",
        "data": dt.date(2026, 9, 23),
        "km": 85,
        "min": 95,
        "cor": "#D500F9",
        "cor_rgb": "213, 0, 249",
        "autoestrada": False,
        "terreno": "ROTA COSTEIRA & VILAS HISTÓRICAS",
        "paragens": [
            ("Praia da Vieira", 39.8739013, -8.9693060, "10:00"),
            ("Alcobaça", 39.5503343, -8.9730531, "10:45"),
            ("S. Martinho do Porto", 39.5116589, -9.1342753, "13:00"),
            ("Óbidos", 39.3572399, -9.1578614, "16:00"),
        ],
        "horario": [
            ("10:00", "SAÍDA DA PRAIA DA VIEIRA", "Estrada da Mata Nacional"),
            ("10:45", "ALCOBAÇA // MOSTEIRO", "Túmulos de Pedro e Inês"),
            ("12:30", "DESCIDA PARA A COSTA", "Rumo à Baía"),
            ("13:00", "ALMOÇO: RESTAURANTE CARVALHO", "Peixe fresco na baía"),
            ("15:30", "ARRANQUE PARA ÓBIDOS", "Condução calma"),
            ("16:00", "CHECK-IN DENTRO DAS MURALHAS", "Pátio House"),
            ("20:00", "JANTAR: TASCA TORTA", "Reservado · 2 min na Rua Direita"),
        ],
        "vistas": ["Mosteiro de Alcobaça", "Concha de S. Martinho", "Óbidos medieval iluminada"],
        "comer": [
            {"quando": "Almoço", "nome": "Restaurante Carvalho", "nota": "Peixe / marisco fresco",
             "maps": "Restaurante Carvalho São Martinho do Porto"},
            {"quando": "Jantar 20:00", "nome": "Tasca Torta", "reservado": True, "coords": (39.361444, -9.1575206),
             "a_pe": "~150 m · 2 min a pé na muralha"},
        ],
        "dormir": {"nome": "Óbidos Pátio House", "maps": "Obidos Patio House", "reservado": True},
        "combustivel": [
            {"nome": "Galp — Vieira de Leiria", "coords": (39.8691482, -8.9344074), "nota": "Abastecer antes de sair"},
        ],
        "aviso_combustivel": "Etapa curta com postos regulares ao longo de todo o percurso.",
        "dica": "Etapa relaxada. Atenção ao calçado confortável para caminhar nas pedras de Óbidos.",
    },
    {
        "id": 5,
        "titulo": "Regresso Rápido",
        "codigo": "STG-05",
        "data": dt.date(2026, 9, 24),
        "km": 95,
        "min": 70,
        "cor": "#FF1744",
        "cor_rgb": "255, 23, 68",
        "autoestrada": True,
        "terreno": "AUTOESTRADA A8 // REGRESSO",
        "paragens": [
            ("Óbidos", 39.3572399, -9.1578614, "11:00"),
            ("Cascais", 38.6960614, -9.4303646, "12:15"),
        ],
        "horario": [
            ("11:00", "SAÍDA DESCONTRAÍDA DE ÓBIDOS", "Entrada direta na A8"),
            ("12:15", "CHEGADA A CASCAIS", "Fim da expedição de moto"),
            ("13:00", "ALMOÇO DE ENCERRAMENTO", "Em casa / Costa de Cascais"),
        ],
        "vistas": ["Linha de costa e regresso sem fadiga"],
        "comer": [{"quando": "Almoço", "nome": "Chegada a Cascais"}],
        "dormir": None,
        "combustivel": [],
        "aviso_combustivel": "Áreas de serviço frequentes na A8.",
        "dica": "Tirada rápida em autoestrada. Condução defensiva na aproximação a Lisboa.",
    },
]
DIA = {d["id"]: d for d in DIAS}

# ==============================================================================
# CSS DISRUPTIVO // TFT COCKPIT & RALLY ROADBOOK HUD
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700;800&display=swap');

/* RESET TOTAL E CORES CYBER-TACTICAL */
:root {
  --hud-bg: #07090E;
  --hud-card: #0F131C;
  --hud-card-sub: #161C28;
  --hud-border: #1E2638;
  --hud-tx: #F8FAFC;
  --hud-mut: #64748B;
  --hud-cyan: #00D2FF;
  --hud-orange: #FF6B00;
  --hud-green: #00E676;
  --hud-red: #FF1744;
  --hud-amber: #FFB300;
}

/* Ocultar elementos padrão do Streamlit */
#MainMenu, footer, header, div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] {
  display: none !important;
}

html, body, [data-testid="stAppViewContainer"] {
  background-color: var(--hud-bg) !important;
  color: var(--hud-tx) !important;
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}

.block-container {
  padding: 0.35rem 0.5rem 4rem !important;
  max-width: 650px !important;
}

/* TOP STATUS BAR ESTILO INSTRUMENTO DE BORDO */
.hud-telemetry-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(15, 19, 28, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid var(--hud-border);
  border-radius: 14px;
  padding: 8px 14px;
  margin-bottom: 12px;
}
.hud-beacon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #00E676;
}
.hud-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00E676;
  box-shadow: 0 0 10px #00E676;
  animation: pulseBeacon 1.6s infinite;
}
@keyframes pulseBeacon {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}

/* CARTÃO TFT DISRUPTIVO // HERO DA ETAPA */
.tft-hero {
  background: radial-gradient(140% 100% at 50% 0%, rgba(var(--c-rgb), 0.14) 0%, rgba(15, 19, 28, 0.95) 70%);
  border: 1px solid rgba(var(--c-rgb), 0.45);
  box-shadow: 0 10px 30px -10px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.1);
  border-radius: 22px;
  padding: 20px 18px;
  position: relative;
  overflow: hidden;
  margin-bottom: 12px;
}
.tft-hero::after {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, transparent, var(--c), transparent);
}

.tft-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--c);
  background: rgba(var(--c-rgb), 0.12);
  border: 1px solid rgba(var(--c-rgb), 0.35);
  padding: 3px 9px;
  border-radius: 8px;
  display: inline-block;
}

.tft-title {
  font-size: 1.6rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin: 8px 0 2px;
  color: #FFFFFF;
}

.tft-route-strip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--hud-mut);
  letter-spacing: 0.02em;
  margin-bottom: 14px;
}

/* PAINEL DE TELEMETRIA (TRIPMASTER GAUGE) */
.tft-gauge-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.1fr;
  gap: 8px;
  margin-top: 12px;
}
.tft-gauge-box {
  background: rgba(22, 28, 40, 0.7);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 10px 8px;
  text-align: center;
}
.tft-gauge-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem;
  font-weight: 900;
  color: #FFFFFF;
  line-height: 1;
}
.tft-gauge-lbl {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--hud-mut);
  margin-top: 4px;
  display: block;
}

/* BOTÕES GIGANTES DE NAVEGAÇÃO TÁTICA (LUVA READY) */
.tactical-nav-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 16px;
}
.btn-tactical {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 56px;
  border-radius: 16px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 900;
  font-size: 0.95rem;
  letter-spacing: 0.02em;
  text-decoration: none !important;
  text-align: center;
  box-shadow: 0 6px 20px rgba(0,0,0,0.4);
  transition: transform 0.12s ease;
}
.btn-tactical:active {
  transform: scale(0.97);
}
.btn-gmaps-tactical {
  background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
  color: #FFFFFF !important;
  border: 1px solid #3B82F6;
}
.btn-waze-tactical {
  background: linear-gradient(135deg, #6D28D9 0%, #8B5CF6 100%);
  color: #FFFFFF !important;
  border: 1px solid #A78BFA;
}

/* RALLY ROADBOOK STYLE // LINHA DO TEMPO */
.roadbook-card {
  background: var(--hud-card);
  border: 1px solid var(--hud-border);
  border-radius: 20px;
  padding: 16px 14px;
  margin-bottom: 12px;
}
.roadbook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--hud-border);
}
.roadbook-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--hud-mut);
  text-transform: uppercase;
}

.roadbook-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 12px;
  transition: background 0.15s;
}
.roadbook-row + .roadbook-row {
  border-top: 1px solid rgba(255,255,255,0.04);
}
.roadbook-time {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 0.95rem;
  color: var(--hud-cyan);
  min-width: 48px;
}
.roadbook-now {
  background: rgba(var(--c-rgb), 0.12) !important;
  border-left: 3px solid var(--c) !important;
}
.roadbook-now .roadbook-time {
  color: #FFFFFF !important;
}
.badge-now {
  background: var(--c);
  color: #000;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 900;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 5px;
  margin-left: 6px;
}

/* METEOROLOGIA CLUSTER */
.wx-cluster {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 6px;
  -webkit-overflow-scrolling: touch;
}
.wx-tile {
  flex: 0 0 108px;
  background: var(--hud-card-sub);
  border: 1px solid var(--hud-border);
  border-radius: 14px;
  padding: 10px 8px;
  text-align: center;
}
.wx-loc {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.78rem;
  font-weight: 800;
  color: #FFFFFF;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wx-temp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.35rem;
  font-weight: 900;
  color: var(--hud-cyan);
  margin: 4px 0;
}
.wx-sub {
  font-size: 0.68rem;
  color: var(--hud-mut);
  font-family: 'JetBrains Mono', monospace;
}

/* ALERTA CRÍTICO ESTILO COCKPIT WARNING */
.hazard-alert {
  background: rgba(255, 107, 0, 0.12);
  border: 1px solid rgba(255, 107, 0, 0.5);
  border-left: 5px solid #FF6B00;
  border-radius: 14px;
  padding: 12px 14px;
  color: #FFD8A8;
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1.45;
  margin-top: 10px;
}

/* PARAGENS E ITENS DE DORMIR / COMER */
.tactical-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}
.tactical-item + .tactical-item {
  border-top: 1px solid rgba(255,255,255,0.06);
}
.btn-pill-ir {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--hud-card-sub);
  border: 1px solid var(--hud-border);
  color: var(--hud-cyan) !important;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 10px;
  text-decoration: none !important;
}

/* CUSTOM STREAMLIT BUTTONS & WIDGETS */
.stButton button, .stDownloadButton button {
  width: 100% !important;
  min-height: 52px !important;
  border-radius: 16px !important;
  background: var(--hud-card-sub) !important;
  border: 1px solid var(--hud-border) !important;
  color: #FFFFFF !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 800 !important;
  font-size: 0.95rem !important;
  box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
  transition: transform 0.1s ease !important;
}
.stButton button:active {
  transform: scale(0.98) !important;
}

/* SEGMENTED CONTROL / RADIO ESTILO TFT SELECTOR */
div[data-testid="stSegmentedControl"] {
  background: var(--hud-card) !important;
  border: 1px solid var(--hud-border) !important;
  border-radius: 16px !important;
  padding: 4px !important;
}
div[data-testid="stSegmentedControl"] button {
  min-height: 42px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.78rem !important;
  font-weight: 800 !important;
  border-radius: 12px !important;
  border: 0 !important;
}

div[data-testid="stForm"] {
  background: var(--hud-card) !important;
  border: 1px solid var(--hud-border) !important;
  border-radius: 20px !important;
  padding: 18px !important;
}
div[data-testid="stFormSubmitButton"] button {
  background: linear-gradient(135deg, var(--c, #00D2FF) 0%, rgba(var(--c-rgb, 0,210,255), 0.8) 100%) !important;
  color: #07090E !important;
  font-weight: 900 !important;
  border: 0 !important;
}
</style>
""", unsafe_allow_html=True)


def html(s):
    st.markdown("".join(linha.strip() for linha in s.splitlines()), unsafe_allow_html=True)


# ==============================================================================
# UTILITÁRIOS DE HORA E COORDENADAS
# ==============================================================================
def agora():
    teste = st.query_params.get("agora")
    if teste:
        try:
            return dt.datetime.fromisoformat(teste).replace(tzinfo=TZ)
        except ValueError:
            pass
    return dt.datetime.now(TZ)


def hm(s):
    return dt.time.fromisoformat(s)


def fmt_min(m):
    return f"{m // 60}H{m % 60:02d}" if m % 60 else f"{m // 60}H"


def fmt_data(d, curto=False):
    if curto:
        return f"{DIAS_SEMANA[d.weekday()]} {d.day}"
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} {MESES[d.month - 1]}"


def gmaps_rota(paragens):
    o, *meio, f = paragens
    url = f"https://www.google.com/maps/dir/?api=1&origin={o[1]},{o[2]}&destination={f[1]},{f[2]}&travelmode=driving"
    if meio:
        url += "&waypoints=" + "|".join(f"{p[1]},{p[2]}" for p in meio)
    return url


def gmaps_ir(lat, lon, modo="driving"):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode={modo}&dir_action=navigate"


def waze_ir(lat, lon):
    return f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"


def gmaps_pesquisa(q):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def gerar_gpx(dias):
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<gpx version="1.1" creator="RallyRoadbookMoto" xmlns="http://www.topografix.com/GPX/1/1">']
    for d in dias:
        nome_rota = escape(f"STAGE {d['id']} - {d['titulo']}")
        linhas.append(f"<rte><name>{nome_rota}</name>")
        for nome, lat, lon, _ in d["paragens"]:
            linhas.append(f'<rtept lat="{lat}" lon="{lon}"><name>{escape(nome)}</name></rtept>')
        linhas.append("</rte>")
    linhas.append("</gpx>")
    return "\n".join(linhas)


# ==============================================================================
# TELEMETRIA METEOROLÓGICA (OPENWEATHER + OPEN-METEO FALLBACK)
# ==============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(lat, lon, quando):
    if WEATHER_KEY:
        try:
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={"lat": lat, "lon": lon, "appid": WEATHER_KEY, "units": "metric", "lang": "pt"},
                timeout=5
            )
            if r.ok:
                items = r.json().get("list", [])
                alvo = quando.timestamp()
                prox = min(items, key=lambda i: abs(i["dt"] - alvo))
                vento = prox.get("wind", {})
                return {
                    "temp": round(prox["main"]["temp"]),
                    "pop": round(prox.get("pop", 0) * 100),
                    "vento": round(vento.get("speed", 0) * 3.6),
                    "desc": prox["weather"][0]["description"].capitalize()
                }
        except Exception:
            pass

    # Open-Meteo zero-key fallback
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m&forecast_days=7&timezone=auto"
        r = requests.get(url, timeout=5)
        if r.ok:
            data = r.json().get("hourly", {})
            h = min(quando.hour, len(data.get("temperature_2m", [])) - 1)
            return {
                "temp": round(data["temperature_2m"][h]),
                "pop": round(data.get("precipitation_probability", [0])[h]),
                "vento": round(data.get("wind_speed_10m", [15])[h]),
                "desc": "Condição Estável"
            }
    except Exception:
        pass
    return None


# ==============================================================================
# MAPA TÁTICO FOLIUM
# ==============================================================================
def mostrar_mapa(dias, foco, altura=380):
    m = folium.Map(location=[39.8, -8.5], zoom_start=8, control_scale=True, tiles="CartoDB dark_matter")
    plugins.Fullscreen(position="topright").add_to(m)
    todos = []

    for d in dias:
        linha_pts = [[p[1], p[2]] for p in d["paragens"]]
        folium.PolyLine(
            linha_pts, color=d["cor"], weight=6 if foco else 3.5, opacity=0.95,
            tooltip=f"{d['codigo']} · {d['titulo']}"
        ).add_to(m)
        todos += linha_pts

        for i, (nome, lat, lon, hora) in enumerate(d["paragens"]):
            if not foco and i == 0 and d["id"] > 1:
                continue
            ponta = (i == 0 or i == len(d["paragens"]) - 1)
            folium.CircleMarker(
                location=[lat, lon],
                radius=8 if ponta else 5,
                color="#FFFFFF",
                weight=2,
                fill=True,
                fill_color=d["cor"],
                fill_opacity=1.0,
                popup=f"<div style='font-family:sans-serif;'><b>{escape(nome)}</b><br>{d['codigo']} · ~{hora}<br><a href='{gmaps_ir(lat, lon)}' target='_blank'>Navegar</a></div>"
            ).add_to(m)

        for c in d.get("combustivel", []):
            folium.CircleMarker(
                location=c["coords"], radius=5, color="#000", fill=True, fill_color="#FFB300", fill_opacity=1.0,
                popup=f"⛽ <b>{escape(c['nome'])}</b><br>{escape(c['nota'])}"
            ).add_to(m)

    if todos:
        lats = [p[0] for p in todos]
        lons = [p[1] for p in todos]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(25, 25))

    st_folium(m, use_container_width=True, height=altura, returned_objects=[], key=f"map_{foco or 0}")


# ==============================================================================
# DIÁRIO DE BORDO SUPABASE
# ==============================================================================
def rpc(funcao, dados):
    if not (SUPA_URL and SUPA_KEY):
        return False, "Sem credenciais Supabase configuradas."
    try:
        r = requests.post(
            f"{SUPA_URL}/rest/v1/rpc/{funcao}", json=dados, timeout=20,
            headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json"}
        )
        if r.ok:
            return True, r.json()
        return False, r.text
    except Exception as e:
        return False, str(e)


def comprimir(ficheiro, lado=1400, qualidade=80):
    img = Image.open(ficheiro)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((lado, lado))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=qualidade, optimize=True)
    return buf.getvalue()


def bloco_diario(d, cor):
    if not (SUPA_URL and SUPA_KEY):
        return

    codigo = st.session_state.get("diario_codigo")
    if not codigo:
        html(f"""
        <div class="roadbook-card" style="border-top:3px solid {cor};">
          <div class="roadbook-header">
            <span class="roadbook-title">🔒 LOGBOOK ENCRYPTED</span>
            <span class="tft-badge" style="color:{cor};">SUPABASE</span>
          </div>
          <div style="color:var(--hud-mut); font-size:0.85rem; margin-bottom:12px;">
            Insere a chave de acesso para sincronizar notas e telemetria da rota.
          </div>
        </div>
        """)
        with st.form("auth_form"):
            c = st.text_input("Código de acesso", type="password", placeholder="••••••••", label_visibility="collapsed")
            if st.form_submit_button("⚡ DESBLOQUEAR LOGBOOK") and c:
                ok, _ = rpc("roadlog_notas", {"p_codigo": c, "p_dia": 1})
                if ok:
                    st.session_state["diario_codigo"] = c
                    st.rerun()
                st.error("Chave inválida.")
        return

    ok_n, notas = rpc("roadlog_notas", {"p_codigo": codigo, "p_dia": d["id"]})
    ok_f, fotos = rpc("roadlog_fotos", {"p_codigo": codigo, "p_dia": d["id"]})
    n_notas = len(notas) if ok_n else 0
    n_fotos = len(fotos) if ok_f else 0

    html(f"""
    <div class="roadbook-card">
      <div class="roadbook-header">
        <span class="roadbook-title">ROAD LOG // {d['codigo']}</span>
        <span class="tft-badge" style="color:{cor};">📝 {n_notas} · 📷/🎥 {n_fotos}</span>
      </div>
    </div>
    """)

    with st.form(f"note_entry_{d['id']}", clear_on_submit=True):
        cat = st.selectbox(
            "Categoria",
            ["⛽ Abastecimento", "☕ Paragem / Café", "🍽️ Almoço / Jantar", "📸 Ponto Alto", "⚠️ Alerta de Estrada", "📝 Nota Livre"],
            label_visibility="collapsed"
        )
        txt = st.text_area("Nota de Estrada", placeholder="Registo de telemetria, piso, consumo, ocorrências...", label_visibility="collapsed", height=75)
        autor = st.text_input("Piloto", value=st.session_state.get("autor", ""), placeholder="Piloto (opcional)", label_visibility="collapsed")

        if st.form_submit_button("⚡ GRAVAR NO LOGBOOK") and txt.strip():
            st.session_state["autor"] = autor
            ok, err = rpc("roadlog_nota_criar", {
                "p_codigo": codigo, "p_dia": d["id"],
                "p_texto": f"{cat} // {txt.strip()}", "p_autor": autor.strip()
            })
            if ok:
                st.rerun()
            st.error(f"Erro: {err}")

    # Upload de Fotos & Vídeos
    MEDIA_VID_EXTS = ('.mp4', '.mov', '.webm', '.m4v', '.avi')
    up = st.file_uploader(
        "Fotos & Vídeos",
        type=["jpg", "jpeg", "png", "webp", "heic", "mp4", "mov", "webm", "m4v"],
        accept_multiple_files=True,
        key=f"u_{d['id']}_{st.session_state.get('up_count', 0)}",
        label_visibility="collapsed"
    )
    if up and st.button(f"📷/🎥 CARREGAR {len(up)} FICHEIRO(S)", key=f"btn_up_{d['id']}"):
        prog = st.progress(0.0)
        falhas = []
        for i, f in enumerate(up, 1):
            fname = f.name.lower()
            is_vid = fname.endswith(MEDIA_VID_EXTS)
            try:
                if is_vid:
                    mime = f.type or "video/mp4"
                    dados = f.read()
                else:
                    mime = "image/jpeg"
                    dados = comprimir(f)

                ok, err = rpc("roadlog_foto_criar", {
                    "p_codigo": codigo, "p_dia": d["id"],
                    "p_dados": base64.b64encode(dados).decode(),
                    "p_mime": mime, "p_legenda": f.name[:60],
                    "p_autor": st.session_state.get("autor", "")
                })
                if not ok:
                    falhas.append(f"{f.name} ({err})")
            except Exception as ex:
                falhas.append(f"{f.name} ({ex})")
            prog.progress(i / len(up))

        st.session_state["up_count"] = st.session_state.get("up_count", 0) + 1
        if falhas:
            st.error(f"Erro no envio: {', '.join(falhas)}")
        else:
            st.rerun()

    # Galeria de Fotos e Vídeos
    if n_fotos:
        html('<div class="roadbook-title" style="margin:14px 0 8px;">GALERIA // FOTOS & VÍDEOS</div>')
        cols = st.columns(2)
        for i, f in enumerate(fotos):
            b = foto_bytes(f["id"], codigo)
            if not b:
                continue
            legenda = f.get("legenda", "")
            mime = f.get("mime", "")
            is_vid = (
                mime.startswith("video") or
                legenda.lower().endswith(MEDIA_VID_EXTS) or
                (len(b) > 8 and (b[4:8] == b'ftyp' or b[:4] == b'RIFF' or b[:4] == b'\x1a\x45\xdf\xa3'))
            )
            col = cols[i % 2]
            hora_f = f.get("criado_em", "")[11:16]
            if is_vid:
                col.video(b, format=mime or "video/mp4")
                col.caption(f"🎥 {hora_f} · {legenda[:20]}")
            else:
                col.image(b, caption=f"📷 {hora_f} · {legenda[:20]}", use_container_width=True)

    # Feed de Notas
    for n in (notas if ok_n else []):
        hora = n["criado_em"][11:16]
        quem = f" · {escape(n['autor'])}" if n.get("autor") else ""
        html(f"""
        <div style="background:var(--hud-card-sub); border:1px solid var(--hud-border); border-radius:14px; padding:12px; margin-bottom:8px;">
          <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--hud-cyan); font-weight:700;">
            {hora}{quem}
          </div>
          <div style="font-size:0.9rem; color:#F8FAFC; margin-top:3px; line-height:1.4;">
            {escape(n['texto'])}
          </div>
        </div>
        """)


# ==============================================================================
# PÁGINA DA ETAPA (TFT COCKPIT & ROADBOOK)
# ==============================================================================
def pagina_etapa(d, now):
    cor = d["cor"]
    cor_rgb = d["cor_rgb"]
    st.markdown(f"<style>:root{{--c:{cor}; --c-rgb:{cor_rgb};}}</style>", unsafe_allow_html=True)
    hoje = now.date() == d["data"]
    destino = d["paragens"][-1]

    # --- TFT HERO CARD (COCKPIT DASHBOARD)
    html(f"""
    <div class="tft-hero">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="tft-badge">{d['codigo']} · {d['terreno']}</span>
        {'<span class="badge-now" style="animation:pulseBeacon 1.5s infinite;">HOJE</span>' if hoje else ''}
      </div>
      <div class="tft-title">{d['titulo']}</div>
      <div class="tft-route-strip">{' ➔ '.join(p[0].upper() for p in d['paragens'])}</div>
      
      <div class="tft-gauge-grid">
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">{d['km']} <span style="font-size:0.75rem;color:var(--hud-cyan)">KM</span></div>
          <span class="tft-gauge-lbl">DISTÂNCIA</span>
        </div>
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">{fmt_min(d['min'])}</div>
          <span class="tft-gauge-lbl">CONDUÇÃO</span>
        </div>
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">{len(d['paragens'])}</div>
          <span class="tft-gauge-lbl">WAYPOINTS</span>
        </div>
      </div>

      <div class="tactical-nav-grid">
        <a class="btn-tactical btn-gmaps-tactical" href="{gmaps_rota(d['paragens'])}" target="_blank">
          🧭 GOOGLE MAPS
        </a>
        <a class="btn-tactical btn-waze-tactical" href="{waze_ir(destino[1], destino[2])}" target="_blank">
          ⚡ ABRIR WAZE
        </a>
      </div>
    </div>
    """)

    # --- CLUSTER METEOROLÓGICO RALLY
    tiles = []
    alertas = []
    for nome, lat, lon, hora in d["paragens"]:
        w = get_weather(lat, lon, dt.datetime.combine(d["data"], hm(hora), TZ))
        if w:
            tiles.append(f"""
            <div class="wx-tile">
              <div class="wx-loc">{nome}</div>
              <div class="wx-sub">{hora}</div>
              <div class="wx-temp">{w['temp']}°C</div>
              <div class="wx-sub">💧 {w['pop']}% · 💨 {w['vento']}KPH</div>
            </div>
            """)
            if w["pop"] >= 40:
                alertas.append(f"🌧️ Probabilidade de chuva em {nome} ({w['pop']}%) — Fato de chuva preparado.")
            if w["vento"] >= 40:
                alertas.append(f"💨 Rajadas de vento forte em {nome} ({w['vento']} km/h).")
        else:
            tiles.append(f"""
            <div class="wx-tile">
              <div class="wx-loc">{nome}</div>
              <div class="wx-sub">{hora}</div>
              <div class="wx-temp">--</div>
              <div class="wx-sub">SEM SINAL</div>
            </div>
            """)

    alerta_html = "".join(f"<div class='hazard-alert'>{a}</div>" for a in set(alertas))
    html(f"""
    <div class="roadbook-card">
      <div class="roadbook-header">
        <span class="roadbook-title">METEO TELEMETRY // STAGE WAYPOINTS</span>
        <span class="tft-badge">SATÉLITE</span>
      </div>
      <div class="wx-cluster">{''.join(tiles)}</div>
      {alerta_html}
    </div>
    """)

    # --- RALLY ROADBOOK (HORÁRIO DINÂMICO)
    atual = -1
    if hoje:
        atual = max((i for i, h in enumerate(d["horario"]) if hm(h[0]) <= now.time()), default=-1)

    itens = []
    for i, (hora, txt, det) in enumerate(d["horario"]):
        cls = "roadbook-now" if (hoje and i == atual) else ""
        badge = '<span class="badge-now">AGORA</span>' if (hoje and i == atual) else ""
        if hoje and atual == -1 and i == 0:
            badge = '<span class="badge-now" style="background:#00E676;">PRÓXIMO</span>'

        det_html = f"<div style='font-size:0.75rem; color:var(--hud-mut); font-family:monospace; margin-top:2px;'>{det}</div>" if det else ""
        itens.append(f"""
        <div class="roadbook-row {cls}">
          <div class="roadbook-time">{hora}</div>
          <div style="flex:1;">
            <div style="font-weight:800; font-size:0.85rem; color:#FFFFFF;">{txt} {badge}</div>
            {det_html}
          </div>
        </div>
        """)

    html(f"""
    <div class="roadbook-card">
      <div class="roadbook-header">
        <span class="roadbook-title">RALLY ROADBOOK // TIMELINE</span>
        <span class="tft-badge">{len(d['horario'])} ENTRADAS</span>
      </div>
      {''.join(itens)}
    </div>
    """)

    # --- ALERTA DE COMBUSTÍVEL SE APLICÁVEL
    if d.get("aviso_combustivel"):
        html(f"<div class='hazard-alert'>{d['aviso_combustivel']}</div>")

    # --- DORMIR & COMER (LOGÍSTICA)
    blocos = []
    if d["dormir"]:
        dm = d["dormir"]
        blocos.append(f"""
        <div class="tactical-item">
          <div>
            <div style="font-weight:800; font-size:0.85rem; color:#FFFFFF;">🛏️ {dm['nome']}</div>
            <div style="color:#00E676; font-size:0.72rem; font-family:monospace; font-weight:700;">CONFIRMADO // RESERVA EFETUADA</div>
          </div>
          <a class="btn-pill-ir" href="{gmaps_pesquisa(dm['maps'])}" target="_blank">MAPA ➔</a>
        </div>
        """)
    for c in d["comer"]:
        res_txt = " · <span style='color:#00E676;'>RESERVADO</span>" if c.get("reservado") else ""
        pe_txt = f"<div style='color:var(--hud-mut); font-size:0.75rem;'>🚶 {c['a_pe']}</div>" if c.get("a_pe") else ""
        link = ""
        if c.get("coords"):
            link = f"<a class='btn-pill-ir' href='{gmaps_ir(*c['coords'])}' target='_blank'>IR ➔</a>"
        elif c.get("maps"):
            link = f"<a class='btn-pill-ir' href='{gmaps_pesquisa(c['maps'])}' target='_blank'>MAPA ➔</a>"

        blocos.append(f"""
        <div class="tactical-item">
          <div>
            <div style="font-weight:800; font-size:0.85rem; color:#FFFFFF;">🍽️ {c['nome']}{res_txt}</div>
            <div style="color:var(--hud-mut); font-size:0.72rem; font-family:monospace;">{c['quando']}</div>
            {pe_txt}
          </div>
          {link}
        </div>
        """)

    html(f"""
    <div class="roadbook-card">
      <div class="roadbook-header">
        <span class="roadbook-title">LOGÍSTICA // ALOJAMENTO & REFEIÇÕES</span>
        <span class="tft-badge">RESERVAS</span>
      </div>
      {''.join(blocos)}
    </div>
    """)

    # --- DICA DE EQUIPAMENTO
    html(f"""
    <div class="roadbook-card" style="border-left:4px solid var(--c);">
      <div class="roadbook-title" style="margin-bottom:4px;">TACTICAL BRIEFING</div>
      <div style="font-size:0.85rem; font-weight:700; color:#FFFFFF;">🧳 {d['dica']}</div>
    </div>
    """)

    # --- DIÁRIO & LOGS
    bloco_diario(d, cor)

    # --- MAPA
    mostrar_mapa([d], d["id"], 360)
    st.download_button(
        f"⚡ EXPORTAR GPX // {d['codigo']}",
        gerar_gpx([d]),
        file_name=f"{d['codigo']}_viagem_piodao.gpx",
        mime="application/gpx+xml"
    )


# ==============================================================================
# PÁGINA GERAL // RESUMO DA EXPEDIÇÃO
# ==============================================================================
def pagina_geral(now):
    total_km = sum(d["km"] for d in DIAS)
    total_min = sum(d["min"] for d in DIAS)

    html(f"""
    <div class="tft-hero" style="--c:#00D2FF; --c-rgb:0,210,255;">
      <div class="tft-badge">EXPEDIÇÃO CENTRO & XISTO // 2026</div>
      <div class="tft-title">Rally Piódão 2026</div>
      <div class="tft-route-strip">CASCAIS ➔ FÁTIMA ➔ AÇOR ➔ COSTA ➔ ÓBIDOS</div>

      <div class="tft-gauge-grid">
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">{total_km} <span style="font-size:0.75rem;color:var(--hud-cyan)">KM</span></div>
          <span class="tft-gauge-lbl">TOTAL ROTA</span>
        </div>
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">{fmt_min(total_min)}</div>
          <span class="tft-gauge-lbl">ESTRADA</span>
        </div>
        <div class="tft-gauge-box">
          <div class="tft-gauge-val">5</div>
          <span class="tft-gauge-lbl">ETAPAS</span>
        </div>
      </div>
    </div>
    """)

    for d in DIAS:
        html(f"""
        <div class="roadbook-card" style="border-left:4px solid {d['cor']}; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="tft-badge" style="color:{d['cor']};">{d['codigo']} · {fmt_data(d['data'])}</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--hud-cyan); font-weight:800;">{d['km']} KM</span>
          </div>
          <div style="font-size:1.1rem; font-weight:900; color:#FFFFFF; margin:4px 0 2px;">{d['titulo']}</div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--hud-mut);">
            {' ➔ '.join(p[0] for p in d['paragens'])}
          </div>
        </div>
        """)
        st.button(f"ABRIR {d['codigo']} ➔", key=f"open_{d['id']}", on_click=st.session_state.update, kwargs={"dia": d["id"]})

    mostrar_mapa(DIAS, None, 400)
    st.download_button("⚡ DESCARREGAR GPX COMPLETO DA EXPEDIÇÃO", gerar_gpx(DIAS), file_name="expedicao_piodao_completa.gpx", mime="application/gpx+xml")


# ==============================================================================
# EXECUÇÃO & SELETOR DE ETAPAS
# ==============================================================================
now = agora()
if "dia" not in st.session_state:
    st.session_state.dia = next((d["id"] for d in DIAS if d["data"] == now.date()), 0)

# Barra de Telemetria de Topo
html(f"""
<div class="hud-telemetry-bar">
  <div class="hud-beacon">
    <span class="hud-dot"></span>
    <span>RALLY HUD // LIVE</span>
  </div>
  <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:var(--hud-mut); font-weight:700;">
    20-24 SET 2026
  </div>
</div>
""")

opcoes = [0] + [d["id"] for d in DIAS]
def format_selector(i):
    if i == 0:
        return "GERAL"
    d = DIA[i]
    ponto = "● " if d["data"] == now.date() else ""
    return f"{ponto}STG 0{i}"

if hasattr(st, "segmented_control"):
    st.segmented_control("Etapa", opcoes, format_func=format_selector, key="dia", label_visibility="collapsed")
else:
    st.radio("Etapa", opcoes, format_func=format_selector, key="dia", horizontal=True, label_visibility="collapsed")

sel = st.session_state.get("dia") or 0
if sel:
    pagina_etapa(DIA[sel], now)
else:
    pagina_geral(now)
