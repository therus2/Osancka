import sys

import cv2
import mediapipe as mp
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont

# --- Инициализация инструментов ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


# --- Функция для вычисления угла ---
def calculate_angle(a, b, c):
    """Вычисляет угол между тремя точками (в градусах). Точка 'b' - вершина угла."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


# --- ОСНОВНАЯ ЧАСТЬ ---

if len(sys.argv) != 3:
    print("Ошибка: Укажите путь к исходному и конечному файлам")
    sys.exit(1)

# Укажите путь к вашему фото, сделанному СБОКУ.
image_path = sys.argv[1]  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕГО ФАЙЛА
output_path = sys.argv[2]  # Имя файла для сохранения результата

# Путь к файлу шрифта
font_path = 'DejaVuSans.ttf'  # <--- УБЕДИТЕСЬ, ЧТО ФАЙЛ В ТОЙ ЖЕ ПАПКЕ

try:
    font_main = ImageFont.truetype(font_path, 30)
    font_diag = ImageFont.truetype(font_path, 32)
    font_warn = ImageFont.truetype(font_path, 25)
except IOError:
    print(f"Ошибка: Не найден файл шрифта по пути {font_path}. Скачайте его.")
    font_main, font_diag, font_warn = None, None, None

# Создаем объект Pose для анализа
with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка: не удалось загрузить изображение: {image_path}")
    else:
        h, w, _ = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            print("На фото не удалось обнаружить человека.")
        else:
            try:
                landmarks = results.pose_landmarks.landmark

                # --- Извлечение координат ключевых точек (левая сторона) ---
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h]
                ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x * w,
                       landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y * h]
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * h]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * w,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * h]

                # --- Вычисление углов ---
                # Угол спины (для кифоза)
                back_angle = calculate_angle(ear, shoulder, hip)
                # Угол тела (для лордоза)
                body_angle = calculate_angle(shoulder, hip, ankle)

                # --- Диагностика ---
                # 1. Анализ на кифоз (сутулость)
                if back_angle >= 170:
                    kyphosis_diag = "Кифоз: Норма"
                    kyphosis_color = (0, 200, 0)
                elif 160 <= back_angle < 170:
                    kyphosis_diag = "Кифоз: Начальная стадия (сутулость)"
                    kyphosis_color = (0, 255, 255)  # Желтый
                else:
                    kyphosis_diag = "Кифоз: Выраженное искривление"
                    kyphosis_color = (0, 165, 255)  # Оранжевый

                # 2. Анализ на лордоз
                if body_angle >= 170:
                    lordosis_diag = "Лордоз: Норма"
                    lordosis_color = (0, 200, 0)
                elif 160 <= body_angle < 170:
                    lordosis_diag = "Лордоз: Незначительное отклонение"
                    lordosis_color = (0, 255, 255)  # Желтый
                else:
                    lordosis_diag = "Лордоз: Подозрение на гиперлордоз"
                    lordosis_color = (0, 0, 255)  # Красный

                # --- Визуализация ---
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(image_pil)

                if font_main:
                    # Вывод углов
                    draw.text((50, 40), f"Угол спины: {back_angle:.1f}°", font=font_main, fill=kyphosis_color, stroke_fill=(0, 0, 0), stroke_width= 1.5)
                    draw.text((50, 80), f"Угол тела: {body_angle:.1f}°", font=font_main, fill=lordosis_color, stroke_fill=(0, 0, 0), stroke_width= 1.5)

                    # Вывод диагнозов
                    draw.text((50, 140), kyphosis_diag, font=font_diag, fill=kyphosis_color, stroke_fill=(0, 0, 0), stroke_width= 1.5)
                    draw.text((50, 180), lordosis_diag, font=font_diag, fill=lordosis_color, stroke_fill=(0, 0, 0), stroke_width= 1.5)

                    # Предупреждение
                    draw.text((50, h - 60), "ВНИМАНИЕ: Результат не является медицинским диагнозом!", font=font_warn,
                              fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width= 1.5)

                image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

                # Рисуем скелет
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                cv2.imwrite(output_path, image)
                print(f"Анализ завершен! Результат сохранен в файл: {output_path}")

            except Exception as e:
                print(f"Произошла ошибка при обработке точек: {e}")