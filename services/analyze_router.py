#场景路由分发器

import time
#from backend.services.scalp.scalp_service import analyze_scalp_image
from services.body_service import analyze_body
from services.face_service import analyze_face
from exceptions import AppException
from exceptions import AppException
from error_mapper import map_face_error

def analyze_by_scene(scene:str,image_path:str) ->dict:
    scene = scene.lower()
    if scene == "face":
        return analyze_face(image_path)
    #elif scene == "body": 
    else:
        raise AppException(
        "UNSUPPORTED_SCENE", "暂不支持该检测类型"
    )
