import streamlit as st
import numpy as np
from scipy.optimize import linprog

st.set_page_config(
    page_title="Optimización de Microgrid",
    layout="wide"
)

st.title("⚡ Optimización de una Microgrid")

st.markdown("""
Minimizar el costo total de operación cumpliendo:

- Energía útil requerida = 450 MWh
- Emisiones ≤ límite establecido
- Energía renovable mínima
- Presupuesto máximo
- Capacidades mínimas y máximas
""")

# Datos iniciales
fuentes = [
    "Diésel",
    "Gas",
    "Solar",
    "Biomasa",
    "Eólica",
    "Batería"
]

datos = pd.DataFrame({
    "Fuente": fuentes,
    "Costo": [120, 80, 10, 50, 5, 30],
    "Mínimo": [30, 20, 0, 10, 0, 0],
    "Máximo": [300, 400, 150, 100, 120, 80],
    "Emisiones": [800, 400, 0, 50, 0, 0],
    "Eficiencia": [0.85, 0.90, 1.00, 0.80, 1.00, 0.90],
    "Renovable": [0, 0, 1, 1, 1, 0]
})

st.header("Parámetros del problema")

col1, col2 = st.columns(2)

with col1:
    energia_objetivo = st.number_input(
        "Energía útil requerida (MWh)",
        value=450.0,
        min_value=0.0
    )

    renovable_min = st.number_input(
        "Mínimo de energía renovable útil (MWh)",
        value=135.0,
        min_value=0.0
    )

with col2:
    emisiones_max = st.number_input(
        "Máximo de emisiones (kg CO₂)",
        value=40000.0,
        min_value=0.0
    )

    presupuesto_max = st.number_input(
        "Presupuesto máximo (USD)",
        value=15000.0,
        min_value=0.0
    )

st.header("Datos de los Generadores")

df = st.data_editor(
    datos,
    use_container_width=True,
    num_rows="fixed"
)

if st.button("🚀 Calcular Optimización"):

    try:

        costos = df["Costo"].to_numpy(dtype=float)
        minimos = df["Mínimo"].to_numpy(dtype=float)
        maximos = df["Máximo"].to_numpy(dtype=float)
        emisiones = df["Emisiones"].to_numpy(dtype=float)
        eficiencia = df["Eficiencia"].to_numpy(dtype=float)
        renovable = df["Renovable"].to_numpy(dtype=float)

        # Restricciones <=

        A_ub = [
            emisiones,
            costos,
            -(renovable * eficiencia)
        ]

        b_ub = [
            emisiones_max,
            presupuesto_max,
            -renovable_min
        ]

        # Restricción de igualdad
        A_eq = [eficiencia]
        b_eq = [energia_objetivo]

        bounds = [
            (float(minimos[i]), float(maximos[i]))
            for i in range(len(fuentes))
        ]

        resultado = linprog(
            c=costos,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs"
        )

        if resultado.success:

            st.success("✅ Solución óptima encontrada")

            solucion = pd.DataFrame({
                "Fuente": fuentes,
                "Generación (MWh)": np.round(resultado.x, 2)
            })

            st.subheader("Generación óptima")

            st.dataframe(
                solucion,
                use_container_width=True
            )

            costo_total = np.dot(costos, resultado.x)

            emisiones_totales = np.dot(
                emisiones,
                resultado.x
            )

            energia_util = np.dot(
                eficiencia,
                resultado.x
            )

            energia_renovable = np.dot(
                renovable * eficiencia,
                resultado.x
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Costo Total",
                f"${costo_total:,.2f}"
            )

            col2.metric(
                "Emisiones",
                f"{emisiones_totales:,.0f} kg"
            )

            col3.metric(
                "Energía Útil",
                f"{energia_util:,.2f} MWh"
            )

            col4.metric(
                "Energía Renovable",
                f"{energia_renovable:,.2f} MWh"
            )

        else:

            st.error("❌ No existe una solución factible")

            st.write(resultado.message)

    except Exception as e:
        st.error(f"Error: {str(e)}")
