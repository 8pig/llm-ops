import logging
import re
from datetime import datetime
from uuid import UUID

from injector import inject
from dataclasses import dataclass

from internal.core.file_extractor import FileExtractor
from db import SQLAlchemy
from internal.entity.dataset_entity import DocumentStatus
from internal.model import Document
from .base_service  import BaseService
from langchain_core.documents import Document as LCDocument


@inject
@dataclass
class IndexingService(BaseService):
    db: SQLAlchemy
    file_extractor: FileExtractor


    def build_document(self, document_ids: list[UUID]) -> None:
        """根据传递的稳定id列表构建文档索引"""
#         1. 根据传递文档id获取所有文档
        documents = self.db.session.query(Document).filter(
            Document.id.in_(document_ids)
        ).all()

        # 循环遍历文档, 完成每个文档构建

        for document in documents:
            try:
                self.update(
                    document,
                    status=DocumentStatus.PARSING,
                    processing_started_at=datetime.now()
                )
                lc_documents = self._parsing(document)

                lc_document = self._splitting(document, lc_documents)


            except Exception as e:
                logging.exception(f"构建文档错误: {str(e)}")
                self.update(
                    document,
                    status=DocumentStatus.ERROR,
                    error_message=str(e),
                    stop_at=datetime.now(),
                )

    def _parsing(self, document:Document) ->list[LCDocument]:
        """解析文档 为lc"""
        upload_file = document.upload_file
        lc_documents = self.file_extractor.load(upload_file, False, True)
        # 去除空白
        for lc_documents in lc_documents:
            lc_documents.page_content = self._clean_extra_text(lc_documents.page_content)

        self.update(
            document,
            character_count=sum([len(lc_documents.page_content) for lc_documents in lc_documents]),
            status=DocumentStatus.SPLITTING,
            parsing_completed_at=datetime.now()
        )
        return lc_documents



    def _splitting(self, document, lc_documents: list[LCDocument]) -> list[LCDocument]:
        """ 分割文档 拆分块"""
    #     根据process rule 获取文本分割器
        process_rule = document.process_rule


    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r'<\|', '<', text)
        text = re.sub(r'\|>', '>', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]', '', text)
        text = re.sub('\uFFFE', '', text)  # 删除零宽非标记字符
        return text
