import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.logging_config import logger

# 配置路径
PROMPTS_CONFIG_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"

prompt_router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptTemplate(BaseModel):
    """提示词模板模型"""
    name: str
    description: str
    prompt: str


class PromptCategory(BaseModel):
    """提示词分类模型"""
    name: str
    key: str
    description: str


class PromptTemplateResponse(BaseModel):
    """提示词模板响应模型"""
    category: str
    key: str
    template: PromptTemplate


def load_prompts_config():
    """加载提示词配置文件"""
    try:
        if not PROMPTS_CONFIG_PATH.exists():
            logger.warning(f"提示词配置文件不存在: {PROMPTS_CONFIG_PATH}")
            return {"templates": {}, "categories": []}
        
        with open(PROMPTS_CONFIG_PATH, encoding="utf-8") as file:
            config = yaml.safe_load(file)
        
        return config or {"templates": {}, "categories": []}
    except Exception as e:
        logger.error(f"加载提示词配置文件失败: {e}")
        raise HTTPException(status_code=500, detail="加载提示词配置失败")


@prompt_router.get("/categories", response_model=List[PromptCategory])
async def get_prompt_categories():
    """获取所有提示词分类"""
    try:
        config = load_prompts_config()
        categories = config.get("categories", [])
        return [PromptCategory(**category) for category in categories]
    except Exception as e:
        logger.error(f"获取提示词分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取提示词分类失败")


@prompt_router.get("/templates", response_model=List[PromptTemplateResponse])
async def get_all_prompt_templates():
    """获取所有提示词模板"""
    try:
        config = load_prompts_config()
        templates = config.get("templates", {})
        
        result = []
        for category_key, category_templates in templates.items():
            for template_key, template_data in category_templates.items():
                result.append(PromptTemplateResponse(
                    category=category_key,
                    key=template_key,
                    template=PromptTemplate(**template_data)
                ))
        
        return result
    except Exception as e:
        logger.error(f"获取所有提示词模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取提示词模板失败")


@prompt_router.get("/templates/{category}", response_model=Dict[str, PromptTemplate])
async def get_prompt_templates_by_category(category: str):
    """根据分类获取提示词模板"""
    try:
        config = load_prompts_config()
        templates = config.get("templates", {})
        
        if category not in templates:
            raise HTTPException(status_code=404, detail=f"分类 '{category}' 不存在")
        
        category_templates = templates[category]
        return {
            key: PromptTemplate(**template_data) 
            for key, template_data in category_templates.items()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类提示词模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取提示词模板失败")


@prompt_router.get("/templates/{category}/{template_key}", response_model=PromptTemplate)
async def get_prompt_template(category: str, template_key: str):
    """获取特定的提示词模板"""
    try:
        config = load_prompts_config()
        templates = config.get("templates", {})
        
        if category not in templates:
            raise HTTPException(status_code=404, detail=f"分类 '{category}' 不存在")
        
        category_templates = templates[category]
        if template_key not in category_templates:
            raise HTTPException(status_code=404, detail=f"模板 '{template_key}' 不存在")
        
        template_data = category_templates[template_key]
        return PromptTemplate(**template_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提示词模板失败: {e}")
        raise HTTPException(status_code=500, detail="获取提示词模板失败")


@prompt_router.get("/search")
async def search_prompt_templates(
    query: str,
    category: Optional[str] = None
):
    """搜索提示词模板"""
    try:
        config = load_prompts_config()
        templates = config.get("templates", {})
        
        results = []
        query_lower = query.lower()
        
        for category_key, category_templates in templates.items():
            # 如果指定了分类，只搜索该分类
            if category and category_key != category:
                continue
            
            for template_key, template_data in category_templates.items():
                # 搜索模板名称、描述和内容
                name = template_data.get("name", "").lower()
                description = template_data.get("description", "").lower()
                prompt = template_data.get("prompt", "").lower()
                
                if (query_lower in name or 
                    query_lower in description or 
                    query_lower in prompt):
                    results.append(PromptTemplateResponse(
                        category=category_key,
                        key=template_key,
                        template=PromptTemplate(**template_data)
                    ))
        
        return {
            "query": query,
            "category": category,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"搜索提示词模板失败: {e}")
        raise HTTPException(status_code=500, detail="搜索提示词模板失败")

    """获取提示词模板统计信息"""
    try:
        config = load_prompts_config()
        templates = config.get("templates", {})
        categories = config.get("categories", [])
        
        stats = {
            "total_categories": len(categories),
            "total_templates": 0,
            "templates_by_category": {},
            "categories": []
        }
        
        for category_key, category_templates in templates.items():
            template_count = len(category_templates)
            stats["total_templates"] += template_count
            stats["templates_by_category"][category_key] = template_count
        
        # 添加分类信息
        for category in categories:
            category_key = category.get("key")
            stats["categories"].append({
                "name": category.get("name"),
                "key": category_key,
                "description": category.get("description"),
                "template_count": stats["templates_by_category"].get(category_key, 0)
            })
        
        return stats
    except Exception as e:
        logger.error(f"获取提示词统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败") 