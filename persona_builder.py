import json
import re
from collections import Counter

class CelebrityPersonaBuilder:
    def __init__(self):
        self.persona_template = {
            "basic_info": {
                "name": "",
                "profession": "",
                "age": "",
                "works": []
            },
            "personality_traits": [],
            "speaking_style": {
                "description": "",
                "common_phrases": [],
                "sentence_patterns": []
            },
            "interests_topics": [],
            "experiences_opinions": [],
            "values_beliefs": []
        }
    
    def build_persona(self, celebrity_data):
        """基于爬取的数据构建明星人设"""
        persona = self.persona_template.copy()
        
        # 提取基本信息
        persona["basic_info"]["name"] = celebrity_data.get("name", "未知")
        persona["basic_info"]["profession"] = self._extract_profession(celebrity_data)
        persona["basic_info"]["age"] = celebrity_data.get("age", "")
        persona["basic_info"]["works"] = celebrity_data.get("works", [])[:5]  # 取前5个作品
        
        # 分析性格特征
        persona["personality_traits"] = self._analyze_personality(celebrity_data)
        
        # 分析语言风格
        persona["speaking_style"] = self._analyze_speaking_style(celebrity_data)
        
        # 提取兴趣话题
        persona["interests_topics"] = self._extract_interests(celebrity_data)
        
        # 提取经历和观点
        persona["experiences_opinions"] = self._extract_experiences(celebrity_data)
        
        # 提取价值观
        persona["values_beliefs"] = self._extract_values(celebrity_data)
        
        return persona
    
    def _extract_profession(self, data):
        """提取职业信息"""
        posts = data.get("posts", [])
        for post in posts:
            if any(profession in post for profession in ["演员", "歌手", "导演", "艺人"]):
                if "演员" in post:
                    return "演员"
                elif "歌手" in post:
                    return "歌手"
                elif "导演" in post:
                    return "导演"
        return "艺人"
    
    def _analyze_personality(self, data):
        """分析性格特征"""
        posts = data.get("posts", [])
        personality_keywords = {
            "开朗": ["开心", "快乐", "高兴", "笑", "幸福"],
            "真诚": ["真心", "真诚", "真实", "坦诚"],
            "努力": ["努力", "奋斗", "坚持", "加油"],
            "感恩": ["感谢", "感恩", "感激", "谢谢"],
            "乐观": ["乐观", "积极", "正能量", "阳光"]
        }
        
        traits = []
        for trait, keywords in personality_keywords.items():
            count = sum(1 for post in posts if any(keyword in post for keyword in keywords))
            if count > len(posts) * 0.1:  # 出现频率超过10%
                traits.append(trait)
        
        return traits if traits else ["亲切", "真诚"]
    
    def _analyze_speaking_style(self, data):
        """分析语言风格"""
        posts = data.get("posts", [])
        
        # 分析常用表达
        all_words = []
        for post in posts:
            words = re.findall(r'[\u4e00-\u9fff]+', post)
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        common_words = [word for word, count in word_freq.most_common(20) if len(word) > 1]
        
        # 分析句子模式
        sentence_patterns = []
        for post in posts[:10]:  # 分析前10条
            if "！" in post:
                sentence_patterns.append("喜欢用感叹号表达情感")
            if "～" in post:
                sentence_patterns.append("喜欢用波浪线显得亲切")
            if "..." in post or "。。。" in post:
                sentence_patterns.append("偶尔用省略号表达思考")
        
        # 去重
        sentence_patterns = list(set(sentence_patterns))
        
        # 构建描述
        description_parts = []
        if any("开心" in post or "高兴" in post for post in posts):
            description_parts.append("语气通常积极向上")
        if any("感谢" in post or "谢谢" in post for post in posts):
            description_parts.append("经常表达感谢")
        if any("！" in post for post in posts):
            description_parts.append("善于用感叹句加强情感表达")
        
        description = "，".join(description_parts) if description_parts else "语气亲切自然，善于与粉丝交流"
        
        return {
            "description": description,
            "common_phrases": common_words[:10],
            "sentence_patterns": sentence_patterns[:5]
        }
    
    def _extract_interests(self, data):
        """提取兴趣话题"""
        posts = data.get("posts", [])
        interest_keywords = {
            "音乐": ["歌", "音乐", "演唱会", "专辑"],
            "电影": ["电影", "电视剧", "剧集", "拍摄"],
            "旅行": ["旅行", "旅游", "风景", "地方"],
            "美食": ["美食", "好吃", "餐厅", "食物"],
            "运动": ["运动", "健身", "跑步", "锻炼"]
        }
        
        interests = []
        for interest, keywords in interest_keywords.items():
            if any(any(keyword in post for keyword in keywords) for post in posts):
                interests.append(interest)
        
        return interests if interests else ["表演", "艺术", "与粉丝互动"]
    
    def _extract_experiences(self, data):
        """提取经历和观点"""
        posts = data.get("posts", [])
        interviews = data.get("interviews", [])
        
        experiences = []
        
        # 从帖子中提取
        for post in posts:
            if any(keyword in post for keyword in ["新剧", "新电影", "新专辑"]):
                experiences.append("经常在社交媒体分享工作进展")
                break
        
        # 从采访中提取
        for interview in interviews[:3]:
            if "角色" in interview:
                experiences.append("重视每一个扮演的角色")
            if "粉丝" in interview:
                experiences.append("珍惜与粉丝之间的感情")
            if "梦想" in interview:
                experiences.append("坚持追求艺术梦想")
        
        return experiences if experiences else [
            "重视表演艺术的追求",
            "感恩粉丝一直以来的支持",
            "努力在演艺道路上不断进步"
        ]
    
    def _extract_values(self, data):
        """提取价值观"""
        posts = data.get("posts", [])
        interviews = data.get("interviews", [])
        
        values = []
        
        # 分析内容中的价值观关键词
        value_keywords = {
            "真诚": ["真诚", "真实", "真心"],
            "努力": ["努力", "坚持", "奋斗"],
            "感恩": ["感恩", "感谢", "感激"],
            "乐观": ["乐观", "积极", "正能量"]
        }
        
        all_text = posts + interviews
        for value, keywords in value_keywords.items():
            if any(any(keyword in text for keyword in keywords) for text in all_text):
                values.append(value)
        
        return values if values else ["真诚待人", "努力进取", "感恩生活"]