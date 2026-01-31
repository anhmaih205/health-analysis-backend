#FastAPI后端主入口文件

#导入模块-->web框架和中间件
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

#环境配置-->加载.env文件
from dotenv import load_dotenv
load_dotenv()

#项目自定义模块
from config import IS_DEV   #开发/生产环境标志
from schemas import FaceAnalyzeResponse #导入响应模型
from services.analyze_router import analyze_by_scene    #面部检测分析逻辑
from exceptions import AppException #自定义异常类

#系统工具
from PIL import Image  #图片格式检查
import shutil   #文件操作
import uuid     #生成唯一ID
import os       #操作系统接口
import logging  #日志记录

#创建应用
app = FastAPI()

# ========== CORS 跨域配置==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    #允许所有来源（开发时要限制）
    allow_methods=["*"],    #允许所有HTTP方法
    allow_headers=["*"],    #允许所有请求
)

# ========== 日志 ==========
logging.basicConfig(
    level=logging.DEBUG if IS_DEV else logging.INFO,  #显示debug日志
    format="%(asctime)s [%(levelname)s] %(message)s"  #格式
)

# ========== 全局异常处理 ==========
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    #业务逻辑异常处理
    logging.warning(f"AppException: {exc.code} : {exc.message}")
    return JSONResponse(
        #返回客户端错误
        status_code=400,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled Exception")
    return JSONResponse(
        #返回服务端错误
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误"
        }
    )

# ========== 健康检查 ==========
@app.get("/health")
def health_check():
    return {
        "status": "healthy",  #表明服务器正常运行
        "service": "health-analysis-backend"
    }

# ========== 上传接口 ==========
@app.post("/upload")
def upload_image(file: UploadFile = File(...)):
    #创建图片存储目录
    os.makedirs("storage", exist_ok=True)
    #保存原始文件
    tmp_filename = f"{uuid.uuid4()}.jpg"
    tmp_path = os.path.join("storage", tmp_filename)
    #保存
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 验证图片
        with Image.open(tmp_path) as img:
            img = img.convert("RGB")
            final_filename = f"{uuid.uuid4()}.jpg"
            final_path = os.path.join("storage", final_filename)

            img.save(final_path, format="JPEG", quality=95)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise AppException("IMAGE_INVALID",f"图片无法解析或格式不支持:{str(e)}")
    finally:
        #删除临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return {
            "status": "success",
            "image_path": final_path
        }

# ========== 分析接口 ==========
#添加响应模型进行验证返回格式是否正确
@app.post("/analyze",response_model=FaceAnalyzeResponse)
def analyze_image(
    image_path: str = Form(...),    #接收图片路径
    scene: str = Form("face")  # 分析场景设置
):
    if not os.path.exists(image_path):
        raise AppException(
            "IMAGE_NOT_FOUND","图片路径不存在"
        )
    
    #调用人脸分析逻辑
    return analyze_by_scene(
        image_path=image_path,
        scene=scene
    )
