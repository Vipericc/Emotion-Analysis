"""
app.py
Flask 后端 - 课程评论情感分析 API
"""
from flask import Flask, render_template, request, jsonify
from snownlp import SnowNLP

app = Flask(__name__)


def analyze_single_review(text, pos_threshold=0.6, neg_threshold=0.4):
    """分析单条评论"""
    s = SnowNLP(text)
    score = round(s.sentiments, 4)

    if score > pos_threshold:
        label = "正面 😊"
        color = "#4CAF50"
    elif score < neg_threshold:
        label = "负面 😞"
        color = "#F44336"
    else:
        label = "中性 😐"
        color = "#FF9800"

    confidence = round(abs(score - 0.5) * 2, 4)

    return {
        "score": score,
        "label": label,
        "color": color,
        "confidence": confidence
    }


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """情感分析 API"""
    data = request.get_json()
    text = data.get('text', '').strip()

    if len(text) < 4:
        return jsonify({"error": "评论太短，至少输入4个字"}), 400

    result = analyze_single_review(text)
    result["text"] = text
    return jsonify(result)


if __name__ == '__main__':
    print("=" * 50)
    print("  课程评论情感分析服务已启动")
    print("  访问地址：http://127.0.0.1:8080")
    print("=" * 50)
    app.run(debug=False, port=8080)