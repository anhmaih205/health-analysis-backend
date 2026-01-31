import cv2

# OpenCV 自带人脸检测模型（不需要下载）
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)


def extract_scalp_region(image):
    """
    使用 OpenCV Haar Cascade 检测人脸
    并在其上方裁剪头皮区域
    """
    if image is None:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    # 没检测到人脸，直接返回原图（保证接口不炸）
    if len(faces) == 0:
        return None

    # 只取第一个人脸
    x, y, w, h = faces[0]

    # 头皮区域：人脸上方
    scalp_y1 = max(0, y - int(0.6 * h))
    scalp_y2 = y
    scalp_x1 = max(0, x)
    scalp_x2 = min(image.shape[1], x + w)

    scalp = image[scalp_y1:scalp_y2, scalp_x1:scalp_x2]

    if scalp.size == 0:
        return None

    return scalp
