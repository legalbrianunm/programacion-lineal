import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

st.set_page_config(page_title="Optimización de Microgrid", layout="wide")

st.title("⚡ Optimización de una Microgrid")

st.markdown("""
### Problema

Se desea minimizar el costo total de operación de una microgrid compuesta por:

- Diésel
- Gas natural
- Solar
- Biomasa
- Eólica
- Batería

Sujeto a las siguientes restricciones:

- La energía útil entregada debe ser exactamente la requerida.
- Deben respetarse las capacidades máximas.
- Deben respetarse las generaciones mínimas.
- Existe un límite de emisiones de CO₂.
- Debe generarse una cantidad mínima de energía renovable.
- Existe un presupuesto máximo disponible.
""")

# -----------------------------
# DATOS INICIALES
# -----------------------------

datos = pd.DataFrame({
    "Generador": ["Diésel", "Gas", "Solar", "Biomasa", "Eólica", "Batería"],
    "Costo": [120, 80, 10, 50, 5, 30],
    "Generación mínima": [30, 20, 0, 10, 0, 0],
    "Capacidad máxima": [300, 400, 150, 100, 120, 80],
    "Emisiones": [800, 400, 0, 50, 0, 0],
    "Eficiencia": [85, 90, 100, 80, 100, 90],
    "Renovable": [False, False, True, True, True, False]
})

st.subheader("Parámetros de los generadores")

datos = st.data_editor(
    datos,
    use_container_width=True,
    num_rows="fixed"
)

# -----------------------------
# RESTRICCIONES GLOBALES
# -----------------------------

st.subheader("Restricciones globales")

col1, col2, col3 = st.columns(3)

with col1:
    energia_requerida = st.number_input(
        "Energía útil requerida (MWh)",
        value=450.0
        step=1
    )

with col2:
    minimo_renovable = st.number_input(
        "Mínimo renovable (MWh)",
        value=135.0
        step=1
    )

with col3:
    emisiones_max = st.number_input(
        "Máximo CO₂ (kg)",
        value=40000.0
        step=1
    )

presupuesto_max = st.number_input(
    "Presupuesto máximo (USD)",
    value=15000.0
    step=1
)

# -----------------------------
# BOTÓN
# -----------------------------

if st.button("Optimizar"):

    costos = datos["Costo"].values

    eficiencia = datos["Eficiencia"].values / 100

    emisiones = datos["Emisiones"].values

    renovables = datos["Renovable"].values.astype(int)

    generacion_min = datos["Generación mínima"].values

    capacidad_max = datos["Capacidad máxima"].values

    # -------------------------
    # MATRIZ DE RESTRICCIONES
    # -------------------------

    A = np.array([

        # Energía útil total
        eficiencia,

        # Energía renovable
        renovables * eficiencia,

        # Emisiones
        emisiones,

        # Presupuesto
        costos

    ])

    bl = [
        energia_requerida,
        minimo_renovable,
        -np.inf,
        -np.inf
    ]

    bu = [
        energia_requerida,
        np.inf,
        emisiones_max,
        presupuesto_max
    ]

    constraints = LinearConstraint(A, bl, bu)

    bounds = Bounds(
        lb=generacion_min,
        ub=capacidad_max
    )

    try:

        resultado = milp(
            c=costos,
            constraints=constraints,
            bounds=bounds,
            integrality=[0]*6
        )

        if resultado.success:

            st.success("Se encontró una solución óptima")

            solucion = pd.DataFrame({
                "Generador": datos["Generador"],
                "Producción óptima (MWh)": resultado.x.round(2)
            })

            st.subheader("Resultado")

            st.dataframe(solucion, use_container_width=True)

            st.metric(
                "Costo mínimo",
                f"${resultado.fun:,.2f}"
            )

            emisiones_totales = np.sum(
                resultado.x * emisiones
            )

            energia_renovable = np.sum(
                resultado.x * renovables * eficiencia
            )

            st.write(f"**Emisiones totales:** {emisiones_totales:,.2f} kg CO₂")

            st.write(f"**Energía renovable útil:** {energia_renovable:,.2f} MWh")

            st.subheader("Distribución de la generación")

            st.bar_chart(
                solucion.set_index("Generador")
            )

        else:

            st.error("El problema es infactible.")

    except Exception as e:

        st.error(f"Error: {e}")
