
import numpy as np
import streamlit as st
import plotly.graph_objects as go


st.set_page_config(page_title="Bench + Barrenos (por barreno)", layout="wide")
st.title("Diseño geométrico de voladura 2D ")

COLORS = {
    "banco_fill": "rgba(120,120,120,0.50)",
    "banco_line": "rgba(0,0,0,0.95)",

    "barreno_fill": "rgba(255,255,255,0.10)",
    "barreno_line": "rgba(0,0,0,0.95)",

    "carga": "rgba(40,120,255,0.90)",
    # Agua con transparencia (75% transparente => alpha=0.25)
    "agua":  "rgba(0,200,255,0.25)",
    "agua_line": "rgba(0,200,255,0.60)",
    "taco":  "rgba(255,150,40,0.92)",
}

# ------------------------ UI (GLOBAL) ------------------------
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.subheader("Parámetros globales")
    colA, colB, colC = st.columns(3)

    with colA:
        h = st.slider("Altura de banco h (m)", 2.0, 30.0, 10.0, 0.5)
        angtalud = st.slider("Ángulo de talud (°)", 30.0, 85.0, 65.0, 0.5)
        base_y = st.slider("Base (offset vertical) (m)", 0.0, 15.0, 5.0, 0.5)

    with colB:
        loninf = st.slider("Longitud de influencia (m)", 5.0, 150.0, 30.0, 1.0)
        burd = st.slider("Burden (m)", 0.5, 15.0, 4.0, 0.1)
        aux = st.slider("Ajuste hacia la cresta aux (m)", 0.0, 10.0, 2.0, 0.1)

    with colC:
        longbase = st.slider("Longitud base estudio (m)", 10.0, 200.0, 50.0, 1.0)
        di = st.slider("Espesor gráfico barreno (m)", 0.05, 2.0, 0.70, 0.05)

st.markdown("---")

# ------------------------ POSICIONES ------------------------
disdif = h / np.tan(np.radians(angtalud)) if np.tan(np.radians(angtalud)) != 0 else 0.0
nbarr = loninf / burd if burd > 0 else 0
nbarrint = int(np.floor(nbarr))

mult = []
for i in range(nbarrint):
    x = loninf - (burd * (i + 1) - aux)
    if x > 0.01:
        mult.append(x)

n = len(mult)
st.info(f"Número de barrenos generados: **{n}**")

# ------------------------ STATE LISTS ------------------------
def ensure_state_list(key, default_value, length):
    if key not in st.session_state or len(st.session_state[key]) != length:
        st.session_state[key] = [default_value for _ in range(length)]

ensure_state_list("lonbar", 11.0, n)
ensure_state_list("lq", 8.0, n)
ensure_state_list("agua", 0.0, n)

# ------------------------ PER-BARRENO SLIDERS ------------------------
with st.expander("Parámetros por barreno (uno por uno)", expanded=True):
    st.caption("El agua es referencia y se sobrepone; no reduce la carga. Taco = lonbar - lq (automático).")
    cols = st.columns(min(4, n) if n > 0 else 1)

    for i in range(n):
        with cols[i % len(cols)]:
            st.markdown(f"### Barreno {i+1}")

            lonbar_i = st.slider(
                f"L barreno (m) — #{i+1}", 1.0, 50.0, float(st.session_state["lonbar"][i]), 0.5,
                key=f"lonbar_{i}"
            )
            lq_i = st.slider(
                f"L carga (m) — #{i+1}", 0.0, float(lonbar_i), float(min(st.session_state["lq"][i], lonbar_i)), 0.5,
                key=f"lq_{i}"
            )
          
            agua_i = st.slider(
                f"L agua (m) — #{i+1}", 0.0, float(lonbar_i), float(min(st.session_state["agua"][i], lonbar_i)), 0.5,
                key=f"agua_{i}"
            )

            st.session_state["lonbar"][i] = lonbar_i
            st.session_state["lq"][i] = lq_i
            st.session_state["agua"][i] = agua_i

            taco_i = max(lonbar_i - lq_i, 0.0)
            st.write(f"**Taco (auto):** {taco_i:.2f} m")

# ------------------------ DIM CONTROLS ------------------------
st.subheader("Opciones de visualización")
colV1, colV2, colV3 = st.columns([1.2, 2.2, 1.6])

with colV1:
    show_dims = st.checkbox("Mostrar cotas", value=True)
with colV2:
    dims_what = st.multiselect(
        "Qué cotas mostrar",
        options=["Banco", "Barreno", "Carga", "Agua", "Taco", "Pie de talud"],
        default=["Banco", "Carga", "Agua", "Taco", "Pie de talud"] if show_dims else []
    )
