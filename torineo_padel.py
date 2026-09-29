"""
Organizador de un Torneo de Padel (Historial de Enfrentamientos)
------------------------------------------------------------------
Estructura de datos principal: matriz de adyacencia N x N (lista de listas).
Cada fila representa a un jugador, cada columna a su rival, y cada celda
contiene la diferencia de sets del enfrentamiento entre ambos. La diagonal
se mantiene siempre en 0 (nadie se enfrenta a si mismo) y la matriz debe
cumplir la propiedad de antisimetria: matriz_traspuesta = -1 * matriz.
"""

import os


class ResultadoDuplicadoError(Exception):
    """
    Se lanza al intentar registrar un resultado para un enfrentamiento que
    ya tiene un resultado cargado, sin autorizar explicitamente la
    sobreescritura. Permite que la interfaz pregunte antes de pisar un dato.
    """
    pass


# ---------------------------------------------------------------------
# Construccion INTERACTIVA del torneo (usada por la interfaz grafica):
# el torneo se arma de a un jugador y de a un resultado por vez, en lugar
# de leerse todo junto desde un archivo. La matriz crece dinamicamente.
# ---------------------------------------------------------------------

def crear_torneo():
    """Crea un torneo vacio: lista de jugadores vacia y matriz 0 x 0."""
    return [], []


def agregar_jugador(jugadores, matriz, nombre):
    """
    Agrega un jugador nuevo, haciendo crecer la matriz de N x N a
    (N+1) x (N+1): se agrega una columna en 0 a cada fila existente y una
    fila nueva de ceros al final (incluida la nueva diagonal). No modifica
    los resultados ya cargados entre los demas jugadores. Lanza ValueError
    si el nombre es invalido o ya esta cargado (evita duplicados).
    """
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del jugador no puede estar vacio.")
    if nombre in jugadores:
        raise ValueError(f"El jugador '{nombre}' ya esta cargado en el torneo.")

    n = len(jugadores)
    for fila in matriz:
        fila.append(0)
    matriz.append([0] * (n + 1))
    jugadores.append(nombre)
    return jugadores, matriz


def registrar_resultado(jugadores, matriz, jugador_a, jugador_b, diferencia,
                         permitir_sobrescribir=False):
    """
    Registra el resultado de un enfrentamiento: diferencia de sets de
    jugador_a sobre jugador_b (negativa si jugador_a perdio). Completa
    automaticamente la celda reciproca (matriz[j][i] = -diferencia), por
    lo que la matriz queda antisimetrica por construccion.

    Si el enfrentamiento ya tenia un resultado cargado (celda distinta de
    0) y no se autoriza explicitamente la sobreescritura, lanza
    ResultadoDuplicadoError en lugar de pisar el dato existente; esto
    permite detectar cargas duplicadas/contradictorias tambien en la
    carga interactiva, no solo al leer un archivo.
    """
    if jugador_a == jugador_b:
        raise ValueError("Un jugador no puede enfrentarse a si mismo.")
    if jugador_a not in jugadores or jugador_b not in jugadores:
        raise ValueError("Ambos jugadores deben estar cargados en el torneo.")
    if diferencia == 0:
        raise ValueError("La diferencia de sets no puede ser 0 (un partido siempre tiene ganador).")

    i, j = jugadores.index(jugador_a), jugadores.index(jugador_b)

    ya_jugaron = matriz[i][j] != 0 or matriz[j][i] != 0
    if ya_jugaron and not permitir_sobrescribir:
        anterior = matriz[i][j]
        raise ResultadoDuplicadoError(
            f"Ya existe un resultado cargado entre {jugador_a} y {jugador_b} "
            f"(diferencia actual: {anterior:+d})."
        )

    matriz[i][j] = diferencia
    matriz[j][i] = -diferencia
    return ya_jugaron  # True si se sobrescribio un resultado existente


# ---------------------------------------------------------------------
# Construccion del torneo a partir de un ARCHIVO de texto (usada por la
# version de consola y por la opcion "Importar desde archivo" de la GUI).
# ---------------------------------------------------------------------

