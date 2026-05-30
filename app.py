"""
app.py
Flask 后端 - 课程评论情感分析 API（纯规则引擎，稳定版）
"""
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# ============================================================
# 课程领域情感词典
# ============================================================

# 正面词 + 权重
positive_words = {
    '好评': 0.8, '推荐': 0.7, '超赞': 0.9, '物超所值': 0.9, '受益匪浅': 0.85,
    '干货': 0.8, '干货满满': 0.9, '通俗易懂': 0.85, '深入浅出': 0.9,
    '醍醐灌顶': 0.95, '茅塞顿开': 0.9, '精彩': 0.8, '满分': 0.95,
    '清晰': 0.6, '详细': 0.5, '耐心': 0.7, '负责': 0.7, '实用': 0.7,
    '充实': 0.6, '生动': 0.7, '幽默': 0.6, '风趣': 0.7, '严谨': 0.5,
    '系统': 0.5, '全面': 0.6, '前沿': 0.7, '创新': 0.6,
    '有条理': 0.7, '重点突出': 0.7, '案例丰富': 0.7, '收获': 0.7,
    '零基础': 0.5, '听懂': 0.6, '学会': 0.6, '掌握': 0.6,
    '进步': 0.6, '提升': 0.6, '通过': 0.6, '考过': 0.7,
    '讲得好': 0.8, '很清楚': 0.7, '很详细': 0.7, '很棒': 0.85,
    '很好': 0.7, '非常好': 0.8, '特别好': 0.9, '太好了': 0.9,
    '满意': 0.6, '喜欢': 0.7, '爱了': 0.9, '赞': 0.6,
    '厉害': 0.7, '优秀': 0.8, '质量高': 0.8, '性价比': 0.7,
    '值得': 0.7, '良心': 0.8, '用心': 0.7, '贴心': 0.7,
    '及时': 0.5, '回复快': 0.7, '答疑好': 0.7, '互动': 0.5,
    '氛围好': 0.7, '不错': 0.5, '可以': 0.3, '还行': 0.2,
}

# 负面词 + 权重
negative_words = {
    '差评': -0.8, '后悔': -0.9, '浪费': -0.8, '不值': -0.8, '别买': -0.9,
    '别学': -0.9, '避坑': -0.8, '听不懂': -0.8, '跟不上': -0.7,
    '太快': -0.6, '太慢': -0.6, '啰嗦': -0.7, '念稿': -0.8,
    '照本宣科': -0.85, '枯燥': -0.7, '无聊': -0.7, '催眠': -0.8,
    '犯困': -0.7, '没意思': -0.7, '没收获': -0.8, '敷衍': -0.85,
    '不负责': -0.9, '不理人': -0.8, '不回': -0.7, '答疑差': -0.8,
    '态度差': -0.85, '内容旧': -0.7, '过时': -0.8, '太浅': -0.6,
    '太简单': -0.5, '没深度': -0.7, '太水': -0.8, '注水': -0.8,
    '坑': -0.8, '骗': -0.95, '假': -0.8, '看不清楚': -0.7,
    '音质差': -0.7, '卡顿': -0.7, '字幕错': -0.6, '错误': -0.6,
    '没用': -0.8, '学不到': -0.85, '白学': -0.9, '浪费时间': -0.9,
    '浪费钱': -0.95, '贵': -0.5, '性价比低': -0.7, '失望': -0.85,
    '不满意': -0.8, '不好': -0.6, '很差': -0.85, '太差': -0.9,
    '极差': -0.95, '烂': -0.9, '糟糕': -0.9, '无语': -0.7,
}

# 程度副词乘数
intensifiers = {
    '非常': 1.5, '特别': 1.5, '极其': 1.6, '十分': 1.4,
    '很': 1.3, '太': 1.3, '真': 1.2, '好': 1.2,
    '挺': 1.1, '比较': 1.0, '有点': 0.7, '稍微': 0.6,
}

# 否定词（反转情感）
negation_words = {'不', '没', '无', '非', '别', '未', '莫', '勿', '并不是', '没有'}


# ============================================================
# 情感分析函数
# ============================================================

def analyze_single_review(text, pos_threshold=0.6, neg_threshold=0.4):
    """纯规则引擎情感分析"""
    total_score = 0.5  # 从 0.5 中性开始
    hit_count = 0

    # 扫描正面词
    for word, weight in positive_words.items():
        if word in text:
            idx = text.find(word)
            # 检查否定词（前3个字符内）
            before_start = max(0, idx - 3)
            before = text[before_start:idx]
            if any(neg in before for neg in negation_words):
                total_score -= weight * 0.5  # 否定翻转，打五折
            else:
                # 检查程度副词
                multiplier = 1.0
                for adv, factor in intensifiers.items():
                    if adv in text[max(0, idx-3):idx]:
                        multiplier = factor
                        break
                total_score += weight * multiplier
            hit_count += 1

    # 扫描负面词
    for word, weight in negative_words.items():
        if word in text:
            idx = text.find(word)
            before_start = max(0, idx - 3)
            before = text[before_start:idx]
            if any(neg in before for neg in negation_words):
                # 否定 + 负面 = 正面（如"不差"）
                total_score += abs(weight) * 0.5
            else:
                multiplier = 1.0
                for adv, factor in intensifiers.items():
                    if adv in text[max(0, idx-3):idx]:
                        multiplier = factor
                        break
                total_score += weight * multiplier  # weight 已经是负数
            hit_count += 1

    # 限制范围
    total_score = max(0.05, min(0.95, total_score))
    final_score = round(total_score, 4)

    # 分类
    if final_score > pos_threshold:
        label, color = "正面 😊", "#4CAF50"
    elif final_score < neg_threshold:
        label, color = "负面 😞", "#F44336"
    else:
        label, color = "中性 😐", "#FF9800"

    confidence = round(abs(final_score - 0.5) * 2, 4)

    return {
        "score": final_score,
        "label": label,
        "color": color,
        "confidence": confidence,
        "hits": hit_count
    }


# ============================================================
# Flask 路由
# ============================================================

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


# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