with colV3:
    sel = st.multiselect(
        "Cotas por barreno (selecciona cuáles)",
        options=[f"#{i+1}" for i in range(n)],
        default=[f"#{i+1}" for i in range(min(n, 2))]
    )
    sel_idx = {int(s.replace("#",""))-1 for s in sel}

# ------------------------ FIGURE ------------------------
fig = go.Figure()

def add_rect(x0, x1, y0, y1, fillcolor, linecolor,
             legendgroup=None, name=None, showlegend=False):
    fig.add_trace(go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y1, y1, y0, y0, y1],
        mode="lines",
        fill="toself",
        fillcolor=fillcolor,
        line=dict(color=linecolor, width=1),
        hoverinfo="skip",
        legendgroup=legendgroup,
        name=name,
        showlegend=showlegend,
    ))

def dim_v(x, y0, y1, text, tag="", dash="dash"):
    fig.add_shape(type="line", x0=x, y0=y0, x1=x, y1=y1,
                  line=dict(width=2, dash=dash, color="black"))
    fig.add_shape(type="line", x0=x-0.35, y0=y0, x1=x+0.35, y1=y0,
                  line=dict(width=2, color="black"))
    fig.add_shape(type="line", x0=x-0.35, y0=y1, x1=x+0.35, y1=y1,
                  line=dict(width=2, color="black"))
    fig.add_annotation(
        x=x-0.85, y=(y0+y1)/2, text=f"{text}{tag}",
        showarrow=False, textangle=-90,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(0,0,0,0.25)", borderwidth=1
    )


def dim_h(y, x0, x1, text, dash="dash", color="black"):
    fig.add_shape(type="line", x0=x0, y0=y, x1=x1, y1=y,
                  line=dict(width=2, dash=dash, color=color))
    fig.add_shape(type="line", x0=x0, y0=y-0.2, x1=x0, y1=y+0.2,
                  line=dict(width=2, color=color))
    fig.add_shape(type="line", x0=x1, y0=y-0.2, x1=x1, y1=y+0.2,
                  line=dict(width=2, color=color))
    fig.add_annotation(
        x=(x0+x1)/2, y=y+0.35, text=text,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(0,0,0,0.25)", borderwidth=1
    )


# ------------------------ BANCO ------------------------
bench_coordinates = [
    (0, 0),
    (0, base_y + h),
    (loninf, base_y + h),
    (loninf + disdif, base_y),
    (longbase, base_y),
    (longbase, 0),
    (0, 0),
]
bx, by = zip(*bench_coordinates)
fig.add_trace(go.Scatter(
    x=bx, y=by, mode="lines", fill="toself",
    name="Banco",
    fillcolor=COLORS["banco_fill"],
    line=dict(color=COLORS["banco_line"], width=2),
    legendgroup="banco",
    showlegend=True
))

# ------------------------ ÁNGULO DE TALUD  ------------------------
ang_cx, ang_cy = loninf + disdif, base_y
R = max(1.5, 0.18 * h)
theta = np.linspace(0, np.radians(angtalud), 60)

arc_x = ang_cx - R * np.cos(theta)
arc_y = ang_cy + R * np.sin(theta)

fig.add_trace(go.Scatter(
    x=arc_x,
    y=arc_y,
    mode="lines",
    line=dict(width=2, dash="dot", color="rgba(220,0,0,0.95)"),
    name="Ángulo talud",
    legendgroup="angulo",
    showlegend=True,
    hoverinfo="skip"
))

# Texto del ángulo fuera del arco + "pill" de fondo
t_mid = np.radians(angtalud * 0.55)
R_txt = R * 1.25
txt_x = ang_cx - R_txt * np.cos(t_mid)
txt_y = ang_cy + R_txt * np.sin(t_mid)

fig.add_trace(go.Scatter(
    x=[txt_x],
    y=[txt_y],
    mode="markers",
    marker=dict(
        symbol="square",
        size=18,
        color="rgba(255,255,255,0.85)",
        line=dict(width=1, color="rgba(0,0,0,0.25)")
    ),
    legendgroup="angulo",
    showlegend=False,
    hoverinfo="skip"
))

fig.add_trace(go.Scatter(
    x=[txt_x],
    y=[txt_y],
    mode="text",
    text=[f"{angtalud:.1f}°"],
    textposition="middle center",
    legendgroup="angulo",
    showlegend=False,
    textfont=dict(size=13, color="rgba(220,0,0,0.95)"),
    hoverinfo="skip"
))

# Flags para que cada grupo aparezca una sola vez en leyenda
first_barreno = True
first_carga = True
first_agua = True
first_taco = True

# acumuladores numeración
label_x, label_y, label_text = [], [], []

# ------------------------ BARRENOS ------------------------
y_top = base_y + h

