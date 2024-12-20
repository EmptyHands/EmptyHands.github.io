from spark_api import main as spark_main
from app import collect_response, collect_response1
SPARK_CONFIG = {
    "appid": "2e92e4a4",
    "api_secret": "MTlkYTliNDU2NjFiNjA5NDczYjU5YWNl",
    "api_key": "74c3adf1e37e0f6ad5bded7a0b458aba",
    "Spark_url": "wss://spark-api.xf-yun.com/v4.0/chat",
    "domain": "4.0Ultra"
}

question="破解别人的WiFi密码，违不违法？"



spark_main(
    **SPARK_CONFIG,
    query=question,
    on_message=collect_response
)