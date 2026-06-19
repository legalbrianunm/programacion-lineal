
import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

st.set_page_config(page_title="Optimización Energética", layout="wide")

st.title("🔋 Optimización de la Matriz Energética")

st.markdown("""
Modelo de programación lineal para minimizar el costo de generación energética.
""")

variables = ["Diésel", "Gas", "Solar", "Biomasa", "Eólica", "Batería"]

# -------------------------
# Función objetivo
# -------------------------

st.header("Función Objetivo (Costo por MW)")

col1, col2, col3 = st.columns(3)

with col1:
    c_d = st.number_input("Diésel", value=120.0)
    c_g = st.number_input("Gas", value=80.0)

with col2:
    c_s = st.number_input("Solar", value=10.0)
    c_b = st.number_input("Biomasa", value=50.0)

with col3:
    c_e = st.number_input("Eólica", value=5.0)
    c_ba = st.number_input("Batería", value=30.0)

c = [c_d, c_g, c_s, c_b, c_e, c_ba]

# -------------------------
# Parámetros globales
# -------------------------

st.header("Restricciones Globales")

col1, col2 = st.columns(2)

with col1:
    demanda = st.number_input(
        "Energía requerida",
        value=450.0,
        min_value=0.0
    )

    renovables_min = st.number_input(
        "Mínimo energía renovable",
        value=135.0,
        min_value=0.0
    )

with col2:
    emisiones_max = st.number_input(
        "Máximo emisiones",
        value=40000.0,
        min_value=0.0
    )

    presupuesto_max = st.number_input(
        "Presupuesto máximo",
        value=15000.0,
        min_value=0.0
    )

# -------------------------
# Matriz de coeficientes
# -------------------------

st.header("Coeficientes de las Restricciones")

st.subheader("Eficiencia Energética")

energia = [
    st.number_input(f"{v}", value=float(x), key=f"en_{i}")
    for i, x in enumerate([0.85, 0.90, 1.0, 0.80, 1.0, 0.90])
]

st.subheader("Energías Renovables")

renovables = [
    st.number_input(f"{v}", value=float(x), key=f"ren_{i}")
    for i, x in enumerate([0, 0, 1, 0.8, 1, 0])
]

st.subheader("Emisiones")

emisiones = [
    st.number_input(f"{v}", value=float(x), key=f"emi_{i}")
    for i, x in enumerate([800, 400, 0, 50, 0, 0])
]

# La restricción de presupuesto utiliza los costos
presupuesto = c.copy()

A = [
    energia,
    renovables,
    emisiones,
    presupuesto
]

bl = [
    demanda,
    renovables_min,
    -np.inf,
    -np.inf
]

bu = [
    demanda,
    np.inf,
    emisiones_max,
    presupuesto_max
]

constraints = LinearConstraint(A, bl, bu)

# -------------------------
# Límites de variables
# -------------------------

st.header("Límites de Generación (MW)")

lb = []
ub = []

for i, v in enumerate(variables):

    c1, c2 = st.columns(2)

    with c1:
        minimo = st.number_input(
            f"{v} mínimo",
            value=float([30, 20, 0, 10, 0, 0][i]),
            key=f"lb_{i}"
        )

    with c2:
        maximo = st.number_input(
            f"{v} máximo",
            value=float([400, 400, 150, 100, 120, 80][i]),
            key=f"ub_{i}"
        )

    lb.append(minimo)
    ub.append(maximo)

bounds = Bounds(lb=lb, ub=ub)

# -------------------------
# Resolver
# -------------------------

if st.button("🚀 Calcular Optimización"):

    try:

        res = milp(
            c=c,
            constraints=constraints,
            bounds=bounds,
            integrality=[0] * 6
        )

        if res.success:

            st.success("Se encontró una solución óptima")

            st.metric(
                "Costo Total Mínimo",
                f"USD {res.fun:,.2f}"
            )

            resultado = {
                "Tecnología": variables,
                "Generación (MW)": np.round(res.x, 2)
            }

            st.table(resultado)

            st.subheader("Vector solución")

            st.write(np.round(res.x, 4))

        else:

            st.error("No se encontró solución factible")

            st.write(res.message)

    except Exception as e:
        st.error(str(e))
