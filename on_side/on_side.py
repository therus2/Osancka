import sys
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    """Вычисляет угол между тремя точками (в градусах)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def main(input_path: str, output_path: str):
    """Анализ фото сбоку (кифоз/лордоз)."""
    from PIL import ImageFont

    def load_font(size: int):
        """Загрузка шрифта с fallback."""
        font_candidates = [
            "DejaVuSans.ttf",  # локальный
            r"C:\Windows\Fonts\arial.ttf",  # Windows
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"  # Linux
        ]
        for path in font_candidates:
            try:
                return ImageFont.truetype(path, size)
            except IOError:
                continue
        return ImageFont.load_default()

    try:
        font_main = load_font(30)
        font_diag = load_font(32)
        font_warn = load_font(25)
    except IOError:
        raise FileNotFoundError(f"Не найден файл шрифта: {load_font}")

    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Не удалось загрузить изображение: {input_path}")

        h, w, _ = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            raise RuntimeError("На фото не удалось обнаружить человека.")

        landmarks = results.pose_landmarks.landmark

        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w,
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h]
        ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x * w,
               landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y * h]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * w,
               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * h]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * w,
                 landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * h]

        back_angle = calculate_angle(ear, shoulder, hip)
        body_angle = calculate_angle(shoulder, hip, ankle)

        # --- Диагностика ---
        if back_angle >= 170:
            kyphosis_diag, kyphosis_color = "Кифоз: Норма", (0, 200, 0)
        elif 160 <= back_angle < 170:
            kyphosis_diag, kyphosis_color = "Кифоз: Начальная стадия (сутулость)", (0, 255, 255)
        else:
            kyphosis_diag, kyphosis_color = "Кифоз: Выраженное искривление", (0, 165, 255)

        if body_angle >= 170:
            lordosis_diag, lordosis_color = "Лордоз: Норма", (0, 200, 0)
        elif 160 <= body_angle < 170:
            lordosis_diag, lordosis_color = "Лордоз: Незначительное отклонение", (0, 255, 255)
        else:
            lordosis_diag, lordosis_color = "Лордоз: Подозрение на гиперлордоз", (0, 0, 255)

        # --- Визуализация ---
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image_pil)

        draw.text((50, 40), f"Угол спины: {back_angle:.1f}°", font=font_main,
                  fill=kyphosis_color, stroke_fill=(0, 0, 0), stroke_width=1)
        draw.text((50, 80), f"Угол тела: {body_angle:.1f}°", font=font_main,
                  fill=lordosis_color, stroke_fill=(0, 0, 0), stroke_width=1)
        draw.text((50, 140), kyphosis_diag, font=font_diag,
                  fill=kyphosis_color, stroke_fill=(0, 0, 0), stroke_width=1)
        draw.text((50, 180), lordosis_diag, font=font_diag,
                  fill=lordosis_color, stroke_fill=(0, 0, 0), stroke_width=1)
        draw.text((50, h - 60), "ВНИМАНИЕ: Результат не является медицинским диагнозом!",
                  font=font_warn, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=1)

        image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imwrite(output_path, image)

        results_text = {
            "back_angle": round(back_angle, 1),
            "body_angle": round(body_angle, 1),
            "kyphosis": kyphosis_diag,
            "lordosis": lordosis_diag
        }

        return output_path, results_text


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python on_side.py input.jpg output.jpg")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
