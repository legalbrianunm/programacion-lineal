import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

st.set_page_config(
    page_title="Optimización de Microgrid",
    layout="wide"
)

st.title("⚡ Optimización de una Microgrid")

st.markdown("""
### Problema

Se desea minimizar el costo total de operación de una microgrid compuesta por distintas fuentes de energía.

Sujeto a las siguientes restricciones:

- La energía útil entregada debe ser exactamente la requerida.
- Deben respetarse las capacidades máximas.
- Deben respetarse las generaciones mínimas.
- Existe un límite de emisiones de CO₂.
- Debe generarse una cantidad mínima de energía renovable.
- Existe un presupuesto máximo disponible.
""")

# ---------------------------------------------------
# DATOS INICIALES
# ---------------------------------------------------

if "datos" not in st.session_state:

    st.session_state.datos = pd.DataFrame({
        "Generador": ["Diésel", "Gas", "Solar", "Biomasa", "Eólica", "Batería"],
        "Costo": [120, 80, 10, 50, 5, 30],
        "Generación mínima": [30, 20, 0, 10, 0, 0],
        "Capacidad máxima": [300, 400, 150, 100, 120, 80],
        "Emisiones": [800, 400, 0, 50, 0, 0],
        "Eficiencia": [85, 90, 100, 80, 100, 90],
        "Renovable": [False, False, True, True, True, False]
    })

st.subheader("Parámetros de los generadores")

# ---------------------------------------------------
# TABLA EDITABLE
# ---------------------------------------------------

datos = st.data_editor(
    st.session_state.datos,
    use_container_width=True,
    num_rows="fixed",
    column_config={

        "Generador": st.column_config.TextColumn(),

        "Costo": st.column_config.NumberColumn(step=1),

        "Generación mínima": st.column_config.NumberColumn(step=1),

        "Capacidad máxima": st.column_config.NumberColumn(step=1),

        "Emisiones": st.column_config.NumberColumn(step=1),

        "Eficiencia": st.column_config.NumberColumn(step=1),

        "Renovable": st.column_config.CheckboxColumn()

    }
)

st.session_state.datos = datos

# ---------------------------------------------------
# BOTONES AGREGAR Y ELIMINAR
# ---------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    if st.button("➕ Agregar generador"):

        nueva_fila = pd.DataFrame({
            "Generador": ["Nuevo"],
            "Costo": [0],
            "Generación mínima": [0],
            "Capacidad máxima": [0],
            "Emisiones": [0],
            "Eficiencia": [100],
            "Renovable": [False]
        })

        st.session_state.datos = pd.concat(
            [st.session_state.datos, nueva_fila],
            ignore_index=True
        )

        st.rerun()

with col2:

    if st.button("➖ Eliminar último generador"):

        if len(st.session_state.datos) > 1:

            st.session_state.datos = (
                st.session_state.datos.iloc[:-1]
                .reset_index(drop=True)
            )

            st.rerun()

# ---------------------------------------------------
# RESTRICCIONES GLOBALES
# ---------------------------------------------------

st.subheader("Restricciones globales")

col1, col2, col3 = st.columns(3)

with col1:

    energia_requerida = st.number_input(
        "Energía útil requerida (MWh)",
        value=450.0,
        step=1.0
    )

with col2:

    minimo_renovable = st.number_input(
        "Mínimo renovable (MWh)",
        value=135.0,
        step=1.0
    )

with col3:

    emisiones_max = st.number_input(
        "Máximo CO₂ (kg)",
        value=40000.0,
        step=1.0
    )

presupuesto_max = st.number_input(
    "Presupuesto máximo (USD)",
    value=15000.0,
    step=1.0
)

# ---------------------------------------------------
# BOTÓN OPTIMIZAR
# ---------------------------------------------------

if st.button("Optimizar"):

    try:

        costos = datos["Costo"].values.astype(float)

        eficiencia = (
            datos["Eficiencia"].values.astype(float) / 100
        )

        emisiones = (
            datos["Emisiones"].values.astype(float)
        )

        renovables = (
            datos["Renovable"].values.astype(int)
        )

        generacion_min = (
            datos["Generación mínima"].values.astype(float)
        )

        capacidad_max = (
            datos["Capacidad máxima"].values.astype(float)
        )

        # ----------------------------------------
        # MATRIZ DE RESTRICCIONES
        # ----------------------------------------

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

        constraints = LinearConstraint(
            A,
            bl,
            bu
        )

        bounds = Bounds(
            lb=generacion_min,
            ub=capacidad_max
        )

        resultado = milp(

            c=costos,

            constraints=constraints,

            bounds=bounds,

            integrality=[0] * len(datos)

        )

        # ----------------------------------------
        # RESULTADOS
        # ----------------------------------------

        if resultado.success:

            st.success(
                "Se encontró una solución óptima."
            )

            solucion = pd.DataFrame({
            
                "Generador": datos["Generador"],
            
                "Producción óptima (MWh)": resultado.x.round(2),

                "Emisiones totales (kg CO₂)": (
                    resultado.x * emisiones
                ).round(2),
                
                "Costo total (USD)": (
                    resultado.x * costos
                ).round(2),
            
            })

            st.subheader("Resultado")

            st.dataframe(
                solucion,
                use_container_width=True
            )

            # ----------------------------------------
            # MÉTRICAS
            # ----------------------------------------

            emisiones_totales = np.sum(
                resultado.x * emisiones
            )

            energia_renovable = np.sum(
                resultado.x *
                renovables *
                eficiencia
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Energía renovable útil",
                    f"{energia_renovable:,.2f} MWh"
                )
                
            with col2:

                st.metric(
                    "Emisiones totales",
                    f"{emisiones_totales:,.2f} kg CO₂"
                )


            with col3:

                st.metric(
                    "Costo mínimo",
                    f"${resultado.fun:,.2f}"
                )

            # ----------------------------------------
            # DATOS PARA LOS GRÁFICOS
            # ----------------------------------------

            emisiones_generador = pd.DataFrame({

                "Generador": datos["Generador"],

                "Emisiones (kg CO₂)": (

                    resultado.x * emisiones

                ).round(2)

            })

            costos_generador = pd.DataFrame({

                "Generador": datos["Generador"],

                "Costo (USD)": (

                    resultado.x * costos

                ).round(2)

            })

            # ----------------------------------------
            # GRÁFICOS
            # ----------------------------------------

            st.subheader("Visualización de resultados")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown("### Producción")

                st.bar_chart(
                    solucion.set_index("Generador")[
                        ["Producción óptima (MWh)"]
                    ]
                )

            with col2:

                st.markdown("### Emisiones")

                st.bar_chart(

                    emisiones_generador.set_index(
                        "Generador"
                    )

                )

            with col3:

                st.markdown("### Costos")

                st.bar_chart(

                    costos_generador.set_index(
                        "Generador"
                    )

                )

        else:

            st.error(
                "El problema es infactible con las restricciones actuales."
            )

    except Exception as e:

        st.error(
            f"Error: {e}"
        )