for i, x in enumerate(mult):
    lonbar_i = float(st.session_state["lonbar"][i])
    lq_i = float(st.session_state["lq"][i])
    agua_i = float(st.session_state["agua"][i])
    taco_i = max(lonbar_i - lq_i, 0.0)

    x0, x1 = x - di/2, x + di/2
    y_bottom = y_top - lonbar_i

    # Barreno
    add_rect(
        x0, x1, y_bottom, y_top,
        fillcolor=COLORS["barreno_fill"],
        linecolor=COLORS["barreno_line"],
        legendgroup="barreno",
        name="Barreno" if first_barreno else None,
        showlegend=first_barreno
    )
    first_barreno = False

    # Carga completa
    if lq_i > 0:
        add_rect(
            x0, x1, y_bottom, y_bottom + lq_i,
            fillcolor=COLORS["carga"],
            linecolor=COLORS["carga"],
            legendgroup="carga",
            name="Carga (explosivo)" if first_carga else None,
            showlegend=first_carga
        )
        first_carga = False

    # Taco
    if taco_i > 0:
        add_rect(
            x0, x1, y_bottom + lq_i, y_top,
            fillcolor=COLORS["taco"],
            linecolor=COLORS["taco"],
            legendgroup="taco",
            name="Taco" if first_taco else None,
            showlegend=first_taco
        )
        first_taco = False

    # Agua overlay
    if agua_i > 0:
        add_rect(
            x0, x1, y_bottom, y_bottom + agua_i,
            fillcolor=COLORS["agua"],
            linecolor=COLORS["agua_line"],
            legendgroup="agua",
            name="Agua" if first_agua else None,
            showlegend=first_agua
        )
        first_agua = False

    # numeración
    label_x.append(x)
    label_y.append((y_top + y_bottom) / 2)
    label_text.append(str(i + 1))

    # cotas por barreno
    if show_dims and (i in sel_idx):
        xdim = x + di + 0.9
        if "Barreno" in dims_what:
            dim_v(xdim, y_bottom, y_top, f"L barreno = {lonbar_i:.2f} m", tag=f"  (#{i+1})")
        if "Agua" in dims_what and agua_i > 0:
            dim_v(xdim + 1.1, y_bottom, y_bottom + agua_i, f"Agua = {agua_i:.2f} m", tag=f"  (#{i+1})")
        if "Carga" in dims_what and lq_i > 0:
            dim_v(xdim + 2.2, y_bottom, y_bottom + lq_i, f"Carga = {lq_i:.2f} m", tag=f"  (#{i+1})")
        if "Taco" in dims_what and taco_i > 0:
            dim_v(xdim + 3.3, y_bottom + lq_i, y_top, f"Taco = {taco_i:.2f} m", tag=f"  (#{i+1})")

# Numeración (pill + texto) toggle en leyenda
fig.add_trace(go.Scatter(
    x=label_x, y=label_y,
    mode="markers",
    marker=dict(symbol="square", size=18,
                color="rgba(255,255,255,0.80)",
                line=dict(width=1, color="rgba(0,0,0,0.30)")),
    name="Nº Barreno",
    legendgroup="labels",
    showlegend=True,
    hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=label_x, y=label_y,
    mode="text",
    text=label_text,
    textposition="middle center",
    legendgroup="labels",
    showlegend=False,
    textfont=dict(size=12, color="black"),
    hoverinfo="skip"
))

# ---------------- Cotas del banco + pie de talud ----------------
if show_dims and "Banco" in dims_what:
    dim_v(x=longbase, y0=base_y, y1=base_y+h, text=f"Altura banco = {h:.2f} m")
    dim_h(y=-1.2, x0=0, x1=longbase, text=f"Longitud = {longbase:.2f} m")

# cota color blanco de límite de pie de talud
if show_dims and "Pie de talud" in dims_what:
    dim_h(
        y=base_y,
        x0=0,
        x1=loninf + disdif,
        text="Límite pie de talud",
        dash="dash",
        color="white"
    )

# ------------------------ LAYOUT ------------------------
x_min = -7
x_max = max(longbase + 2, loninf + disdif + 14)
y_min = -2.5
y_max = base_y + h + 5

fig.update_layout(
    height=740,
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        title="Leyenda",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(0,0,0,0.25)",
        borderwidth=1,
        traceorder="normal",
        groupclick="togglegroup"
    ),
    xaxis=dict(title="Longitud (m)", range=[x_min, x_max], zeroline=False),
    yaxis=dict(title="Altura (m)", range=[y_min, y_max], zeroline=False),
)

fig.update_yaxes(scaleanchor="x", scaleratio=1)

st.markdown("---")
st.subheader("Gráfica resultante")
st.plotly_chart(fig, use_container_width=True)





