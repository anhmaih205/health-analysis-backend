#响应模型-->规定统一的返回格式

from typing import Optional,Dict,Any
from pydantic import BaseModel

#定义Pydantic模型，验证输入/输出数据的格式是否符合预期，提高准确性
#请求模型
class AnalyzeRequest(BaseModel):
    image_path: str
    scene: str = "face"

#详细的子模型
class SkinType(BaseModel):
    label:str
    confidence:float
    type_value:int

class HealthOverview(BaseModel):
    level:str
    summary:str
    health_score:float
    risk_level:str

class AnalysisItem(BaseModel):
    value:str
    confidence:float

class Advice(BaseModel):
    base_care:list[str]
    targeted_advice:list[str]

#主要响应模型
class FaceAnalyzeResponse(BaseModel):
    status: str
    scene: str
    skin_type:SkinType
    health_overview:HealthOverview
    analysis:Dict[str,Any]
    advice:Advice
    disclaimer: str
    debug: Optional[Dict[str,Any]] = None

