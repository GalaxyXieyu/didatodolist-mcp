"""
文本分析工具
提供分词、关键词提取和相似度计算功能
"""

import re
import math
import jieba
import jieba.analyse
from typing import List, Dict, Tuple, Set, Optional, Union, Any
from collections import Counter


# 确保jieba加载完成
jieba.setLogLevel(20)  # 设置日志级别为INFO，避免过多的输出

# 停用词集
STOP_WORDS = set([
    '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
    '或', '一个', '没有', '我们', '你们', '他们', '她们', '它们',
    '这个', '那个', '这些', '那些', '这样', '那样', '不', '在',
    '我', '你', '他', '她', '它', '这', '那', '有', '个',
    '要', '去', '来', '到', '会', '用', '第', '从', '给',
    '被', '让', '但', '因为', '所以', '如果', '虽然', '于是',
    '可以', '可能', '应该', '需要', '由于', '因此'
])


def load_stop_words(file_path: Optional[str] = None) -> Set[str]:
    """
    加载停用词表
    
    Args:
        file_path: 停用词文件路径，如果未提供则使用内置停用词
    
    Returns:
        停用词集合
    """
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = set([line.strip() for line in f.readlines()])
                return words
        except Exception as e:
            print(f"加载停用词文件失败: {e}")
            
    return STOP_WORDS


def segment_text(text: str, stop_words: Optional[Set[str]] = None) -> List[str]:
    """
    对文本进行分词
    
    Args:
        text: 要分词的文本
        stop_words: 停用词集合，如果未提供则使用默认停用词
    
    Returns:
        分词结果列表
    """
    if stop_words is None:
        stop_words = STOP_WORDS
    
    # 清理文本
    text = clean_text(text)
    
    # 使用jieba分词
    seg_list = jieba.cut(text)
    
    # 过滤停用词和空字符
    filtered_words = []
    for word in seg_list:
        if word not in stop_words and word.strip():
            filtered_words.append(word)
    
    return filtered_words


def clean_text(text: str) -> str:
    """
    清理文本，去除特殊字符和多余空格
    
    Args:
        text: 要清理的文本
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 将多个空白字符替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 去除标点符号(保留中文字符、英文字母、数字和空格)
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    
    return text.strip()


def extract_keywords(text: str, top_k: int = 10, with_weight: bool = False) -> Union[List[str], List[Tuple[str, float]]]:
    """
    提取文本关键词
    
    Args:
        text: 文本内容
        top_k: 返回的关键词数量
        with_weight: 是否返回权重
    
    Returns:
        关键词列表，如果with_weight为True则返回(关键词, 权重)元组列表
    """
    if not text:
        return [] if not with_weight else []
    
    # 使用TF-IDF算法提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=with_weight)
    
    return keywords


def extract_keywords_from_tasks(tasks: List[Dict[str, Any]], fields: List[str] = ['title', 'content'],
                               top_k: int = 20) -> Dict[str, int]:
    """
    从任务列表中提取关键词
    
    Args:
        tasks: 任务列表，每个任务是一个字典
        fields: 要分析的字段列表
        top_k: 返回的关键词数量
    
    Returns:
        关键词频率字典
    """
    # 合并所有文本
    all_text = ""
    for task in tasks:
        for field in fields:
            if field in task and task[field]:
                all_text += task[field] + " "
    
    # 分词
    words = segment_text(all_text)
    
    # 统计词频
    word_counts = Counter(words)
    
    # 返回出现频率最高的词
    return dict(word_counts.most_common(top_k))


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度(余弦相似度)
    
    Args:
        text1: 文本1
        text2: 文本2
    
    Returns:
        相似度得分(0-1之间)
    """
    # 分词
    words1 = segment_text(text1)
    words2 = segment_text(text2)
    
    # 如果其中一个文本为空，则相似度为0
    if not words1 or not words2:
        return 0.0
    
    # 创建词频向量
    word_set = set(words1) | set(words2)
    
    # 计算词频
    word_freq1 = Counter(words1)
    word_freq2 = Counter(words2)
    
    # 创建向量
    vector1 = [word_freq1.get(word, 0) for word in word_set]
    vector2 = [word_freq2.get(word, 0) for word in word_set]
    
    # 计算余弦相似度
    dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
    
    # 计算向量模长
    magnitude1 = math.sqrt(sum(v**2 for v in vector1))
    magnitude2 = math.sqrt(sum(v**2 for v in vector2))
    
    # 避免除零错误
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def match_keywords(text: str, keywords: List[str]) -> float:
    """
    计算文本与关键词列表的匹配度
    
    Args:
        text: 文本内容
        keywords: 关键词列表
    
    Returns:
        匹配度得分(0-1之间)，表示包含关键词的比例
    """
    if not text or not keywords:
        return 0.0
    
    # 分词
    words = set(segment_text(text))
    
    # 处理关键词
    keyword_set = set(keywords)
    
    # 计算匹配的关键词数量
    matched = sum(1 for keyword in keyword_set if keyword in words)
    
    # 返回匹配比例
    return matched / len(keyword_set) if keyword_set else 0.0


def normalize_keywords(keywords: Union[str, List[str]]) -> List[str]:
    """
    归一化关键词，将逗号分隔的字符串转为列表，并去重和清理
    
    Args:
        keywords: 关键词字符串或列表
    
    Returns:
        处理后的关键词列表
    """
    if isinstance(keywords, str):
        # 处理逗号分隔的字符串
        keyword_list = [k.strip() for k in keywords.split(',')]
    else:
        keyword_list = keywords
    
    # 清理和去重
    return list(set(k for k in keyword_list if k))
