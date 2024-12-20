from flask import Flask, render_template, request, jsonify
from spark_api import main as spark_main
import queue
import threading
import json

app = Flask(__name__)

# 用于存储API响应的队列
response_queue = queue.Queue()

# 存储API配置
SPARK_CONFIG = {
    "appid": "2e92e4a4",
    "api_secret": "MTlkYTliNDU2NjFiNjA5NDczYjU5YWNl",
    "api_key": "74c3adf1e37e0f6ad5bded7a0b458aba",
    "Spark_url": "wss://spark-api.xf-yun.com/v4.0/chat",
    "domain": "4.0Ultra"
}

def collect_response(ws, message):
    """websocket消息处理函数"""
    data = json.loads(message)
    # print(f"收到消息: {message}")
    code = data['header']['code']
    if code != 0:
        response_queue.put({"error": f"请求错误: {code}"})
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        response_queue.put({"content": content, "status": status})
        if status == 2:
            ws.close()

def collect_response1(ws, message):
    print("### message:", message)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    # 清空队列
    while not response_queue.empty():
        response_queue.get()

    # 在新线程中调用API
    def api_thread():
        try:
            spark_main(
                **SPARK_CONFIG,
                query=question,
                on_message=collect_response
            )
        except Exception as e:
            response_queue.put({"error": str(e)})

    threading.Thread(target=api_thread).start()

    # 收集完整响应
    full_response = ""
    while True:
        try:
            response = response_queue.get(timeout=30)  # 30秒超时
            if "error" in response:
                return jsonify({"error": response["error"]}), 500
            
            full_response += response.get("content", "")
            if response.get("status") == 2:
                break
                
        except queue.Empty:
            return jsonify({"error": "请求超时"}), 504

    return jsonify({"response": full_response})

if __name__ == '__main__':
    app.run(debug=True)