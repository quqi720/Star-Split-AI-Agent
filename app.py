from flask import Flask, request, jsonify, render_template, session
import json
import os
import requests  # 改为使用requests库
from datetime import datetime
from persona_builder import CelebrityPersonaBuilder
from memory_system import MemorySystem
from scraper import CelebrityDataScraper

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 初始化组件
persona_builder = CelebrityPersonaBuilder()
memory_system = MemorySystem()
scraper = CelebrityDataScraper()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-5758a530c77d455a82784755ecfb6bc4')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class CelebrityAgent:
    def __init__(self, celebrity_name):
        self.celebrity_name = celebrity_name
        self.persona = None
        self.load_or_create_persona()

    def load_or_create_persona(self):
        """加载或创建明星人设"""
        persona_file = f"personas/{self.celebrity_name}_persona.json"

        if os.path.exists(persona_file):
            with open(persona_file, 'r', encoding='utf-8') as f:
                self.persona = json.load(f)
        else:
            # 从网络爬取数据构建人设
            celebrity_data = scraper.scrape_celebrity_data(self.celebrity_name)
            self.persona = persona_builder.build_persona(celebrity_data)

            # 保存人设
            os.makedirs('personas', exist_ok=True)
            with open(persona_file, 'w', encoding='utf-8') as f:
                json.dump(self.persona, f, ensure_ascii=False, indent=2)

    def generate_response(self, user_message, user_id):
        """生成明星风格的回答"""
        # 获取对话历史
        conversation_history = memory_system.get_conversation_history(user_id, limit=5)

        # 构建Prompt
        prompt = self._build_prompt(user_message, conversation_history)

        try:
            # 调用DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt["system_prompt"]},
                    {"role": "user", "content": prompt["user_prompt"]}
                ],
                "temperature": 0.8,
                "max_tokens": 500,
                "stream": False
            }

            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()  # 如果状态码不是200，抛出异常

            result = response.json()
            reply = result["choices"][0]["message"]["content"].strip()

            # 保存对话
            memory_system.save_conversation(user_id, user_message, reply)

            return reply

        except requests.exceptions.Timeout:
            print("DeepSeek API请求超时")
            return "抱歉，我现在有点忙，网络连接不太稳定，稍后再聊吧～"
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API请求错误: {e}")
            return "抱歉，服务暂时不可用，请稍后再试～"
        except Exception as e:
            print(f"DeepSeek API调用错误: {e}")
            # 备用回复
            backup_responses = [
                "谢谢你的支持！我会继续努力给大家带来好作品的～",
                "最近在准备新作品，希望大家会喜欢",
                "感恩有你们这些可爱的粉丝一路相伴",
                "保持积极心态，生活会更美好哦",
                "工作虽然忙，但看到大家的支持就很开心"
            ]
            import random
            return random.choice(backup_responses)

    def _build_prompt(self, user_message, conversation_history):
        """构建模拟明星的Prompt"""

        # 系统Prompt - 定义角色
        system_prompt = f"""
        你现在是{self.persona['basic_info']['name']}，一位{self.persona['basic_info']['profession']}。

        基本信息：
        - 年龄：{self.persona['basic_info'].get('age', '未知')}
        - 代表作品：{', '.join(self.persona['basic_info'].get('works', []))}
        - 性格特点：{', '.join(self.persona['personality_traits'])}

        语言风格：
        {self.persona['speaking_style']['description']}

        常用表达方式：
        {chr(10).join(f"- {phrase}" for phrase in self.persona['speaking_style'].get('common_phrases', []))}

        重要经历和观点：
        {chr(10).join(f"- {exp}" for exp in self.persona['experiences_opinions'])}

        请严格保持角色设定，用第一人称回复，保持自然真实的对话风格。不要暴露你是AI的事实。
        """

        # 用户Prompt - 添加上下文和当前消息
        context = "之前的对话：\n"
        for i, (msg, resp) in enumerate(reversed(conversation_history)):
            context += f"粉丝：{msg}\n"
            context += f"你：{resp}\n"
            if i >= 2:  # 只保留最近3轮对话作为上下文
                break

        user_prompt = f"{context}\n当前粉丝说：{user_message}\n\n你的回复："

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }


# 创建明星Agent实例（这里以"赵丽颖"为例，可以替换为任何明星）
celebrity_agent = CelebrityAgent("赵丽颖")


@app.route('/')
def index():
    # 生成用户ID（如果不存在）
    if 'user_id' not in session:
        session['user_id'] = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"

    return render_template('index.html',
                           celebrity_name=celebrity_agent.celebrity_name,
                           user_id=session['user_id'])


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    user_id = request.json.get('user_id', 'default_user')

    if not user_message.strip():
        return jsonify({'response': '你好，请说点什么吧～'})

    # 生成回复
    response = celebrity_agent.generate_response(user_message, user_id)

    return jsonify({'response': response})


@app.route('/memory/<user_id>')
def get_memory(user_id):
    """获取用户的对话记忆（用于调试）"""
    memory = memory_system.get_conversation_history(user_id, limit=10)
    return jsonify(memory)


@app.route('/persona')
def get_persona():
    """获取当前明星的人设信息（用于调试）"""
    return jsonify(celebrity_agent.persona)


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Celebrity Agent is running!'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', False))