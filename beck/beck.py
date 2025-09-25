import sys

import cv2
import mediapipe as mp
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont

# --- Инициализация инструментов ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


# --- Функции для вычислений ---
def calculate_angle_with_horizontal(p1, p2):
    """Вычисляет угол линии между двумя точками относительно горизонтальной оси."""
    radians = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    angle = math.degrees(radians)
    return angle


def calculate_angle_with_vertical(p1, p2):
    """Вычисляет угол линии между двумя точками относительно вертикальной оси."""
    radians = math.atan2(p2[0] - p1[0], p2[1] - p1[1])
    angle = 90 - math.degrees(radians)
    return abs(angle)


# --- ОСНОВНАЯ ЧАСТЬ ---

if len(sys.argv) != 3:
    print("Ошибка: Укажите путь к исходному и конечному файлам")
    sys.exit(1)

# Укажите путь к вашему фото, сделанному СБОКУ.
image_path = sys.argv[1]  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕГО ФАЙЛА
output_path = sys.argv[2]

# Путь к файлу шрифта для русского текста
font_path = 'DejaVuSans.ttf'  # <--- УБЕДИТЕСЬ, ЧТО ФАЙЛ В ТОЙ ЖЕ ПАПКЕ

try:
    font_main = ImageFont.truetype(font_path, 30)  # Основной шрифт
    font_diag = ImageFont.truetype(font_path, 32)  # Шрифт для диагноза
    font_warn = ImageFont.truetype(font_path, 18)  # Шрифт для предупреждения
except IOError:
    print(f"Ошибка: Не найден файл шрифта по пути {font_path}. Скачайте его и положите рядом со скриптом.")
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

                left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w,
                                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h]
                right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * w,
                                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * h]
                left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * w,
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * h]
                right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]

                shoulder_angle = calculate_angle_with_horizontal(left_shoulder, right_shoulder)
                mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2)
                mid_hip = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
                spine_angle_from_vertical = abs(90 - calculate_angle_with_vertical(mid_shoulder, mid_hip))

                # --- Диагностика по степеням ---
                max_deviation = max(abs(shoulder_angle), spine_angle_from_vertical)

                if max_deviation <= 3:
                    diagnosis = "Норма"
                    color = (0, 200, 0)  # Зеленый
                elif 3 < max_deviation <= 10:
                    diagnosis = "Сколиоз I степени"
                    color = (0, 255, 255)  # Желтый
                elif 10 < max_deviation <= 25:
                    diagnosis = "Подозрение на сколиоз II степени"
                    color = (0, 165, 255)  # Оранжевый
                else:  # max_deviation > 25
                    diagnosis = "Подозрение на сколиоз III степени"
                    color = (0, 0, 255)  # Красный

                # --- Визуализация (с русским текстом) ---
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(image_pil)

                if font_main:
                    draw.text((50, 40), f"Наклон плеч: {shoulder_angle:.1f}°", font=font_main, fill=(255, 255, 0), stroke_fill=(0, 0, 0), stroke_width= 1.5)
                    draw.text((50, 80), f"Искривление позвоночника: {spine_angle_from_vertical:.1f}°", font=font_main,
                              fill=(0, 255, 255), stroke_fill=(0, 0, 0), stroke_width= 1.5)
                    draw.text((50, 130), f"Диагноз: {diagnosis}", font=font_diag, fill=color, stroke_fill=(0, 0, 0), stroke_width= 1.5)
                    draw.text((30, h - 60), "ВНИМАНИЕ: Результат не является медицинским диагнозом!", font=font_warn,
                              fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width= 1.5)

                image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

                cv2.line(image, (int(left_shoulder[0]), int(left_shoulder[1])),
                         (int(right_shoulder[0]), int(right_shoulder[1])), (255, 255, 0), 3)
                cv2.line(image, (int(mid_shoulder[0]), int(mid_shoulder[1])), (int(mid_hip[0]), int(mid_hip[1])),
                         (0, 255, 255), 3)
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                cv2.imwrite(output_path, image)
                print(f"Анализ завершен! Результат сохранен в файл: {output_path}")

            except Exception as e:
                print(f"Произошла ошибка при обработке точек: {e}")