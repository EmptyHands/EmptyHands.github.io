import _thread as thread

import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket



class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, gpt_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.gpt_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    print("### WebSocket连接已建立")
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    # print("### 进入run函数，开始准备发送数据")
    data = json.dumps(gen_params(appid=ws.appid, query=ws.query, domain=ws.domain))
    # print("### 已生成要发送的数据，准备发送")
    ws.send(data)
    # print("### 数据已发送成功")


# 收到websocket消息的处理
def on_message_default(ws, message):
    # print("### message:", message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content, end='')
        if status == 2:
            print("#### 关闭会话")
            ws.close()


def gen_params(appid, query, domain):
    """
    通过appid和用户的提问来生成请参数
    """

    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 0.5,
                "max_tokens": 1024,
                "auditing": "default",
            }
        },
        "payload": {
            "message": {
                "text": [
                    {"role": "system", "content": "你现在是一个咨询律师，因为我对法律专业知识一无所知，所以请对我的法律咨询进行简明扼要的回答"},
                    {"role": "user", "content": query}
                ]
            }
        }
    }
    return data


def main(appid, api_secret, api_key, Spark_url, domain, query, on_message=None):
    print('Q:', query)
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    
    # 如果提供了自定义的on_message回调，使用它
    message_callback = on_message if on_message else on_message_default

    ws = websocket.WebSocketApp(
        wsUrl, 
        on_message=message_callback,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.appid = appid
    print('app_id:', ws.appid)
    ws.query = query
    print('query:', ws.query)
    ws.domain = domain
    print('domain:', ws.domain)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


if __name__ == "__main__":
    main(
        appid="2e92e4a4",
        api_secret="MTlkYTliNDU2NjFiNjA5NDczYjU5YWNl",
        api_key="74c3adf1e37e0f6ad5bded7a0b458aba",
        Spark_url="wss://spark-api.xf-yun.com/v4.0/chat",
        domain="4.0Ultra",
        query="破解别人的WiFi密码，违不违法？"
    )
