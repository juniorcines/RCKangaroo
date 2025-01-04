# Valores originales
lines = [
    ("1B9", "7A4C9D3E6F2"),
    ("0B4", "1A5C7D8E2F6"),
    ("2B1", "6A1C4D7E9F5"),
    ("1B0", "0A2C5D3E8F6"),
    ("9B4", "1A9C4D2E7F0"),
    ("6B5", "6A3C1D5E2F9"),
    ("7B4", "7A4C8D6E3F1"),
    ("5B2", "8A2C7D4E0F6"),
    ("3B1", "6A1C5D8E2F7"),
    ("1B3", "0A8C3D6E5F1"),
    ("4B1", "8A2C4D7E3F9"),
    ("3B9", "8A1C6D2E4F7"),
    ("9B3", "7A5C2D9E6F0"),
    ("2B6", "8A3C6D5E9F7"),
    ("2B4", "7A0C3D6E2F9"),
    ("9B2", "1A9C4D2E7F3"),
    ("0B9", "8A2C1D5E9F4"),
    ("3B2", "7A0C2D6E3F1"),
    ("1B4", "8A3C2D5E7F4"),
    ("4B0", "8A1C9D3E6F2"),
]

# Invertir los valores hexadecimales
mirrored_lines = [(line[0][::-1], line[1][::-1]) for line in lines]

# Crear las líneas en formato solicitado e imprimirlas
for i, (line, mirrored) in enumerate(zip(lines, mirrored_lines)):
    print(f"Linea {i+1}: {line[0]} {line[1]} = {mirrored[0]} {mirrored[1]}")