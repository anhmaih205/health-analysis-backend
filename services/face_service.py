#Face++ 人脸皮肤分析服务

import os
import requests
import time
import threading
import logging
from exceptions import AppException
from config import IS_DEV

# 全局锁，确保同一时间只有一个 Face++ 调用
facepp_lock = threading.Lock()
last_call_time = 0

#从环境变量中读取API密钥
FACEPP_API_KEY = os.getenv("FACEPP_API_KEY")
FACEPP_API_SECRET = os.getenv("FACEPP_API_SECRET")
#调用URL
FACEPP_SKIN_API = "https://api-cn.faceplusplus.com/facepp/v1/skinanalyze"

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 工具函数-->数据映射字典，将返回的value转换为中文描述
BOOLEAN_MAP = {
    0: "无",
    1: "有"
}

EYELID_MAP = {
    0: "单眼皮",
    1: "平行双眼皮",
    2: "扇形双眼皮"
}

SKIN_TYPE_MAP = {
    0: "油性皮肤",
    1: "干性皮肤",
    2: "中性皮肤",
    3: "混合性皮肤"
}

#解析详细检测结果
#当置信度低于60%，则不返回这个结果
def parse_boolean(item: dict, min_confidence=0.6):
    """解析 {value, confidence} 结构的布尔检测项"""
    if not item:
        return None
    if item.get("confidence", 0) < min_confidence:
        return None
    return item.get("value")

def parse_enum(item: dict, enum_map: dict, min_confidence=0.6):
    """解析枚举型检测项"""
    if not item:
        return None
    if item.get("confidence", 0) < min_confidence:
        return None
    value = item.get("value")
    return enum_map.get(value,"未知")

