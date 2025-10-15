import sqlite3
import json
from datetime import datetime
import os

class MemorySystem:
    def __init__(self, db_path="chat_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建对话记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                context_summary TEXT
            )
        ''')
        
        # 创建用户画像表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                known_interests TEXT,
                conversation_style TEXT,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_interactions INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_id, user_message, bot_response, context_summary=None):
        """保存对话记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (user_id, user_message, bot_response, context_summary)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_message, bot_response, context_summary))
        
        # 更新用户画像
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (user_id, last_interaction, total_interactions)
            VALUES (?, CURRENT_TIMESTAMP, 
                   COALESCE((SELECT total_interactions FROM user_profiles WHERE user_id = ?) + 1, 1))
        ''', (user_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id, limit=5):
        """获取用户对话历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, bot_response 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        # 返回格式：[("用户消息", "回复"), ...]
        return [(msg, resp) for msg, resp in results]
    
    def get_user_profile(self, user_id):
        """获取用户画像"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT known_interests, conversation_style, total_interactions
            FROM user_profiles
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "known_interests": json.loads(result[0]) if result[0] else [],
                "conversation_style": result[1],
                "total_interactions": result[2]
            }
        return None
    
    def update_user_interests(self, user_id, interests):
        """更新用户兴趣"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (user_id, known_interests)
            VALUES (?, ?)
        ''', (user_id, json.dumps(interests, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
    
    def get_conversation_summary(self, user_id, last_n=10):
        """生成对话摘要"""
        history = self.get_conversation_history(user_id, last_n)
        
        if not history:
            return "这是第一次对话"
        
        # 简单的摘要生成（实际可以使用AI生成更复杂的摘要）
        topics = []
        for user_msg, _ in history:
            if any(word in user_msg for word in ["电影", "电视剧", "作品"]):
                topics.append("作品相关")
            elif any(word in user_msg for word in ["生活", "日常", "今天"]):
                topics.append("日常生活")
            elif any(word in user_msg for word in ["音乐", "歌", "演唱会"]):
                topics.append("音乐相关")
        
        unique_topics = list(set(topics))
        summary = f"最近聊过：{', '.join(unique_topics)}" if unique_topics else "对话内容多样"
        
        return summary