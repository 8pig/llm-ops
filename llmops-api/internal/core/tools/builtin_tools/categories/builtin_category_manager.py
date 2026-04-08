import os
from typing import Any

import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import CategoryEntity
from internal.exception import NotFoundException


@inject
@singleton
class BuiltinCategoryManager(BaseModel):
    """内置分类管理"""
    category_map: dict[str, Any] = Field(default_factory=dict)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_categories()

    def get_category_map(self) -> dict[str, Any]:
        """获取所有分类实体列表信息"""
        return self.category_map

    def _init_categories(self):
        """初始化"""
        # 1 检测是否存在
        if self.category_map:
            return

        # 获取yaml 文件路径 加载
        current_path:str = os.path.abspath(__file__)
        categories_path = os.path.dirname(current_path)
        categories_yaml_path = os.path.join(categories_path, "categories.yaml")
        with open(categories_yaml_path,  encoding="utf-8") as f:
            categories = yaml.safe_load(f)


        #  生成生成
        for category in categories:
            category_entity = CategoryEntity(**category)
            #  获取icon
            icon_path = os.path.join(categories_path, "icons", category_entity.icon)
            if not os.path.exists(icon_path):
                raise NotFoundException(f"该分类icon {category_entity.category} 未找到")

            with open(icon_path, encoding="utf-8") as f:
                icon = f.read()


            self.category_map[category_entity.category] = {
                "category": category_entity,
                "icon": icon,
            }
