import os.path
from typing import Any

import yaml
from injector import inject, singleton
from internal.core.tools.builtin_tools.entities import ProviderEntity, Provider




@singleton
@inject
class BuiltinProviderManager:
    """"""

    provider_map: dict[str, Provider] = {}

    def __init__(self):
        """构造函数初始化对应的providermap"""
        self._get_provider_tool_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据服务提供商名字获取服务提供商"""
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        """获取所有服务提供商列表"""
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        """获取所有服务提供商实体列表信息"""
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name, tool_name) -> Any:
        """根据服务提供商名字和工具名字获取工具"""
        provider = self.get_provider(provider_name)
        if provider is None:
            return None

        return provider.get_tool(tool_name)

    def _get_provider_tool_map(self):
        """初始化  填充映射关系"""
        if self.provider_map:
            return


        # 获取类的当前路径
        current_path = os.path.abspath(__file__)
        providers_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        # 读取yaml 数据
        with open(providers_yaml_path, "r", encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity
            )