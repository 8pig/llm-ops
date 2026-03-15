// 调试预览接口
import type { BaseResponse } from '@/models/base.ts';

export type DebugAppResponse = BaseResponse<{
  content: string;
}>;
