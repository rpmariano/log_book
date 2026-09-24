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

# ==========================================
# CONFIGURAÇÃO DE PÁGINA & SECRETS
# ==========================================
st.set_page_config(
    page_title="Road Log Moto — Piódão",
    page_icon="🏍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    TZ = ZoneInfo("Europe/Lisbon")
except Exception:
    TZ = dt.timezone(dt.timedelta(hours=1))  # Hora de verão de Portugal continental

WEATHER_KEY = st.secrets.get("OPENWEATHER_KEY", "")
ORS_KEY = st.secrets.get("ORS_KEY", "")
SUPA_URL = st.secrets.get("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = st.secrets.get("SUPABASE_KEY", "")

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# ==========================================
# PLANO DA VIAGEM COMPLETO
# ==========================================
DIAS = [
    {
        "id": 1, "titulo": "Benção e Romance", "data": dt.date(2026, 9, 20), "km": 225, "min": 150,
        "cor": "#2F80ED", "autoestrada": True,
        "paragens": [
            ("Cascais", 38.6960614, -9.4303646, "09:00"),
            ("Fátima", 39.6324, -8.6713, "10:30"),
            ("Coimbra", 40.2033145, -8.4102573, "15:30"),
        ],
        "horario": [
            ("09:00", "Saída de Cascais", "Via A1/A8"),
            ("10:30", "Chegada a Fátima", "Estacionamento"),
            ("11:00", "Missa e Benção dos Capacetes", ""),
            ("13:00", "Almoço em Fátima", ""),
            ("14:30", "Saída rumo a Coimbra", ""),
            ("15:30", "Chegada e check-in", "Passeio na Quinta das Lágrimas"),
            ("20:00", "Jantar no Quebra o Galho", "Reservado · 12 min a pé"),
        ],
        "vistas": ["Santuário de Fátima", "Quinta das Lágrimas", "Alta de Coimbra"],
        "comer": [
            {"quando": "Almoço", "nome": "Em Fátima", "maps": "Restaurantes Fátima"},
            {"quando": "Jantar 20:00", "nome": "Quebra o Galho", "url": "https://www.quebraogalho.com/", "reservado": True,
             "coords": (40.2087486, -8.4282289), "a_pe": "~900 m · 12 min a pé do hotel (atravessa a ponte; sobe na Alta)"},
        ],
        "dormir": {"nome": "Five Senses in Coimbra", "maps": "Five Senses in Coimbra", "reservado": True},
        "combustivel": [], "aviso_combustivel": "Dia de autoestrada: áreas de serviço da A8/A1 ao longo de todo o percurso.",
        "dica": "Tiradas rápidas em autoestrada. Tampões de ouvidos e casaco ventilado.",
    },
    {
        "id": 2, "titulo": "O Refúgio no Xisto", "data": dt.date(2026, 9, 21), "km": 95, "min": 140,
        "cor": "#E67E22", "autoestrada": False,
        "paragens": [
            ("Coimbra", 40.2033145, -8.4102573, "10:30"),
            ("Góis", 40.1572681, -8.1106277, "12:00"),
            ("Fajão", 40.1495149, -7.9222764, "13:30"),
            ("Piódão", 40.2292601, -7.8250288, "16:45"),
        ],
        "horario": [
            ("10:30", "Saída de Coimbra", ""),
            ("12:00", "Chegada a Góis", "Café à beira rio"),
            ("12:30", "Arranque para Fajão", ""),
            ("13:30", "Almoço em Fajão", "O Juiz"),
            ("15:30", "Descida final para a Serra do Açor", ""),
            ("16:45", "Chegada ao Piódão", "Pôr do sol"),
            ("19:00", "Jantar n'O Fontinha", "Reservado · 11 min a pé (levar lanterna)"),
        ],
        "vistas": ["Rio Ceira", "Aldeia de Fajão", "Pôr do sol no Piódão"],
        "comer": [
            {"quando": "Almoço", "nome": "O Juiz (Fajão)", "nota": "Chanfana em forno a lenha", "maps": "O Juiz Fajão"},
            {"quando": "Jantar 19:00", "nome": "O Fontinha (Piódão)", "reservado": True, "coords": (40.2297396, -7.8249356),
             "a_pe": "~850 m · 11 min a pé do hotel (regresso a subir; levar lanterna)"},
        ],
        "dormir": {"nome": "INATEL Piódão Hotel", "maps": "INATEL Piodao Hotel", "reservado": True},
        "combustivel": [
            {"nome": "Galp — Coimbra (saída sul)", "coords": (40.2013031, -8.4086694), "nota": "24/7 · atestar antes de sair"},
            {"nome": "Alves Bandeira — Góis", "coords": (40.1554162, -8.1141220), "nota": "Última bomba prática antes da serra"},
        ],
        "aviso_combustivel": "⛽ Não há bomba no Fajão nem no Piódão. A mais próxima do Piódão fica a ~8 km (Pomares). Sair de Góis com depósito cheio.",
        "dica": "A temperatura desce ao final da tarde no Açor. Forro térmico acessível.",
    },
    {
        "id": 3, "titulo": "O Vale do Alva, Retiro e SPA", "data": dt.date(2026, 9, 22), "km": 175, "min": 165,
        "cor": "#27AE60", "autoestrada": False,
        "paragens": [
            ("Piódão", 40.2292601, -7.8250288, "09:45"),
            ("Vide", 40.295411, -7.784012, "10:30"),
            ("Ponte das Três Entradas", 40.306915, -7.870779, "10:50"),
            ("Côja", 40.256689, -7.990173, "11:20"),
            ("Casal de S. Simão", 39.9163506, -8.3223319, "12:30"),
            ("Praia da Vieira", 39.8739013, -8.9693060, "16:45"),
        ],
        "horario": [
            ("09:45", "Saída do Piódão pela M508", "Direção norte · encosta remota da serra"),
            ("10:30", "Passagem em Vide ➔ Entrada na N230", "Asfalto de sonho colado ao Rio Alva"),
            ("10:50", "Ponte das Três Entradas", "Confluência dos rios · curvas lendárias"),
            ("11:20", "Paragem em Côja (Vale do Alva)", "Secção verdejante · café à beira-rio"),
            ("11:45", "Transição rápida via IC6 / IC8", "Vias rápidas para despachar transição a sul"),
            ("12:30", "Chegada a Casal de S. Simão", "Passeio nos Passadiços antes do almoço"),
            ("13:30", "Almoço com vista para a serra", "Varanda do Casal · Reservado"),
            ("15:30", "Saída em direção à costa (IC8)", "Ligação para o mar"),
            ("16:45", "Chegada à Praia da Vieira", "Direto para o SPA"),
            ("20:00", "Jantar no Nau Frágil", "Reservado · 1 min a pé"),
        ],
        "vistas": ["Estrada M508 (Encosta Norte)", "Curvas da N230 no Rio Alva", "Ponte das Três Entradas", "Passadiços de S. Simão", "Pôr do sol na Praia da Vieira"],
        "comer": [
            {"quando": "Almoço", "nome": "Varanda do Casal (S. Simão)", "maps": "Varanda do Casal Casal de São Simão"},
            {"quando": "Jantar 20:00", "nome": "Nau Frágil", "reservado": True, "coords": (39.875889, -8.971315),
             "a_pe": "~100 m · 1 min a pé do hotel (na Marginal)"},
        ],
        "dormir": {"nome": "Hotel Cristal Vieira Praia & SPA", "maps": "Hotel Cristal Vieira Praia SPA", "reservado": True},
        "combustivel": [
            {"nome": "Alves Bandeira — Côja", "coords": (40.2592, -7.9941), "nota": "Bomba na saída de Côja rumo ao IC6"},
            {"nome": "Intermarché — Figueiró dos Vinhos", "coords": (39.9058098, -8.2807051), "nota": "~8 km de Casal de S. Simão"},
            {"nome": "Galp — Vieira de Leiria", "coords": (39.8691482, -8.9344074), "nota": "~3 km do hotel, à chegada"},
        ],
        "aviso_combustivel": "⛽ Rota do Vale do Alva com bomba conveniente em Côja antes de entrar no IC6.",
        "dica": "A N230 entre Vide e a Ponte das Três Entradas é pura diversão motociclística. Em Côja respira fundo e usa o IC6/IC8 para chegar a horas ao almoço.",
    },
    {
        "id": 4, "titulo": "Mosteiros, Mar e Muralhas", "data": dt.date(2026, 9, 23), "km": 85, "min": 95,
        "cor": "#8E44AD", "autoestrada": False,
        "paragens": [
            ("Praia da Vieira", 39.8739013, -8.9693060, "10:00"),
            ("Alcobaça", 39.5503343, -8.9730531, "10:45"),
            ("S. Martinho do Porto", 39.5116589, -9.1342753, "13:00"),
            ("Óbidos", 39.3572399, -9.1578614, "16:00"),
        ],
        "horario": [
            ("10:00", "Saída da Praia da Vieira", ""),
            ("10:45", "Chegada a Alcobaça", "Túmulos de Pedro e Inês"),
            ("12:30", "Saída para a costa", ""),
            ("13:00", "Almoço em S. Martinho do Porto", "Restaurante Carvalho"),
            ("15:30", "Saída rumo a Óbidos", ""),
            ("16:00", "Chegada e check-in nas muralhas", ""),
            ("20:00", "Jantar na Tasca Torta", "Reservado · 2 min a pé"),
        ],
        "vistas": ["Mosteiro de Alcobaça", "Baía de S. Martinho", "Ruelas noturnas em Óbidos"],
        "comer": [
            {"quando": "Almoço", "nome": "Restaurante Carvalho", "nota": "Peixe fresco / marisco",
             "maps": "Restaurante Carvalho São Martinho do Porto"},
            {"quando": "Jantar 20:00", "nome": "Tasca Torta", "reservado": True, "coords": (39.361444, -9.1575206),
             "a_pe": "~150 m · 2 min a pé do hotel (Rua Direita)"},
        ],
        "dormir": {"nome": "Óbidos Pátio House", "maps": "Obidos Patio House", "reservado": True},
        "combustivel": [
            {"nome": "Galp — Vieira de Leiria", "coords": (39.8691482, -8.9344074), "nota": "~3 km do hotel, antes de arrancar"},
        ],
        "aviso_combustivel": "Etapa curta e com bombas frequentes ao longo da costa.",
        "dica": "Etapa muito curta. Condução relaxada.",
    },
    {
        "id": 5, "titulo": "Regresso Rápido (AE)", "data": dt.date(2026, 9, 24), "km": 95, "min": 70,
        "cor": "#E74C3C", "autoestrada": True,
        "paragens": [
            ("Óbidos", 39.3572399, -9.1578614, "11:00"),
            ("Cascais", 38.6960614, -9.4303646, "12:15"),
        ],
        "horario": [
            ("11:00", "Saída relaxada de Óbidos", "Diretos à A8"),
            ("12:15", "Chegada a Cascais", ""),
            ("13:00", "Almoço de encerramento", "Em casa / na linha"),
        ],
        "vistas": ["Tirada reta para regresso sem fadiga"],
        "comer": [{"quando": "Almoço", "nome": "Chegada a Cascais"}],
        "dormir": None,
        "combustivel": [], "aviso_combustivel": "A8 com áreas de serviço. Atestar só se for preciso.",
        "dica": "Tampões para os ouvidos por causa do vento da autoestrada.",
    },
]
DIA = {d["id"]: d for d in DIAS}

# ==========================================
# CSS MOBILE DE TOPO (COCKPIT DE MOTO & TÁCTIL)
# ==========================================
st.markdown("""
<style>
:root {
  --bg-main: #0B0E14;
  --card: #151A23;
  --tx: #F1F5F9;
  --mut: #94A3B8;
  --line: #232B3A;
  --soft: #1C222E;
  --warn-bg: #351C05;
  --warn-tx: #FDBA74;
  --warn-bd: #8A4305;
  --ok-bg: #0B291B;
  --ok-tx: #86EFAC;
  --ok-bd: #166534;
}
@media (prefers-color-scheme:light){
  :root {
    --bg-main: #F8FAFC;
    --card: #FFFFFF;
    --tx: #0F172A;
    --mut: #475569;
    --line: #E2E8F0;
    --soft: #F1F5F9;
    --warn-bg: #FFFBEB;
    --warn-tx: #B45309;
    --warn-bd: #FCD34D;
    --ok-bg: #F0FDF4;
    --ok-tx: #15803D;
    --ok-bd: #BBF7D0;
  }
}

.block-container {
  padding: 0.5rem 0.75rem 4rem !important;
  max-width: 680px;
}
#MainMenu, footer, header { visibility: hidden; }

/* Cartão Táctil */
.card {
  background: var(--card);
  color: var(--tx);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.12);
}

.hero {
  border-top: 6px solid var(--c, #2F80ED);
}

.eyebrow {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--c, #2F80ED);
}

.title {
  font-size: 1.4rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  line-height: 1.2;
  margin: 4px 0 6px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.chip {
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.82rem;
  font-weight: 700;
}

/* Botões gigantes para luvas */
.btn-nav-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 14px;
}
.btn-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 52px;
  border-radius: 14px;
  font-weight: 800;
  font-size: 0.95rem;
  text-decoration: none !important;
  color: #fff !important;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.btn-gmaps { background: #2563EB; }
.btn-waze { background: #7C3AED; }

.alert {
  border-radius: 14px;
  padding: 12px 14px;
  margin-top: 10px;
  font-weight: 700;
  font-size: 0.88rem;
  background: var(--warn-bg);
  color: var(--warn-tx);
  border: 1px solid var(--warn-bd);
  line-height: 1.4;
}

/* Linha de Tempo com Destaque */
.tl { list-style: none; margin: 0; padding: 0; }
.tl li {
  display: flex;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 12px;
  align-items: flex-start;
}
.tl li + li { border-top: 1px solid var(--line); }
.tl .h { font-family: monospace; font-weight: 800; font-size: 0.95rem; min-width: 46px; }
.tl .now { background: var(--soft); border-left: 4px solid var(--c, #2F80ED); }
.tl .done { opacity: 0.45; }

.tag-now {
  font-size: 0.65rem;
  font-weight: 900;
  background: #2563EB;
  color: #fff;
  border-radius: 6px;
  padding: 2px 6px;
  margin-left: 6px;
}

.stButton button, .stDownloadButton button {
  width: 100%;
  border-radius: 14px;
  min-height: 50px;
  font-weight: 800;
  font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)


def html(s):
    st.markdown("".join(linha.strip() for linha in s.splitlines()), unsafe_allow_html=True)


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
    return f"{m // 60}h{m % 60:02d}" if m % 60 else f"{m // 60}h"


def fmt_data(d, curto=False):
    if curto:
        return f"{DIAS_SEMANA[d.weekday()][:3]} {d.day}"
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} {MESES[d.month - 1]}"


def gmaps_rota(paragens):
    o, *meio, f = paragens
    url = f"https://www.google.com/maps/dir/?api=1&origin={o[1]},{o[2]}&destination={f[1]},{f[2]}&travelmode=driving"
    if meio:
        url += "&waypoints=" + "|".join(f"{p[1]},{p[2]}" for p in meio)
    return url


def waze_ir(lat, lon):
    return f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"


def gmaps_ir(lat, lon):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"


def gerar_gpx(dias):
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<gpx version="1.1" creator="roadlog-moto" xmlns="http://www.topografix.com/GPX/1/1">']
    for d in dias:
        nome_rota = escape("Dia %d - %s" % (d["id"], d["titulo"]))
        linhas.append(f"<rte><name>{nome_rota}</name>")
        for nome, lat, lon, _ in d["paragens"]:
            linhas.append(f'<rtept lat="{lat}" lon="{lon}"><name>{escape(nome)}</name></rtept>')
        linhas.append("</rte>")
    linhas.append("</gpx>")
    return "\n".join(linhas)


# ==========================================
# MAPA FOLIUM
# ==========================================
def mostrar_mapa(dias, foco, altura=380):
    m = folium.Map(location=[39.8, -8.5], zoom_start=8, control_scale=True)
    plugins.Fullscreen(position="topright").add_to(m)
    todos = []

    for d in dias:
        linha_pts = [[p[1], p[2]] for p in d["paragens"]]
        folium.PolyLine(linha_pts, color=d["cor"], weight=6 if foco else 4, opacity=0.9,
                        tooltip=f"Dia {d['id']} · {d['titulo']}").add_to(m)
        todos += linha_pts

        for i, (nome, lat, lon, hora) in enumerate(d["paragens"]):
            folium.CircleMarker(
                location=[lat, lon],
                radius=8 if (i == 0 or i == len(d["paragens"]) - 1) else 6,
                color="#FFFFFF",
                fill=True,
                fill_color=d["cor"],
                fill_opacity=1.0,
                popup=f"<b>{escape(nome)}</b><br>Dia {d['id']} · ~{hora}<br><a href='{gmaps_ir(lat, lon)}' target='_blank'>Navegar</a>"
            ).add_to(m)

    if todos:
        lats = [p[0] for p in todos]
        lons = [p[1] for p in todos]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(25, 25))

    st_folium(m, use_container_width=True, height=altura, returned_objects=[], key=f"map_{foco or 0}")


# ==========================================
# PÁGINA DO DIA
# ==========================================
def pagina_dia(d, now):
    cor = d["cor"]
    hoje = now.date() == d["data"]
    via = "🛣️ Autoestrada" if d["autoestrada"] else "🌄 Curvas & Nacionais"
    tag_hoje = " · <span class='tag-now'>HOJE</span>" if hoje else ""

    # Topo do Dia
    html(f"""
    <div class="card hero" style="--c:{cor}">
      <div class="eyebrow">Dia {d['id']} · {fmt_data(d['data'])}{tag_hoje}</div>
      <div class="title">{d['titulo']}</div>
      <div style="color:var(--mut); font-size:0.92rem; font-weight:600;">{' → '.join(p[0] for p in d['paragens'])}</div>
      <div class="chips">
        <span class="chip">📏 {d['km']} km</span>
        <span class="chip">⏱️ {fmt_min(d['min'])} condução</span>
        <span class="chip">{via}</span>
      </div>
      <div class="btn-nav-grid">
        <a class="btn-nav btn-gmaps" href="{gmaps_rota(d['paragens'])}" target="_blank">🗺️ Google Maps</a>
        <a class="btn-nav btn-waze" href="{waze_ir(d['paragens'][-1][1], d['paragens'][-1][2])}" target="_blank">🚗 Waze</a>
      </div>
    </div>
    """)

    # Aviso Combustível se existir
    if d.get("aviso_combustivel"):
        html(f"<div class='alert'>{escape(d['aviso_combustivel'])}</div>")

    # Horário
    atual = -1
    if hoje:
        atual = max((i for i, h in enumerate(d["horario"]) if hm(h[0]) <= now.time()), default=-1)

    itens = []
    for i, (hora, txt, det) in enumerate(d["horario"]):
        cls = "done" if (hoje and i < atual) else "now" if (hoje and i == atual) else ""
        tag = "<span class='tag-now'>AGORA</span>" if (hoje and i == atual) else ""
        small = f"<div style='color:var(--mut); font-size:0.8rem; margin-top:2px;'>{det}</div>" if det else ""
        itens.append(f"<li class='{cls}'><span class='h'>{hora}</span><div style='flex:1'><b>{txt}</b>{tag}{small}</div></li>")

    html(f"""
    <div class="card" style="--c:{cor}">
      <div class="eyebrow" style="margin-bottom:8px">Horário & Etapas</div>
      <ul class="tl">{''.join(itens)}</ul>
    </div>
    """)

    # Alojamento e Refeições
    blocos = []
    if d["dormir"]:
        dm = d["dormir"]
        blocos.append(f"<div style='padding:8px 0; border-bottom:1px solid var(--line);'>🛏️ <b>{dm['nome']}</b> <span style='color:var(--ok-tx); font-weight:800; font-size:0.75rem;'>✓ Reservado</span></div>")
    for c in d["comer"]:
        res = " <span style='color:var(--ok-tx); font-weight:800; font-size:0.75rem;'>✓ Reservado</span>" if c.get("reservado") else ""
        pe = f"<div style='color:var(--mut); font-size:0.8rem;'>🚶 {c['a_pe']}</div>" if c.get("a_pe") else ""
        blocos.append(f"<div style='padding:8px 0;'>🍽️ <b>{c['nome']}</b> ({c['quando']}){res}{pe}</div>")

    html(f"""
    <div class="card" style="--c:{cor}">
      <div class="eyebrow" style="margin-bottom:6px">Dormir & Comer</div>
      {''.join(blocos)}
    </div>
    """)

    # Dica do Dia
    html(f"""
    <div class="card" style="--c:{cor}">
      <div class="eyebrow">Dica de Equipamento</div>
      <div style="font-size:0.9rem; font-weight:700; margin-top:4px;">🧳 {d['dica']}</div>
    </div>
    """)

    # Mapa Folium da Etapa
    mostrar_mapa([d], d["id"], 360)
    st.download_button(f"⬇️ Descarregar GPX Dia {d['id']}", gerar_gpx([d]), file_name=f"dia{d['id']}.gpx", mime="application/gpx+xml")


# ==========================================
# PÁGINA RESUMO
# ==========================================
def pagina_resumo(now):
    total_km = sum(d["km"] for d in DIAS)
    total_min = sum(d["min"] for d in DIAS)

    html(f"""
    <div class="card hero" style="--c:#2F80ED">
      <div class="eyebrow">Roteiro Completo</div>
      <div class="title">Viagem ao Piódão & Xisto</div>
      <div style="color:var(--mut); font-weight:600;">20 a 24 de Setembro de 2026 · 5 Dias</div>
      <div class="chips">
        <span class="chip">📏 ~{total_km} km</span>
        <span class="chip">⏱️ ~{fmt_min(total_min)} na estrada</span>
        <span class="chip">⛰️ Serra do Açor</span>
      </div>
    </div>
    """)

    for d in DIAS:
        html(f"""
        <div class="card hero" style="--c:{d['cor']}; margin-bottom:8px;">
          <div class="eyebrow">Dia {d['id']} · {fmt_data(d['data'])}</div>
          <div style="font-weight:900; font-size:1.15rem; margin:2px 0;">{d['titulo']}</div>
          <div style="color:var(--mut); font-size:0.85rem;">{' → '.join(p[0] for p in d['paragens'])}</div>
          <div style="font-size:0.82rem; margin-top:4px; font-weight:700;">📏 {d['km']} km · ⏱️ {fmt_min(d['min'])}</div>
        </div>
        """)
        st.button(f"Abrir Cockpit Dia {d['id']} →", key=f"btn_open_{d['id']}", on_click=st.session_state.update, kwargs={"dia": d["id"]})

    mostrar_mapa(DIAS, None, 400)
    st.download_button("⬇️ GPX da Viagem Completa", gerar_gpx(DIAS), file_name="viagem_piodao_completa.gpx", mime="application/gpx+xml")


# ==========================================
# EXECUÇÃO & NAVEGAÇÃO
# ==========================================
now = agora()
if "dia" not in st.session_state:
    st.session_state.dia = next((d["id"] for d in DIAS if d["data"] == now.date()), 0)

html("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
  <span style="font-size:1.25rem; font-weight:900;">🏍️ Road Log Moto</span>
  <span style="font-size:0.82rem; font-weight:700; color:var(--mut);">20–24 Set</span>
</div>
""")

opcoes = [0] + [d["id"] for d in DIAS]
def format_tab(i):
    if i == 0: return "Resumo"
    return f"Dia {i}"

if hasattr(st, "segmented_control"):
    st.segmented_control("Dia", opcoes, format_func=format_tab, key="dia", label_visibility="collapsed")
else:
    st.radio("Dia", opcoes, format_func=format_tab, key="dia", horizontal=True, label_visibility="collapsed")

sel = st.session_state.get("dia") or 0
if sel:
    pagina_dia(DIA[sel], now)
else:
    pagina_resumo(now)
