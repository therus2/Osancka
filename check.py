import sys
import os

import cv2

print("--- ИСПОЛЬЗУЕМЫЙ ФАЙЛ PYTHON ---")
print(sys.executable)
print("\n--- ПАПКИ, ГДЕ PYTHON ИЩЕТ БИБЛИОТЕКИ ---")
for path in sys.path:
    print(path)

print(cv2.__version__)