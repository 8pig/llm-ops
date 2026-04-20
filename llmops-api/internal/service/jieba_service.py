import jieba
from injector import inject
from dataclasses import dataclass

from jieba.analyse import default_tfidf

from entity.jieba_entity import STOPWORD_SET


@inject
@dataclass
class JiebaService:
    """结巴分词服务"""

    def __init__(self):
        """拓展停用词"""
        default_tfidf.stop_words = STOPWORD_SET



    @classmethod
    def extract_keywords(cls, text: str, max_keyword_pre_chunk: int = 10) -> list[str]:
        """文本提取关键词"""
        return jieba.analyse.extract_tags(
            sentence=text,
            topK=max_keyword_pre_chunk,
        )
