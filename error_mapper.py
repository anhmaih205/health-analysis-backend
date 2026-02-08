from exceptions import AppException


def map_face_error(error: Exception) -> AppException:
    msg = str(error)

    if "NO_FACE_FOUND" in msg:
        return AppException(
            "NO_FACE_FOUND",
            "未检测到人脸，请重新上传清晰人脸照片"
        )

    if "MULTIPLE_FACES" in msg:
        return AppException(
            "MULTIPLE_FACES",
            "检测到多张人脸，请只上传单人照片"
        )

    return AppException(
        "FACE_ANALYSIS_FAILED",
        "人脸检测失败"
    )
