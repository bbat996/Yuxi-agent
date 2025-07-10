import os
import traceback

from server.src import config
from server.src.utils.logging_config import logger
from server.src.models.chat_model import OpenAIBase

def select_model(model_provider, model_name=None):
    """根据模型提供者选择模型"""
    assert model_provider is not None, "Model provider not specified"
    model_info = config.model_names.get(model_provider, {})
    model_name = model_name or model_info.get("default", "")

    logger.info(f"Selecting model from `{model_provider}` with `{model_name}`")

    if model_provider == "qianfan":
        from server.src.models.chat_model import Qianfan
        return Qianfan(model_name)

    if model_provider == "openai":
        from server.src.models.chat_model import OpenModel
        return OpenModel(model_name)

    if model_provider == "custom":
        model_info = get_custom_model(model_name)

        from server.src.models.chat_model import CustomModel
        return CustomModel(model_info)

    # 其他模型，默认使用OpenAIBase
    try:
        model = OpenAIBase(
            api_key=os.getenv(model_info["env"][0]),
            base_url=model_info["base_url"],
            model_name=model_name,
        )
        return model
    except Exception as e:
        raise ValueError(f"Model provider {model_provider} load failed, {e} \n {traceback.format_exc()}")

def get_custom_model(model_id):
    """return model_info"""
    assert config.custom_models is not None, "custom_models is not set"
    modle_info = next((x for x in config.custom_models if x["custom_id"] == model_id), None)
    if modle_info is None:
        raise ValueError(f"Model {model_id} not found in custom models")
    return modle_info