#智能建议生成器
def generate_health_advice(skin_type_value,analysis):
    """基于皮肤类型和详细分析结果，生成综合性健康建议"""
    base_advice={
        0:{
            "level": "油性皮肤",
            "summary": "皮脂分泌旺盛，需注重控油与清洁",
            "base_care": ["使用氨基酸等温和洁面产品，每日清洁1-2次", 
                          "选择质地清爽的保湿产品，如含有透明质酸、神经酰胺的乳液或凝露",
                            "日常使用防晒霜，避免油脂氧化加剧皮肤问题"]
        },
        1:{
            "level": "干性皮肤",
            "summary": "皮肤屏障可能偏弱，需强化保湿与修护",
            "base_care": ["使用温和、滋润的洁面产品，避免过度清洁",
                           "选择含角鲨烷、油脂成分较高的面霜，锁住水分",
                           "室内可考虑使用加湿器"]
        },
        2:{
            "level": "中性皮肤",
            "summary": "皮肤状态整体平衡健康，注意维持",
            "base_care": ["保持现有护肤习惯",
                           "注意补水保湿和日常防晒"]
        },
        3:{
            "level": "混合性皮肤",
            "summary": "T区与脸颊需求不同，建议分区护理",
            "base_care": ["T区（额头、鼻子、下巴）可使用较清爽的护肤品", 
                          "脸颊等干燥区域使用更滋润的产品"]
        }
    }

    #存储所有皮肤类型的数据，若返回值不是{0，1，2，3}则返回中性皮肤的建议
    skin_info = base_advice.get(skin_type_value,base_advice[2])

    #分析具体问题，生成针对性建议
    detailed_advice = []
    focus_problems = []
    #按问题优先级和类别分组建议
    problem_advice_map = {
        # 皱纹类
        "forehead_wrinkle": "抬头纹提示可能常做挑眉表情或额头肌肉紧张，建议注意表情管理，可考虑使用含有胜肽或维A醇（晚间使用）的产品。",
        "crows_feet": "鱼尾纹与眼周干燥和表情相关，需加强眼周保湿，可选用滋润型眼霜，并减少眯眼等夸张表情。",
        "eye_finelines": "眼部细纹需注重保湿和防晒，避免用力揉搓眼睛。",
        "glabella_wrinkle": "眉间纹（川字纹）与皱眉习惯有关，有意识放松眉间肌肉，并做好该区域保湿。",
        "nasolabial_fold": "法令纹成因复杂，确保脸颊充足保湿、避免侧睡挤压，可辅助面部轻柔提拉按摩。",
        # 皮肤质地类
        "pores_forehead": "额头毛孔粗大可能与油脂分泌有关，需做好清洁和控油，定期使用清洁面膜（每周1-2次）。",
        "pores_left_cheek": "左脸颊毛孔粗大需注意该侧清洁是否彻底，并避免经常用手触摸。",
        "pores_right_cheek": "右脸颊毛孔粗大需注意该侧清洁是否彻底，并避免经常用手触摸。",
        "pores_jaw": "下巴毛孔粗大常与油脂分泌及角质代谢有关，注意清洁和适度去角质（油性皮肤可每周1次）。",
        # 瑕疵类
        "blackhead": "有黑头问题，需坚持使用温和的清洁产品，并可定期使用水杨酸或果酸类产品帮助疏通毛孔。",
        "acne": "有痘痘，避免用手挤压，注重抗炎和舒缓，可选用含茶树精油、烟酰胺或壬二酸成分的产品点涂。",
        "skin_spot": "有斑点，必须严格防晒（SPF30以上），并可考虑使用含有维生素C、烟酰胺等成分的产品帮助淡化。",
        # 眼周问题
        "eye_pouch": "有眼袋，可能与循环不佳或水肿有关，建议保证充足睡眠，睡前减少饮水，可配合眼部按摩促进循环。",
        "dark_circle": "有黑眼圈，需区分类型（色素型、血管型、结构型），通常建议保证睡眠、做好眼周防晒，并可选用含维生素K或咖啡因的眼霜。"
    }
    #检查每个问题，存在则给建议
    for problem_key,advice in problem_advice_map.items():
        if analysis.get(problem_key) == 1:
            detailed_advice.append(advice)
            focus_problems.append(problem_key)
    
    #计算健康评分
    #统计有某项皮肤问题的值，每个值10分，50分为保底分数
    total_problems = sum(1 for v in analysis.values() if isinstance(v,int) and v == 1)
    health_score = max(50,100 - total_problems * 10)
    health_score = round(health_score)

    #生成最终结论
    final_summary = skin_info["summary"]
    if focus_problems:
        #翻译字段名为显式，共15项检测项目
        problem_name_map = {
            "forehead_wrinkle":"抬头纹",
            "crows_feet":"鱼尾纹",
            "eye_finelines": "眼部细纹",
            "glabella_wrinkle": "眉间纹",
            "nasolabial_fold": "法令纹",
            "pores_forehead": "额头毛孔",
            "pores_left_cheek": "左脸颊毛孔",
            "pores_right_cheek": "右脸颊毛孔",
            "pores_jaw": "下巴毛孔",
            "blackhead": "黑头",
            "acne": "痘痘",
            "skin_spot": "斑点",
            "eye_pouch": "眼袋",
            "dark_circle": "黑眼圈",
            "mole":"痣"
        }
        problem_names = [problem_name_map.get(k,k) for k in focus_problems[:3]]
        final_summary += f"。检测到需重点关注：{'、'.join(problem_names)}"
    return {
        "level": skin_info["level"],
        "summary": final_summary,
        "health_score": health_score,
        "base_care": skin_info["base_care"],
        "targeted_advice": detailed_advice,
        "focus_problems": focus_problems[:3]
    }

