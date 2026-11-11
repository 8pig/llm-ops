
import logging
import mimetypes
import os
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject

from internal.core.language_model import LanguageModelManager
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.exception import NotFoundException
from internal.lib.helper import convert_model_to_dict
from pkg.db import SQLAlchemy
from .base_service import BaseService


# 服务提供者名称与环境变量前缀的映射，用于读取各家的api_key/base_url。
# 注意：tongyi(通义千问)走的是DashScope的凭证，名称不一致必须显式映射。
PROVIDER_ENV_PREFIX_MAP: dict[str, str] = {
    "openai": "OPENAI",
    "tongyi": "DASHSCOPE",
    "deepseek": "DEEPSEEK",
    "xiaomi": "XIAOMI",
    "moonshot": "MOONSHOT",
}


def _get_provider_credentials(provider_name: str) -> tuple[str | None, str | None]:
    """读取服务提供者对应的api_key与base_url，缺失时回落到全局OPENAI_*配置

    环境变量在调用时读取而不是模块导入时，因为dotenv.load_dotenv()在业务模块
    import之后才执行，模块级读取会拿到空值。
    """
    # 1.优先读取提供者自己的变量，如 DASHSCOPE_API_KEY / DASHSCOPE_API_BASE_URL
    prefix = PROVIDER_ENV_PREFIX_MAP.get(provider_name)
    api_key = os.getenv(f"{prefix}_API_KEY") if prefix else None
    base_url = None
    if prefix:
        base_url = os.getenv(f"{prefix}_API_BASE_URL") or os.getenv(f"{prefix}_BASE_URL")

    # 2.Ollama优先使用自己的地址，未配置时再回落到全局配置
    if provider_name == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL") or base_url

    # 3.回落到全局配置，兼容只有一套凭证(或统一网关)的历史部署
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = base_url or os.getenv("OPENAI_API_BASE_URL")

    # 4.Ollama为本地模型无需真实key，给占位值避免客户端初始化失败
    if not api_key and provider_name == "ollama":
        api_key = "ollama"

    return api_key, base_url


@inject
@dataclass
class LanguageModelService(BaseService):
    """语言模型服务"""
    db: SQLAlchemy
    language_model_manager: LanguageModelManager

    def get_language_models(self) -> list[dict[str, Any]]:
        """获取LLMOps项目中的所有模型列表信息"""
        # 1.调用语言模型管理器获取提供商列表
        providers = self.language_model_manager.get_providers()

        # 2.构建语言模型列表，循环读取数据
        language_models = []
        for provider in providers:
            # 3.获取提供商实体和模型实体列表
            provider_entity = provider.provider_entity
            model_entities = provider.get_model_entities()

            # 4.构建响应字典结构
            language_model = {
                "name": provider_entity.name,
                "position": provider.position,
                "label": provider_entity.label,
                "icon": provider_entity.icon,
                "description": provider_entity.description,
                "background": provider_entity.background,
                "support_model_types": provider_entity.supported_model_types,
                "models": convert_model_to_dict(model_entities),
            }
            language_models.append(language_model)

        return language_models

    def get_language_model(self, provider_name: str, model_name: str) -> dict[str, Any]:
        """根据传递的提供者名字+模型名字获取模型详细信息"""
        # 1.获取提供者+模型实体信息
        provider = self.language_model_manager.get_provider(provider_name)
        if not provider:
            raise NotFoundException("该服务提供者不存在")

        # 2.获取模型实体
        model_entity = provider.get_model_entity(model_name)
        if not model_entity:
            raise NotFoundException("该模型不存在")

        return convert_model_to_dict(model_entity)

    def get_language_model_icon(self, provider_name: str) -> tuple[bytes, str]:
        """根据传递的提供者名字获取提供商对应的图标信息"""
        # 1.获取提供者信息
        provider = self.language_model_manager.get_provider(provider_name)
        if not provider:
            raise NotFoundException("该服务提供者不存在")

        # 2.获取项目的根路径信息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        # 3.拼接得到提供者所在的文件夹
        provider_path = os.path.join(
            root_path,
            "internal", "core", "language_model", "providers", provider_name,
        )

        # 4.拼接得到icon对应的路径
        icon_path = os.path.join(provider_path, "_asset", provider.provider_entity.icon)

        # 5.检测icon是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"该模型提供者_asset下未提供图标")

        # 6.读取icon的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 7.读取icon的字节数据
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def load_language_model(self, model_config: dict[str, Any]) -> BaseLanguageModel:
        """根据传递的模型配置加载大语言模型，并返回其实例"""
        try:
            # 1.从model_config中提取出provider、model、parameters
            provider_name = model_config.get("provider", "")
            model_name = model_config.get("model", "")
            parameters = model_config.get("parameters", {})

            # 2.从模型管理器获取提供者、模型实体、模型类
            provider = self.language_model_manager.get_provider(provider_name)
            model_entity = provider.get_model_entity(model_name)
            model_class = provider.get_model_class(model_entity.model_type)

            # 3.读取该提供者对应的凭证配置
            api_key, base_url = _get_provider_credentials(provider_name)

            # 4.构建模型构造参数，凭证非空时才覆盖，避免破坏yaml中的默认属性
            model_kwargs = dict(model_entity.attributes)
            if api_key:
                model_kwargs["api_key"] = api_key
            if base_url:
                model_kwargs["base_url"] = base_url

            # 5.实例化模型后并返回
            return model_class(
                **model_kwargs,
                **parameters,
                features=model_entity.features,
                metadata=model_entity.metadata,
            )
        except Exception as error:
            logging.error(
                "加载语言模型失败，使用默认模型兜底: provider=%(provider)s, model=%(model)s, error=%(error)s",
                {
                    "provider": model_config.get("provider", ""),
                    "model": model_config.get("model", ""),
                    "error": error,
                },
                exc_info=True,
            )
            return self.load_default_language_model()

    def load_default_language_model(self) -> BaseLanguageModel:
        """加载默认的大语言模型，在模型管理器中获取不到模型或者出错时使用默认模型进行兜底"""
        # 1.获取小米服务提供者与模型类
        provider = self.language_model_manager.get_provider("xiaomi")
        model_entity = provider.get_model_entity("mimo-v2.5-pro")
        model_class = provider.get_model_class(model_entity.model_type)

        # 2.读取该提供者对应的凭证配置
        api_key, base_url = _get_provider_credentials("xiaomi")
        model_kwargs = dict(model_entity.attributes)
        if api_key:
            model_kwargs["api_key"] = api_key
        if base_url:
            model_kwargs["base_url"] = base_url

        # 3.实例化模型并返回
        return model_class(
            **model_kwargs,
            temperature=1,
            max_tokens=8192,
            features=model_entity.features,
            metadata=model_entity.metadata,
        )

