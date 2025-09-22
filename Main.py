import cv2
import mediapipe as mp
import numpy as np
import math

# Инициализация инструментов MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def calculate_angle(a, b, c):
    """
    Вычисляет угол между тремя точками (в градусах).
    Точка 'b' - вершина угла.
    """
    a = np.array(a)  # Первая точка
    b = np.array(b)  # Вершина
    c = np.array(c)  # Последняя точка

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


# --- ОСНОВНАЯ ЧАСТЬ ---

# Укажите путь к вашему фото.
# Для проверки сделайте фото, где человек стоит в профиль.
image_path = '5.jpg'  # <--- ЗАМЕНИТЕ НА ИМЯ ВАШЕГО ФАЙЛА
output_path = 'result_photo5.jpg'  # Имя файла для сохранения результата

# Создаем объект Pose для анализа
with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
    # 1. Загрузка и предобработка изображения
    image = cv2.imread(image_path)
    if image is None:
        print(f"Ошибка: не удалось загрузить изображение по пути: {image_path}")
    else:
        # Переводим изображение из BGR в RGB для MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 2. Обнаружение позы
        results = pose.process(image_rgb)

        # 3. Извлечение точек и вычисление угла
        if not results.pose_landmarks:
            print("На фото не удалось обнаружить человека.")
        else:
            try:
                landmarks = results.pose_landmarks.landmark

                # Получаем размеры изображения для пересчета координат
                h, w, _ = image.shape

                # Координаты ключевых точек для левой стороны тела
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h]

                ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x * w,
                       landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y * h]

                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * w,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * h]

                # Вычисляем угол
                back_angle = calculate_angle(ear, shoulder, hip)

                # --- Визуализация на изображении ---
                # Отображаем значение угла
                cv2.putText(image,
                            f"Back Angle: {int(back_angle)}",
                            (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                # Добавляем рекомендацию
                if back_angle < 165:
                    recommendation = "Risk: Keep your back straight!"
                    color = (0, 0, 255)  # Красный
                else:
                    recommendation = "Posture is OK"
                    color = (0, 255, 0)  # Зеленый

                cv2.putText(image, recommendation, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

                # 4. Отрисовка скелета
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                )

                # 5. Сохранение результата
                cv2.imwrite(output_path, image)
                print(f"Анализ завершен! Результат сохранен в файл: {output_path}")

            except Exception as e:
                print(f"Произошла ошибка при обработке точек: {e}")