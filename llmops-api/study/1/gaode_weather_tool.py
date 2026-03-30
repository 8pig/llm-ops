import json
from typing import Type, Any

import requests
from flask import session
from pydantic import BaseModel, Field
import  dotenv
import os

class GaodeWeatherArgusSchema(BaseModel):
    city: str = Field(..., description="城市名称 例如: 广告")


class GaodeWeatherTool(BaseModel):
    """
    根据传入城市名 查询天气
    高德天气查询工具
    """
    name: str = "gade_weather"
    description: str = "根据传入城市名 获取天气"
    args_schema: Type[BaseModel] = GaodeWeatherArgusSchema

    def _run(self, *args, **kwargs) -> Any:
        gaode_api_key = os.getenv("GAODE_API_KEY")
        if not gaode_api_key:
            raise Exception("请设置环境变量 GAODE_API_KEY")

        city = kwargs.get("city")
        if not city:
            raise ValueError("必须提供 city 参数")

        api_domain = "https://restapi.amap.com/v3"
        requests_session = requests.session()

        try:
            # 获取城市编码
            city_response = requests_session.request(
                "get",
                f"{api_domain}/config/district?key={gaode_api_key}&keywords={city}&subdistrict=0",
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10
            )
            city_response.raise_for_status()
            city_data = city_response.json()

            if city_data.get("info") != "OK" or not city_data.get("districts"):
                return f"未找到城市：{city}"

            city_code = city_data.get("districts")[0].get("adcode")

            # 获取天气信息
            weather_response = requests_session.request(
                "get",
                f"{api_domain}/weather/weatherInfo?key={gaode_api_key}&city={city_code}&extensions=all",
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            if weather_data.get("info") == "OK":
                return json.dumps(weather_data, ensure_ascii=False)
            return f"获取{city}天气失败"

        except requests.exceptions.RequestException as e:
            return f"请求失败：{str(e)}"
        except Exception as e:
            return f"发生错误：{str(e)}"

    def invoke(self, *args, **kwargs) -> Any:
        """调用工具"""
        return self._run(*args, **kwargs)


gaode_weather = GaodeWeatherTool()
print(gaode_weather.invoke(city="上海"))

gaode_weather = GaodeWeatherTool()
print(gaode_weather.invoke(city="上海"))