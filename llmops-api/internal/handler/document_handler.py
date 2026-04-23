from injector import inject
from dataclasses import dataclass

from uuid import UUID
from flask import request

from pkg.response import validate_error_json, success_json,success_message
from pkg.paginator import PageModel
from internal.schema.document_schema import (
    CreateDocumentsReq, CreateDocumentsResp, GetDocumentResp,
    UpdateDocumentNameReq, GetDocumentsWithPageReq, GetDocumentsWithPageResp,
    UpdateDocumentEnabledReq
)
from internal.service import DocumentService


@inject
@dataclass
class DocumentHandler:
    """文档处理器"""
    document_service: DocumentService


    def create_document(self, dataset_id: UUID):
        """知识库新增/上传文档列表"""
        # 1.提取请求并校验
        print("1111")
        req = CreateDocumentsReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务并创建文档，返回文档列表信息+处理批次
        documents, batch = self.document_service.create_documents(dataset_id, **req.data)

        # 3.生成响应结构并返回
        resp = CreateDocumentsResp()

        return success_json(resp.dump((documents, batch)))


    def get_document(self, dataset_id: UUID, document_id: UUID):
        """知识库id + 文档id 获取知识库详情"""
        document = self.document_service.get_document(dataset_id, document_id)
        resp = GetDocumentResp()
        return success_json(resp.dump(document))

    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        """知识库id + 文档id 修改文档名称"""
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_name(dataset_id, document_id, name=req.name.data)
        return success_message("修改成功")

    def get_documents_with_page(self, dataset_id: UUID):
        """知识库id + 文档id 获取文档列表"""
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        documents, paginator = self.document_service.get_documents_with_page(dataset_id, req)
        resp = GetDocumentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(documents), paginator=paginator))

    def get_document_status(self, dataset_id: UUID, batch: str):
        """根据知识库id + 批 获取文档状态"""
        documents_status = self.document_service.get_document_status(dataset_id, batch)

        return success_json(documents_status)


    def update_document_enabled(self, dataset_id, document_id):
        """更新文档启用状态"""
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_enabled(dataset_id, document_id, req.enabled.data)

        return success_message("更改状态成功")


    def delete_document(self, dataset_id, document_id):
        """删除文档"""
        self.document_service.delete_document(dataset_id, document_id)
        return success_message("删除成功")


