"""
app.py
Flask 后端 - 课程评论情感分析 API（测试版）
"""
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """测试 API - 直接返回固定结果"""
    data = request.get_json()
    text = data.get('text', '').strip()

    if len(text) < 4:
        return jsonify({"error": "评论太短，至少输入4个字"}), 400

    return jsonify({
        "text": text,
        "score": 0.85,
        "label": "正面 😊",
        "color": "#4CAF50",
        "confidence": 0.7
    })


@app.route('/health')
def health():
    return "OK"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