def cargar_partidos(ruta_archivo):
    """
    Lee el archivo de resultados (formato: jugadorA,jugadorB,diferencia)
    y devuelve la lista de partidos validos. Detecta y descarta lineas
    con datos duplicados/contradictorios antes de construir la matriz.
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontro el archivo '{ruta_archivo}'.")

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        lineas = [linea.strip() for linea in f if linea.strip()]

    if not lineas:
        return []  # Caso limite: archivo vacio -> no hay partidos que cargar

    partidos = []
    registrados = {}  # clave: par ordenado alfabeticamente -> diferencia normalizada

    for numero_linea, linea in enumerate(lineas, start=1):
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 3:
            print(f"  Aviso: linea {numero_linea} mal formada, se omite -> '{linea}'")
            continue

        jugador_a, jugador_b, texto_diferencia = partes
        try:
            diferencia = int(texto_diferencia)
        except ValueError:
            print(f"  Aviso: linea {numero_linea} con diferencia invalida, se omite -> '{linea}'")
            continue

        # Normalizamos el par (orden alfabetico) para detectar duplicados
        # sin importar desde la perspectiva de que jugador fue cargado el dato.
        if jugador_a < jugador_b:
            clave = (jugador_a, jugador_b)
            diferencia_normalizada = diferencia
        else:
            clave = (jugador_b, jugador_a)
            diferencia_normalizada = -diferencia

        if clave in registrados:
            if registrados[clave] != diferencia_normalizada:
                print(f"  Error: dato duplicado y CONTRADICTORIO en linea {numero_linea} "
                      f"para el enfrentamiento {jugador_a} vs {jugador_b}. Se descarta la linea.")
            else:
                print(f"  Aviso: linea {numero_linea} repite un resultado ya cargado "
                      f"({jugador_a} vs {jugador_b}); se ignora por ser identica.")
            continue

        registrados[clave] = diferencia_normalizada
        partidos.append((jugador_a, jugador_b, diferencia))

    return partidos


def construir_matriz(partidos):
    """
    A partir de la lista de partidos validos arma:
    - la lista de jugadores (orden alfabetico -> define los indices)
    - la matriz de enfrentamientos N x N
    """
    jugadores = sorted({jugador for a, b, _ in partidos for jugador in (a, b)})
    n = len(jugadores)
    indice = {nombre: i for i, nombre in enumerate(jugadores)}

    matriz = [[0 for _ in range(n)] for _ in range(n)]

    for jugador_a, jugador_b, diferencia in partidos:
        i, j = indice[jugador_a], indice[jugador_b]
        matriz[i][j] = diferencia
        matriz[j][i] = -diferencia  # se completa la reciproca automaticamente

    return jugadores, matriz


# ---------------------------------------------------------------------
# Validacion y calculo de resultados (comunes a ambas formas de carga).
# ---------------------------------------------------------------------

def es_antisimetrica(matriz):
    """Verifica matriz_traspuesta == -1 * matriz (incluye diagonal en 0)."""
    n = len(matriz)
    for i in range(n):
        if matriz[i][i] != 0:
            return False, (i, i)
        for j in range(n):
            if matriz[i][j] != -matriz[j][i]:
                return False, (i, j)
    return True, None


def calcular_ranking(jugadores, matriz):
    n = len(jugadores)
    resultados = []
    for i in range(n):
        total_diferencia = sum(matriz[i])
        victorias = sum(1 for valor in matriz[i] if valor > 0)
        derrotas = sum(1 for valor in matriz[i] if valor < 0)
        resultados.append((jugadores[i], victorias, derrotas, total_diferencia))

    resultados.sort(key=lambda fila: (-fila[3], -fila[1]))
    return resultados


def mostrar_matriz(jugadores, matriz):
    n = len(jugadores)
    ancho = max(len(nombre) for nombre in jugadores) + 2
    encabezado = " " * ancho + "".join(f"{nombre:>{ancho}}" for nombre in jugadores)
    print(encabezado)
    for i in range(n):
        fila = f"{jugadores[i]:<{ancho}}" + "".join(f"{matriz[i][j]:>{ancho}}" for j in range(n))
        print(fila)


def mostrar_ranking(resultados):
    print(f"{'Jugador':<10}{'PG':>4}{'PP':>4}{'Dif. acumulada':>18}")
    for nombre, pg, pp, dif in resultados:
        print(f"{nombre:<10}{pg:>4}{pp:>4}{dif:>18}")


def ejecutar_torneo(ruta_archivo):
    print(f"--- Procesando '{ruta_archivo}' ---")
    try:
        partidos = cargar_partidos(ruta_archivo)
    except FileNotFoundError as error:
        print(f"  Error: {error}")
        return

    if not partidos:
        print("  No hay partidos cargados. No se puede determinar un campeon.")
        return

    jugadores, matriz = construir_matriz(partidos)

    valida, celda = es_antisimetrica(matriz)
    if not valida:
        print(f"  Error critico: la matriz no es antisimetrica en la celda {celda}. "
              "Se aborta el procesamiento.")
        return

    print("\n  Matriz de enfrentamientos:")
    mostrar_matriz(jugadores, matriz)

    resultados = calcular_ranking(jugadores, matriz)
    print("\n  Tabla de posiciones:")
    mostrar_ranking(resultados)

    campeon = resultados[0][0]
    print(f"\n  Campeon del torneo: {campeon}")


if __name__ == "__main__":
    ejecutar_torneo("resultados.txt")