# 主逻辑
#满足必要条件后才能调用API
def analyze_face(image_path: str) -> dict:
    global last_call_time
    if not os.path.exists(image_path):
        raise AppException("IMAGE_NOT_FOUND", "图片不存在")

    if not FACEPP_API_KEY or not FACEPP_API_SECRET:
        raise AppException("FACEPP_CONFIG_ERROR", "Face++ API Key 未配置")

    # ========== 使用锁确保串行执行 ==========
    with facepp_lock:
        # 计算距离上次调用的时间
        now = time.time()
        time_since_last = now - last_call_time
        
        # 如果距离上次调用太近，等待更久
        if time_since_last < 10:  # 至少间隔8秒
            time.sleep(10 - time_since_last)

        # 更新最后调用时间
        last_call_time = time.time()

        #异常处理
        try:
            with open(image_path, "rb") as f:
                resp = requests.post(
                    FACEPP_SKIN_API,
                    data={
                        "api_key": FACEPP_API_KEY,
                        "api_secret": FACEPP_API_SECRET
                    },
                    files={"image_file": f},
                    timeout=30
                )
        except requests.RequestException as e:
            raise AppException("FACEPP_REQUEST_FAILED", str(e))

    if resp.status_code != 200:
        raise AppException("FACEPP_HTTP_ERROR", resp.text)

    result = resp.json()

    if "error_message" in result:
        raise AppException("FACEPP_API_ERROR", result["error_message"])

    skin = result.get("result", {})

    # 皮肤类型
    skin_type_info = skin.get("skin_type", {})
    skin_type_value = skin_type_info.get("skin_type")
    skin_type_label = SKIN_TYPE_MAP.get(skin_type_value, "未知")
    details = skin_type_info.get("details", {})
    skin_type_confidence = details.get(skin_type_value, {}).get("confidence", 0)

    # 面部问题检测
    raw_analysis = {}
    analysis_for_display = {}   #客户端显示格式
    
    # 需要检测的所有问题字段
    problem_fields = [
        "eye_pouch", "dark_circle", "forehead_wrinkle", "crows_feet", 
        "eye_finelines", "glabella_wrinkle", "nasolabial_fold",
        "pores_forehead", "pores_left_cheek", "pores_right_cheek", "pores_jaw",
        "blackhead", "acne", "mole", "skin_spot"
    ]
    for field in problem_fields:
        item = skin.get(field)
        raw_value = parse_boolean(item)  # 得到 0 或 1
        if raw_value is not None:
            raw_analysis[field] = raw_value
            # 同时生成用于显示的结果
            if item and item.get("confidence", 0) >= 0.6:
                analysis_for_display[field] = {
                    "value": BOOLEAN_MAP.get(raw_value, "未知"),
                    "confidence": round(item.get("confidence"), 2)
                }
    # 眼部形态（不需要参与健康评分，仅展示）
    left_eyelid = parse_enum(skin.get("left_eyelids"), EYELID_MAP)
    right_eyelid = parse_enum(skin.get("right_eyelids"), EYELID_MAP)
    if left_eyelid:
        analysis_for_display["left_eyelids"] = left_eyelid
    if right_eyelid:
        analysis_for_display["right_eyelids"] = right_eyelid
    
    #生成智能健康建议
    health_info = generate_health_advice(skin_type_value,raw_analysis)

    #构建最终响应
    response = {
        "status": "success",
        "scene": "face",
        "skin_type": {
            "label": skin_type_label,
            "confidence": round(skin_type_confidence, 2),
            "type_value":skin_type_value
        },
        "health_overview":{
            "level":health_info["level"],
            "summary":health_info["summary"],
            "health_score":health_info["health_score"],
            #风险等级划分
            "risk_level": "low" if health_info["health_score"] >= 80 
            else "medium" if health_info["health_score"] >= 60 else "high"
        },
        "analysis":analysis_for_display,
        "advice":{
            "base_care":health_info["base_care"],
            "targeted_advice":health_info["targeted_advice"]
        },
        "disclaimer":(
            "本结果基于AI图像分析，仅供护肤参考，不构成医疗诊断。"
            "如有严重皮肤问题，请咨询专业医生。")
    }

    if IS_DEV:
        response["debug"] = {
            "raw_analysis":raw_analysis,
            "focus_problems":health_info["focus_problems"],
            "raw_result": skin
        }

    return response
