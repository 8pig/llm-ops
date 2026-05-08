import { get, post } from '@/utils/request'
import {
  type CreateDatasetRequest,
  type CreateDocumentsRequest,
  type CreateDocumentsResponse,
  type GetDatasetQueriesResponse,
  type GetDatasetResponse,
  type GetDatasetsWithPageResponse,
  type GetDocumentResponse,
  type GetDocumentsStatusResponse,
  type GetDocumentsWithPageRequest,
  type GetDocumentsWithPageResponse,
  type HitRequest,
  type HitResponse,
  type UpdateDatasetRequest,
} from '@/models/dataset'
import { type BaseResponse } from '@/models/base'

// 获取知识库分页列表数据
export const getDatasetsWithPage = (
  current_page: number = 1,
  page_size: number = 20,
  search_word: string = '',
) => {
  return get<GetDatasetsWithPageResponse>(`/datasets`, {
    params: { current_page, page_size, search_word },
  })
}

// 新增知识库
export const createDataset = (req: CreateDatasetRequest) => {
  return post<BaseResponse<any>>(`/datasets`, {
    body: req,
  })
}

// 更新知识库
export const updateDataset = (dataset_id: string, req: UpdateDatasetRequest) => {
  return post<BaseResponse<any>>(`/datasets/${dataset_id}`, {
    body: req,
  })
}

// 删除知识库请求
export const deleteDataset = (dataset_id: string) => {
  return post<BaseResponse<any>>(`/datasets/${dataset_id}/delete`)
}

// 获取知识库详情
export const getDataset = (dataset_id: string) => {
  return get<GetDatasetResponse>(`/datasets/${dataset_id}`)
}

// 获取文档分页列表数据
export const getDocumentsWithPage = (
  dataset_id: string,
  req: GetDocumentsWithPageRequest = {
    current_page: 1,
    page_size: 20,
    search_word: '',
  },
) => {
  return get<GetDocumentsWithPageResponse>(`/datasets/${dataset_id}/documents`, {
    params: req,
  })
}

// 获取指定文档详情
export const getDocument = (dataset_id: string, document_id: string) => {
  return get<GetDocumentResponse>(`/datasets/${dataset_id}/documents/${document_id}`)
}

// 更新指定文档的启用状态
export const updateDocumentEnabled = (
  dataset_id: string,
  document_id: string,
  enabled: boolean,
) => {
  return post<BaseResponse<any>>(`/datasets/${dataset_id}/documents/${document_id}/enabled`, {
    body: { enabled },
  })
}

// 删除指定文档信息
export const deleteDocument = (dataset_id: string, document_id: string) => {
  return post<BaseResponse<any>>(`/datasets/${dataset_id}/documents/${document_id}/delete`)
}

// 更新文档的名字
export const updateDocumentName = (dataset_id: string, document_id: string, name: string) => {
  return post<BaseResponse<any>>(`/datasets/${dataset_id}/documents/${document_id}/name`, {
    body: { name },
  })
}

// 知识库召回测试
export const hit = (dataset_id: string, req: HitRequest) => {
  return post<HitResponse>(`/datasets/${dataset_id}/hit`, {
    body: req,
  })
}

// 最近查询记录
export const getDatasetQueries = (dataset_id: string) => {
  return get<GetDatasetQueriesResponse>(`/datasets/${dataset_id}/queries`)
}

// 上传文档到知识库
export const createDocuments = (dataset_id: string, req: CreateDocumentsRequest) => {
  return post<CreateDocumentsResponse>(`/datasets/${dataset_id}/documents`, {
    body: req,
  })
}

// 根据批处理获取文档的处理状态
export const getDocumentsStatus = (dataset_id: string, batch: string) => {
  return get<GetDocumentsStatusResponse>(`/datasets/${dataset_id}/documents/batch/${batch}`)
}
