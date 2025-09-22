import cv2
import mediapipe as mp
import numpy as np
import math

# Инициализация инструментов MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


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

# Укажите путь к вашему фото, сделанному со спины.
image_path = 'b10.jpg'  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕГО ФАЙЛА
output_path = 'result_back_photo10.jpg'  # Имя файла для сохранения результата

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

                # Координаты плеч
                left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w,
                                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h]
                right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * w,
                                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * h]

                # Координаты бедер
                left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * w,
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * h]
                right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w,
                             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h]

                # 1. Анализ наклона плеч
                shoulder_angle = calculate_angle_with_horizontal(left_shoulder, right_shoulder)

                # 2. Анализ вертикальности позвоночника
                mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2)
                mid_hip = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
                spine_angle = calculate_angle_with_vertical(mid_shoulder, mid_hip)

                # --- Визуализация ---

                # Рисуем линию плеч
                cv2.line(image, (int(left_shoulder[0]), int(left_shoulder[1])),
                         (int(right_shoulder[0]), int(right_shoulder[1])), (0, 255, 255), 3)

                # Рисуем линию "позвоночника"
                cv2.line(image, (int(mid_shoulder[0]), int(mid_shoulder[1])),
                         (int(mid_hip[0]), int(mid_hip[1])), (255, 255, 0), 3)

                # Выводим результаты на экран
                cv2.putText(image, f"Shoulder Tilt: {shoulder_angle:.1f} deg", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                cv2.putText(image, f"Spine Verticality: {spine_angle:.1f} deg", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                # Предварительное заключение
                # Допустимый наклон плеч и позвоночника обычно не превышает 2-3 градуса
                if abs(shoulder_angle) > 3 or abs(90 - spine_angle) > 3:
                    conclusion = "Risk detected. Consult a specialist."
                    color = (0, 0, 255)  # Красный
                else:
                    conclusion = "Posture seems balanced."
                    color = (0, 255, 0)  # Зеленый

                cv2.putText(image, conclusion, (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                # Рисуем скелет
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Сохраняем результат
                cv2.imwrite(output_path, image)
                print(f"Анализ завершен! Результат сохранен в файл: {output_path}")

            except Exception as e:
                print(f"Произошла ошибка при обработке точек: {e}")