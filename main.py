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
import tempfile #临时文件
import time     #时间处理

#创建应用
app = FastAPI()

# ========== CORS 跨域配置==========
app.add_middleware(
    CORSMiddleware,
    # 明确列出允许的源
    allow_origins=[
        "https://nextself.live",
        "https://www.nextself.live",
        "http://localhost",        # 保留本地开发
        "http://localhost:8000",
    ],
    allow_credentials=True,        # 如果需要cookie/session则设为True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确列出方法
    allow_headers=["*"],           # 或明确列出需要的headers
    expose_headers=["*"],          # 允许前端访问的响应头
    max_age=600,                   # 预检请求缓存时间（秒）
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


# ========== 合并上传+分析接口 ==========
#添加响应模型进行验证返回格式是否正确
@app.post("/analyze",response_model=FaceAnalyzeResponse)
async def analyze_image(
    file:UploadFile=File(...),    #接收图片路径
    scene: str = Form("face")  # 分析场景设置
): 
    try:
        # 1️⃣ 读文件到内存
        contents = await file.read()
        from io import BytesIO
        img = Image.open(BytesIO(contents))
        img = img.convert("RGB")
        # 2️⃣ 保存到 /tmp
        tmp_path = f"/tmp/upload_{uuid.uuid4().hex}.jpg"
        img.save(tmp_path, format="JPEG", quality=95)
        # 3️⃣ 调用分析
        result = analyze_by_scene(
            image_path=tmp_path,
            scene=scene
        )
        return result

    except AppException:
        raise
    except Exception as e:
        logging.exception("Analyze failed")
        raise AppException("ANALYZE_FAILED", str(e))
    
    finally:
        # ✅ 分析完成后立即清理文件
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass  # 忽略清理错误
