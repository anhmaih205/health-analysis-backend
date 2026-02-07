#场景路由分发器

import time
#from backend.services.scalp.scalp_service import analyze_scalp_image
from services.body_service import analyze_body
from services.face_service import analyze_face
from exceptions import AppException

def analyze_by_scene(scene:str,image_path:str) ->dict:
    scene = scene.lower()
    if scene == "face":
        # 在路由层也添加延迟，确保双重保护
        print(f"[路由层] 开始处理 face 分析，先等待 4 秒")
        time.sleep(4.0)
        print(f"[路由层] 等待结束，调用 analyze_face")
        return analyze_face(image_path)
    #elif scene == "body": 
    else:
        raise AppException(
        "UNSUPPORTED_SCENE", "暂不支持该检测类型"
    )
