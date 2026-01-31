import os
import cv2
import numpy as np
import base64
from tencentcloud.tiia.v20190529 import tiia_client, models
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from config import IS_DEV
from exceptions import AppException
from backend.services.scalp.scalp_roi import extract_scalp_region

def analyze_with_tencent_cloud(image_path: str) -> dict:
    """调用腾讯云图像识别API"""
    try:
        # 读取图片
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 腾讯云密钥
        secret_id = os.getenv("TENCENT_SECRET_ID")
        secret_key = os.getenv("TENCENT_SECRET_KEY")
        
        if not secret_id or not secret_key:
            return {"has_hair": True, "has_scalp": True, "labels": []}

        # 调用API
        cred = credential.Credential(secret_id, secret_key)
        client = tiia_client.TiiaClient(cred, "ap-guangzhou")
        
        req = models.DetectLabelRequest()
        req.ImageBase64 = image_base64  # 简化的参数设置
        req.Scenes = ["CAMERA"]

        response = client.DetectLabel(req)
        
        # 解析结果
        labels = []
        if hasattr(response, 'Labels'):
            labels = [label.Name.lower() for label in response.Labels]
        elif hasattr(response, 'LabelSet'):
            labels = [label["Name"].lower() for label in response.LabelSet]

        # 检查是否有头发或头皮相关标签
        scalp_keywords = ["scalp", "head", "hair", "face", "skin", "bald", "human", "person"]
        has_scalp = any(any(keyword in label for keyword in scalp_keywords) for label in labels)

        return {
            "has_hair": has_scalp or len(labels) == 0,  # 如果没有标签，默认是头皮
            "has_scalp": has_scalp or len(labels) == 0,  # 如果没有标签，默认是头皮
            "labels": labels,
        }
        
    except Exception:
        # API调用失败时，直接返回是头皮
        return {"has_hair": True, "has_scalp": True, "labels": []}

# 核心：头皮分析主函数（简化版）
def analyze_scalp_image(image_path: str) -> dict:
    # 1. 检查文件是否存在
    if not os.path.exists(image_path):
        raise AppException("IMAGE_NOT_FOUND", "图片不存在")

    # 2. 读取图片
    image = cv2.imread(image_path)
    if image is None:
        raise AppException("IMAGE_READ_FAILED", "图片读取失败")

    # 3. 尝试裁剪头皮区域
    scalp = extract_scalp_region(image)
    if scalp is None or scalp.size == 0:
        scalp = image  # 如果裁剪失败，用原图

    # 4. 转为灰度图
    gray = cv2.cvtColor(scalp, cv2.COLOR_BGR2GRAY)
    
    # 5. 获取腾讯云结果（但不管结果如何，都继续处理）
    vision_result = analyze_with_tencent_cloud(image_path)
    
    # 6. 简单检查：图片不能太小或太大
    height, width = gray.shape
    if height < 50 or width < 50:
        raise AppException("NOT_SCALP_IMAGE", "图片太小，请上传更清晰的照片")
    
    # 7. 计算图像特征
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # 8. 计算分数（简单公式）
    score = round((min(contrast / 64, 5) + min(sharpness / 500, 5)) / 2, 2)
    score = min(max(score, 1), 5)  # 确保分数在1-5之间

    # 9. 判断头皮类型
    if brightness > 180:
        level = "油性"
        summary = "头皮偏油，油脂分泌较旺盛"
        issues = [{"code": "oil", "label": "油脂分泌偏多", "severity": 2}]
        advice_immediate = ["避免高油饮食", "注意头皮清洁"]
        advice_long = ["选择控油型洗护产品"]
    elif brightness < 90:
        level = "干性"
        summary = "头皮偏干，油脂分泌不足"
        issues = [{"code": "dry", "label": "头皮干燥", "severity": 2}]
        advice_immediate = ["减少清洗频率"]
        advice_long = ["加强保湿护理"]
    else:
        level = "正常"
        summary = "头皮状态整体健康"
        issues = [{"code": "normal", "label": "无明显异常", "severity": 0}]
        advice_immediate = ["保持规律作息"]
        advice_long = ["选择适合自身发质的洗护产品"]

    # 10. 风险等级
    if score < 2:
        risk_level = "low"
    elif score < 3.5:
        risk_level = "medium"
    else:
        risk_level = "high"

    # 11. 返回结果
    result = {
        "status": "success",
        "scene": "scalp",
        "level": level,
        "risk_level": risk_level,
        "score": score,
        "summary": summary,
        "issues": issues,
        "advice": {"immediate": advice_immediate, "long_term": advice_long},
        "disclaimer": "本结果仅供健康参考，不构成医疗诊断"
    }

    # 调试信息
    if IS_DEV:
        result["debug"] = {
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
            "vision_result": vision_result,
            "image_size": f"{width}x{height}"
        }

    return result