import os

# 环境配置
IS_DEV = os.getenv("APP_ENV", "dev") == "dev"

# 图片存储配置
IMAGE_UPLOAD_DIR = "storage"
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# 腾讯云配置
TENCENT_CLOUD_REGION = "ap-guangzhou"