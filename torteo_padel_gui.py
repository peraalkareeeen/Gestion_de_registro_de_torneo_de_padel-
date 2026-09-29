"""
Organizador de un Torneo de Padel - Interfaz grafica interactiva (Tkinter)
------------------------------------------------------------------
Reutiliza toda la logica de torneo_padel.py. A diferencia de una version
que solo lee un archivo ya armado, esta interfaz permite ir cargando el
torneo de forma interactiva: agregar jugadores de a uno (la matriz N x N
crece dinamicamente) y registrar resultados de a un enfrentamiento por
vez, entre cualquier par de jugadores ya cargados. Tambien conserva la
opcion de importar resultados en bloque desde un archivo de texto.

Despues de cada cambio se recalcula la matriz, se valida que siga siendo
antisimetrica y se actualiza la tabla de posiciones y el campeon.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from torneo_padel import (
    crear_torneo, agregar_jugador, registrar_resultado, ResultadoDuplicadoError,
    cargar_partidos, es_antisimetrica, calcular_ranking,
)


class VentanaTorneo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador de Torneo de Padel - Historial de Enfrentamientos")
        self.geometry("980x680")
        self.minsize(860, 560)
        self.configure(bg="#f2f2f2")

        # Estado del torneo: crece de a un jugador y de a un resultado por vez.
        self.jugadores, self.matriz = crear_torneo()

        self._construir_widgets()
        self._refrescar_todo()

    # ---------- Construccion de la interfaz ----------
    def _construir_widgets(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Encabezado.TLabel", font=("Segoe UI", 13, "bold"), background="#f2f2f2")
        estilo.configure("Seccion.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        estilo.configure("Campeon.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1a7a1a")
        estilo.configure("Error.TLabel", font=("Segoe UI", 10), foreground="#b00020")
        estilo.configure("Ok.TLabel", font=("Segoe UI", 9), foreground="#1a7a1a")

        ttk.Label(self, text="Organizador de Torneo de Padel", style="Encabezado.TLabel",
                  padding=(10, 8, 10, 0)).pack(anchor="w")

        # ---- Panel superior: alta de jugadores y carga de resultados ----
        panel = ttk.Frame(self, padding=(10, 4))
        panel.pack(fill="x")
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        marco_jugador = ttk.Labelframe(panel, text="1. Agregar jugador", style="Seccion.TLabelframe")
        marco_jugador.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.nombre_var = tk.StringVar()
        entrada_nombre = ttk.Entry(marco_jugador, textvariable=self.nombre_var, width=18)
        entrada_nombre.pack(side="left", padx=8, pady=8)
        entrada_nombre.bind("<Return>", lambda evento: self.agregar_jugador())
        ttk.Button(marco_jugador, text="Agregar", command=self.agregar_jugador).pack(
            side="left", padx=(0, 8), pady=8)

        marco_archivo = ttk.Labelframe(panel, text="Importar en bloque (opcional)",
                                        style="Seccion.TLabelframe")
        marco_archivo.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Button(marco_archivo, text="Importar desde archivo...",
                   command=self.importar_desde_archivo).pack(padx=8, pady=8)

        marco_partido = ttk.Labelframe(panel, text="2. Registrar resultado de un enfrentamiento",
                                        style="Seccion.TLabelframe")
        marco_partido.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))

        ttk.Label(marco_partido, text="Jugador:").grid(row=0, column=0, padx=(8, 4), pady=8)
        self.combo_a = ttk.Combobox(marco_partido, state="readonly", width=14, values=[])
        self.combo_a.grid(row=0, column=1, padx=4, pady=8)

        ttk.Label(marco_partido, text="le gano/perdio contra Rival:").grid(row=0, column=2, padx=4, pady=8)
        self.combo_b = ttk.Combobox(marco_partido, state="readonly", width=14, values=[])
        self.combo_b.grid(row=0, column=3, padx=4, pady=8)

        ttk.Label(marco_partido, text="Diferencia de sets:").grid(row=0, column=4, padx=4, pady=8)
        self.dif_var = tk.StringVar()
        entrada_dif = ttk.Entry(marco_partido, textvariable=self.dif_var, width=6)
        entrada_dif.grid(row=0, column=5, padx=4, pady=8)
        entrada_dif.bind("<Return>", lambda evento: self.registrar_resultado())

        ttk.Button(marco_partido, text="Registrar", command=self.registrar_resultado).grid(
            row=0, column=6, padx=8, pady=8)

        ttk.Label(marco_partido,
                  text="(Positiva si el jugador de la izquierda gano, negativa si perdio. "
                       "La celda reciproca del rival se completa sola.)",
                  foreground="#555", font=("Segoe UI", 8)).grid(
            row=1, column=0, columnspan=7, sticky="w", padx=8, pady=(0, 6))

        # ---- Mensajes de estado ----
        marco_estado = ttk.Frame(self, padding=(10, 0))
        marco_estado.pack(fill="x")
        self.mensaje = ttk.Label(marco_estado, text="", style="Error.TLabel")
        self.mensaje.pack(side="left")
        self.estado_matriz = ttk.Label(marco_estado, text="", style="Ok.TLabel")
        self.estado_matriz.pack(side="right")

        # ---- Resultados: matriz y tabla de posiciones ----
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=8)

        self.pestana_matriz = ttk.Frame(notebook)
        self.pestana_ranking = ttk.Frame(notebook)
        notebook.add(self.pestana_matriz, text="Matriz de enfrentamientos")
        notebook.add(self.pestana_ranking, text="Tabla de posiciones")

        self.tabla_matriz = ttk.Treeview(self.pestana_matriz, show="headings")
        self.tabla_matriz.pack(fill="both", expand=True, padx=6, pady=6)

        self.tabla_ranking = ttk.Treeview(
            self.pestana_ranking, columns=("pg", "pp", "dif"), show="tree headings")
        self.tabla_ranking.heading("#0", text="Jugador")
        self.tabla_ranking.column("#0", width=110, anchor="w")
        self.tabla_ranking.heading("pg", text="Partidos ganados")
        self.tabla_ranking.heading("pp", text="Partidos perdidos")
        self.tabla_ranking.heading("dif", text="Diferencia acumulada")
        self.tabla_ranking.pack(fill="both", expand=True, padx=6, pady=6)

        self.etiqueta_campeon = ttk.Label(self, text="", style="Campeon.TLabel", padding=10)
        self.etiqueta_campeon.pack(fill="x")

    # ---------- Acciones ----------
    def agregar_jugador(self):
        self._ocultar_mensaje()
        nombre = self.nombre_var.get()
        try:
            self.jugadores, self.matriz = agregar_jugador(self.jugadores, self.matriz, nombre)
        except ValueError as error:
            self._mostrar_error(str(error))
            return

        self.nombre_var.set("")
        self._refrescar_todo()

    def registrar_resultado(self, permitir_sobrescribir=False):
        self._ocultar_mensaje()
        jugador_a = self.combo_a.get()
        jugador_b = self.combo_b.get()

        if not jugador_a or not jugador_b:
            self._mostrar_error("Elija un jugador y un rival de las listas.")
            return

        texto_dif = self.dif_var.get().strip()
        try:
            diferencia = int(texto_dif)
        except ValueError:
            self._mostrar_error("La diferencia de sets debe ser un numero entero (por ej. 2 o -3).")
            return

        try:
            sobrescribio = registrar_resultado(
                self.jugadores, self.matriz, jugador_a, jugador_b, diferencia,
                permitir_sobrescribir=permitir_sobrescribir,
            )
        except ResultadoDuplicadoError as error:
            if messagebox.askyesno(
                "Resultado ya cargado",
                f"{error}\n\n¿Desea sobrescribirlo con el nuevo valor?"
            ):
                self.registrar_resultado(permitir_sobrescribir=True)
            return
        except ValueError as error:
            self._mostrar_error(str(error))
            return

        self.dif_var.set("")
        self._refrescar_todo()
        if sobrescribio:
            self._mostrar_aviso(f"Resultado {jugador_a} vs {jugador_b} actualizado.")

    def importar_desde_archivo(self):
        self._ocultar_mensaje()
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de resultados",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return

        try:
            partidos = cargar_partidos(ruta)
        except FileNotFoundError as error:
            self._mostrar_error(str(error))
            return

        if not partidos:
            self._mostrar_error("El archivo no tiene partidos validos para importar.")
            return

        agregados, actualizados, conflictos = 0, 0, 0
        for jugador_a, jugador_b, diferencia in partidos:
            for nombre in (jugador_a, jugador_b):
                if nombre not in self.jugadores:
                    self.jugadores, self.matriz = agregar_jugador(self.jugadores, self.matriz, nombre)
                    agregados += 1
            try:
                registrar_resultado(self.jugadores, self.matriz, jugador_a, jugador_b, diferencia)
            except ResultadoDuplicadoError:
                conflictos += 1
            else:
                actualizados += 1

        self._refrescar_todo()
        resumen = f"Importados {actualizados} resultado(s) y {agregados} jugador(es) nuevo(s)."
        if conflictos:
            resumen += f" Se omitieron {conflictos} por ya existir (edite manualmente si desea pisarlos)."
        self._mostrar_aviso(resumen)

    # ---------- Refresco de la interfaz ----------
    def _refrescar_todo(self):
        self.combo_a["values"] = self.jugadores
        self.combo_b["values"] = self.jugadores

        self._cargar_matriz()

        if len(self.jugadores) < 2:
            self._limpiar_ranking()
            self.etiqueta_campeon.configure(text="")
            self.estado_matriz.configure(text="")
            return

        valida, celda = es_antisimetrica(self.matriz)
        if not valida:
            # No deberia ocurrir (la matriz se completa siempre en pareja),
            # pero se deja como control de integridad explicito.
            self.estado_matriz.configure(
                text=f"Matriz NO antisimetrica en {celda}", style="Error.TLabel")
            self._limpiar_ranking()
            self.etiqueta_campeon.configure(text="")
            return

        self.estado_matriz.configure(text="Matriz antisimetrica: correcta", style="Ok.TLabel")

        resultados = calcular_ranking(self.jugadores, self.matriz)
        self._cargar_ranking(resultados)
        campeon = resultados[0][0]
        self.etiqueta_campeon.configure(text=f"Campeon del torneo (hasta el momento): {campeon}")

    def _cargar_matriz(self):
        tabla = self.tabla_matriz
        tabla.delete(*tabla.get_children())
        tabla["columns"] = ()

        if not self.jugadores:
            return

        columnas = ["jugador"] + self.jugadores
        tabla["columns"] = columnas
        tabla.heading("jugador", text="")
        tabla.column("jugador", width=90, anchor="w")
        for nombre in self.jugadores:
            tabla.heading(nombre, text=nombre)
            tabla.column(nombre, width=70, anchor="center")
        for i, nombre_fila in enumerate(self.jugadores):
            valores = [nombre_fila] + [self.matriz[i][j] for j in range(len(self.jugadores))]
            tabla.insert("", "end", values=valores)

    def _cargar_ranking(self, resultados):
        self._limpiar_ranking()
        for nombre, pg, pp, dif in resultados:
            self.tabla_ranking.insert("", "end", text=nombre, values=(pg, pp, dif))

    def _limpiar_ranking(self):
        self.tabla_ranking.delete(*self.tabla_ranking.get_children())

    def _mostrar_error(self, texto):
        self.mensaje.configure(text=texto, style="Error.TLabel")

    def _mostrar_aviso(self, texto):
        self.mensaje.configure(text=texto, style="Ok.TLabel")

    def _ocultar_mensaje(self):
        self.mensaje.configure(text="")


if __name__ == "__main__":
    app = VentanaTorneo()
    app.mainloop()