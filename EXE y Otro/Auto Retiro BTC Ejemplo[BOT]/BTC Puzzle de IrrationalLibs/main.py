# Matriz de ejemplo representada como lista de listas
matrix = [
    list("T9U3V8W2Y0Z5R4O1B9M6J2K7H0L3X1Q5N8P7A4C9D3E6F2G8I7"),
    list("S0T4U5V9W3Y6Z2R7O0B4M8J1K3H6L2X0Q4N9P1A5C7D8E2F6G3"),
    list("I1S9T7U0V4W8Y5Z3R6O2B1M7J9K4H0L5X2Q8N3P6A1C4D7E9F5"),
    list("G2I8S3T6U2V7W0Y4Z9R501B0M3J6K8H2L1X7Q9N4P0A2C5D3E8"),
    list("F6G4I0S7T1U9V5W2Y8Z6R3O9B4M1J7K0H3L6X5Q2N8P1A9C4D2"),
    list("E7F0G3I6S8T5U3V0W4Y7Z2R1O6B5M0J2K9H7L3X1Q4N8P6A3C1"),
    list("D5E2F9G7I4S0T6U8V3W5Y1Z9R2O7B4M6J3K1H8L6X2Q5N9P7A4"),
    list("C8D6E3F1G5I2S7T0U4V9W6Y3Z1R8O5B2M7J0K6H3L9X4Q1N5P8"),
    list("A2C7D4E0F6G8I3S1T5U2V7W9Y0Z4R603B1M8J5K2H7L4X0Q3N9"),
    list("P6A1C5D8E2F7G4I9S6T3U0V5W2Y8Z7R4O1B3M0J6K9H2L5X1Q7"),
    list("N4P0A8C3D6E5F1G2I7S9T8U4V0W3Y5Z2R6O4B1M7J3K0H5L2X9"),
    list("Q6N1P8A2C4D7E3F9G5I0S6T1U5V2W8Y7Z4R0O3B9M6J2K1H4L7"),
    list("X3Q0N5P8A1C6D2E4F7G9I3S8T5U0V2W6Y1Z4R7O9B3M5J0K2H6"),
    list("L4X8Q1N3P7A5C2D9E6F0G4I7S1T3U8V5W2Y6Z6R4O2B6M9J3K7"),
    list("H0L5X2Q1N4P8A3C6D5E9F7G2I0S4T8U1V3W5Y7Z9R6O2B4M1J5"),
    list("K0H3L6X4Q8N2P7A0C3D6E2F9G5I1S7T4U8V0W2Y6Z3R5O9B2M4"),
    list("J1K7H3L0X5Q6N8P1A9C4D2E7F3G6I0S5T1U4V8W2Y7Z6R3O0B9"),
    list("M5J2K1H4L7X0Q3N6P8A2C1D5E9F4G7I3S6T9U2V5W8Y1Z4R7O3"),
    list("B2M6J0K9H5L3X1Q4N8P7A0C2D6E3F1G5I9S4T7U5V2W0Y6Z3R8"),
    list("O1B4M2J7K3H0L6X5Q1N9P8A3C2D5E7F4G6I0S3T8U1V7W2Y5Z9"),
    list("R6O4B0M3J1K2H7L4X0Q6N5P8A1C9D3E6F2G5I7S4T0U3V2W8Y6"),
]

# Direcciones posibles en el reloj
directions = {
    "arriba": (-1, 0),
    "arriba derecha": (-1, 1),
    "derecha": (0, 1),
    "abajo derecha": (1, 1),
    "abajo": (1, 0),
    "abajo izquierda": (1, -1),
    "izquierda": (0, -1),
    "arriba izquierda": (-1, -1),
}

# Función para buscar la secuencia y extraer todos los caracteres en la dirección
def buscar_secuencia_y_extraer(matrix, secuencia):
    filas = len(matrix)
    columnas = len(matrix[0])
    resultados = []

    # Recorremos toda la matriz
    for i in range(filas):
        for j in range(columnas):
            # Por cada dirección
            for nombre_dir, (di, dj) in directions.items():
                x, y = i, j
                encontrada = True
                caracteres_encontrados = []

                # Verificamos si la secuencia completa cabe en la dirección
                for k in range(len(secuencia)):
                    if not (0 <= x < filas and 0 <= y < columnas) or matrix[x][y] != secuencia[k]:
                        encontrada = False
                        break
                    caracteres_encontrados.append(matrix[x][y])
                    x += di
                    y += dj
                
                # Si encontramos la secuencia, seguimos en la misma dirección para capturar más caracteres
                if encontrada:
                    while 0 <= x < filas and 0 <= y < columnas:
                        caracteres_encontrados.append(matrix[x][y])
                        x += di
                        y += dj
                    
                    resultados.append((i, j, nombre_dir, ''.join(caracteres_encontrados)))
    
    return resultados

# Llamada a la función con la secuencia deseada
secuencia_objetivo = list("9V")
resultados = buscar_secuencia_y_extraer(matrix, secuencia_objetivo)

# Mostramos los resultados con formato de línea y posición
for fila, columna, direccion, caracteres in resultados:
    print(f"Línea {fila + 1} posición {columna + 1} dirección {direccion}: {caracteres}")
