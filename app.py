"""
app.py
Flask 后端 - 课程评论情感分析 API（带自定义情感词典）
"""
from flask import Flask, render_template, request, jsonify
from snownlp import SnowNLP
from snownlp import sentiment
import os

app = Flask(__name__)

# ============================================================
# 课程领域自定义情感词典（让评分更准确）
# ============================================================

# 正面词（加分）
positive_words = [
    '好评', '推荐', '超赞', '物超所值', '受益匪浅', '干货满满',
    '通俗易懂', '深入浅出', '醍醐灌顶', '茅塞顿开', '精彩', '满分',
    '清晰', '详细', '耐心', '负责', '实用', '充实', '生动',
    '幽默', '风趣', '严谨', '系统', '全面', '前沿', '创新',
    '有条理', '重点突出', '案例丰富', '收获很大', '零基础',
    '听懂', '学会', '掌握', '进步', '提升', '通过', '考过',
    '讲得好', '讲得清楚', '讲得细', '很棒', '很好', '非常好',
    '特别好', '太好了', '不错', '还行', '可以', '满意',
    '喜欢', '爱了', '赞', '顶', '牛', '强', '厉害', '优秀',
    '质量高', '水平高', '性价比高', '值得', '良心', '用心',
    '细心', '贴心', '及时', '回复快', '答疑好', '互动好',
    '氛围好', '课程好', '老师好', '内容好', '平台好',
]

# 负面词（扣分）
negative_words = [
    '差评', '后悔', '浪费', '不值', '别买', '别学', '避坑',
    '听不懂', '跟不上', '太慢', '太啰嗦', '念稿', '照本宣科',
    '枯燥', '无聊', '催眠', '犯困', '没意思', '没收获',
    '敷衍', '不负责任', '不理人', '不回', '答疑差', '态度差',
    '内容旧', '过时', '太浅', '太简单', '太基础', '没深度',
    '太水', '注水', '水分大', '坑', '骗', '假', '虚',
    '看不清楚', '音质差', '卡顿', '字幕错', '错别字', '错误多',
    '没用', '学不到', '白学', '浪费时间', '浪费钱', '不值得',
    '贵', '性价比低', '失望', '不满意', '不好', '很差', '太差',
    '极差', '烂', '糟糕', '无语', '醉了', '服了',
]

# 程度副词（增强情感强度）
intensifiers = {
    '非常': 1.5, '特别': 1.5, '极其': 1.6, '十分': 1.4,
    '很': 1.3, '太': 1.3, '真': 1.2, '好': 1.2,
    '挺': 1.1, '比较': 1.0, '有点': 0.8, '稍微': 0.7,
}

# 否定词（反转情感）
negation_words = {'不', '没', '无', '非', '别', '未', '莫', '勿'}

# 将自定义词典注入 SnowNLP
for word in positive_words:
    sentiment.train.add(word, '正面')
for word in negative_words:
    sentiment.train.add(word, '负面')

# 重新训练情感模型
sentiment.train.classify()


# ============================================================
# 情感分析函数
# ============================================================

def analyze_single_review(text, pos_threshold=0.6, neg_threshold=0.4):
    """分析单条评论（结合 SnowNLP + 自定义规则）"""
    
    # 1. SnowNLP 基础打分
    s = SnowNLP(text)
    base_score = s.sentiments
    
    # 2. 自定义规则打分（关键词匹配 + 程度修饰）
    rule_score = 0.5  # 从 0.5（中性）开始
    hit_count = 0
    
    for word in positive_words:
        if word in text:
            # 检查前面是否有否定词或程度副词
            idx = text.find(word)
            before = text[max(0, idx-2):idx]
            
            if any(neg in before for neg in negation_words):
                rule_score -= 0.3
            else:
                # 检查程度副词
                intensity = 1.0
                for adv, factor in intensifiers.items():
                    if adv in text[max(0, idx-3):idx]:
                        intensity = factor
                        break
                rule_score += 0.25 * intensity
            hit_count += 1
    
    for word in negative_words:
        if word in text:
            idx = text.find(word)
            before = text[max(0, idx-2):idx]
            
            if any(neg in before for neg in negation_words):
                rule_score += 0.3  # "不差" = 正面
            else:
                intensity = 1.0
                for adv, factor in intensifiers.items():
                    if adv in text[max(0, idx-3):idx]:
                        intensity = factor
                        break
                rule_score -= 0.25 * intensity
            hit_count += 1
    
    # 限制规则分数范围
    rule_score = max(0, min(1, rule_score))
    
    # 3. 综合打分：SnowNLP 权重 0.6，规则权重 0.4
    if hit_count > 0:
        final_score = round(base_score * 0.6 + rule_score * 0.4, 4)
    else:
        final_score = round(base_score, 4)
    
    # 4. 分类
    if final_score > pos_threshold:
        label = "正面 😊"
        color = "#4CAF50"
    elif final_score < neg_threshold:
        label = "负面 😞"
        color = "#F44336"
    else:
        label = "中性 😐"
        color = "#FF9800"
    
    confidence = round(abs(final_score - 0.5) * 2, 4)
    
    return {
        "score": final_score,
        "label": label,
        "color": color,
        "confidence": confidence
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
