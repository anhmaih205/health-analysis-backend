"""
第三方错误 → App内部错误 映射
"""

def map_face_error(face_code: str):
    """
    Face++错误 → App统一错误
    返回 (code, message)
    """

    mapping = {

        # ===== 人脸问题 =====
        "NO_FACE_FOUND": (
            "NO_FACE_FOUND",
            "未检测到人脸，请上传清晰正脸照片"
        ),

        "INVALID_IMAGE_FACE": (
            "INVALID_IMAGE_FACE",
            "请确保只有一张完整人脸"
        ),

        # ===== 图片问题 =====
        "IMAGE_ERROR_UNSUPPORTED_FORMAT": (
            "INVALID_IMAGE_FORMAT",
            "图片格式不支持，请使用JPG或PNG"
        ),

        "INVALID_IMAGE_SIZE": (
            "INVALID_IMAGE_SIZE",
            "图片尺寸不符合要求"
        ),

        "IMAGE_FILE_TOO_LARGE": (
            "IMAGE_TOO_LARGE",
            "图片不能超过2MB"
        ),

        "IMAGE_DOWNLOAD_TIMEOUT": (
            "IMAGE_TIMEOUT",
            "图片处理超时，请重试"
        ),
    }

    # 默认未知错误
    return mapping.get(
        face_code,
        ("FACE_API_ERROR", "图片识别失败，请重试")
    )
