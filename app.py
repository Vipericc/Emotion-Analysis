"""
app.py
Flask 后端 - 课程评论情感分析 API
"""
from flask import Flask, render_template, request, jsonify
from snownlp import SnowNLP
import os

app = Flask(__name__)


def analyze_single_review(text, pos_threshold=0.6, neg_threshold=0.4):
    s = SnowNLP(text)
    score = round(s.sentiments, 4)
    if score > pos_threshold:
        label, color = "正面 😊", "#4CAF50"
    elif score < neg_threshold:
        label, color = "负面 😞", "#F44336"
    else:
        label, color = "中性 😐", "#FF9800"
    confidence = round(abs(score - 0.5) * 2, 4)
    return {"score": score, "label": label, "color": color, "confidence": confidence}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '').strip()
    if len(text) < 4:
        return jsonify({"error": "评论太短，至少输入4个字"}), 400
    result = analyze_single_review(text)
    result["text"] = text
    return jsonify(result)


if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    serve(app, host='0.0.0.0', port=port)
