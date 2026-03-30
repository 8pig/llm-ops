/* 基础*/
export type BaseResponse<T> = {
  code: String;
  data: T;
  message: string;
};

export type BasePaginatorResponse<T> = BaseResponse<{
  list: Array<T>;
  paginator: {
    total_page: number;
    current_page: number;
    page_size: number;
    total_record: number;
  };
}>;
