
from uuid import UUID
from flask import request
from flask_login import login_required, current_user
from injector import inject


from internal.schema.app_schema import CreateAppReq, GetAppResp, GetPublishHistoriesWithPageResp, \
    GetPublishHistoriesWithPageReq, FallbackHistoryToDraftReq, UpdateDebugConversationSummaryReq, DebugChatReq
from pkg.paginator import PageModel

from pkg.response import success_json, validate_error_json, success_message, compact_generate_response
from internal.service import AppService, ApiToolService, VectorDatabaseService, ConversationService, RetrievalService

from dataclasses import dataclass
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager




@inject
@dataclass
class AppHandler:
    app_service: AppService
    api_tool_service: ApiToolService
    # provider_factory: ProviderFactory
    # vector_database_service: VectorDatabaseService
    builtin_provider_manager :BuiltinProviderManager
    coversation_service: ConversationService
    retrieval_service: RetrievalService

    """应用控制器"""
    @login_required
    def create_app(self):
        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)
        app = self.app_service.create_app(req, current_user)
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: UUID):
        app = self.app_service.get_app(app_id, current_user)
        resp = GetAppResp()

        return success_json(resp.dump( app))


    @login_required
    def get_draft_app_config(self, app_id: UUID):
        """ 获取appid的最新草稿"""
        draft_config = self.app_service.get_draft_app_config(app_id, current_user)

        return success_json(draft_config)

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """根据传递的应用id+草稿配置更新应用的最新草稿配置"""
        # 1.获取草稿请求json数据
        draft_app_config = request.get_json(force=True, silent=True) or {}

        # 2.调用服务更新应用的草稿配置
        self.app_service.update_draft_app_config(app_id, draft_app_config, current_user)

        return success_message("更新应用草稿配置成功")


    @login_required
    def publish(self, app_id: UUID):
        """ 根据app_id 发布"""
        self.app_service.publish_draft_app_config(app_id, current_user)
        return success_message("发布/更新成功")

    @login_required
    def cancel_publish(self, app_id: UUID):
        """根据传递的应用id，取消发布指定的应用配置信息"""
        self.app_service.cancel_publish_app_config(app_id, current_user)
        return success_message("取消发布应用配置成功")


    @login_required
    def get_publish_histories_with_page(self, app_id: UUID):
        """根据传递的应用id，获取应用发布历史列表"""
        # 1.获取请求数据并校验
        req = GetPublishHistoriesWithPageReq(request.args)

        if not req.validate():
            return validate_error_json(req.errors)

        app_config_versions, paginator = self.app_service.get_publish_histories_with_page(app_id, req, current_user)
        resp = GetPublishHistoriesWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(app_config_versions), paginator=paginator))


    @login_required
    def fallback_history_to_draft(self, app_id: UUID):
        """根据传递的应用id+历史配置版本id，退回指定版本到草稿中"""
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.app_service.fallback_history_to_draft(app_id, req.app_config_version_id.data, current_user)

        return success_message("回退历史配置至草稿成功")

    @login_required
    def get_debug_conversation_summary(self, app_id: UUID):
        summary = self.app_service.get_debug_conversation_summary(app_id, current_user)
        return success_json({"summary":summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: UUID):
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.app_service.update_debug_conversation_summary(app_id, req.summary.data, current_user)
        return success_message("更新应用长期会话成功")

    @login_required
    def delete_debug_conversation(self, app_id: UUID):
        self.app_service.delete_debug_conversation(app_id, current_user)
        return success_message("清空应用调试会话成功")


    @login_required
    def debug_chat(self, app_id: UUID):
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        response = self.app_service.debug_chat(app_id, req.query.data, current_user)

        return compact_generate_response(response)


    @login_required
    def stop_debug_chat(self, app_id: UUID, task_id: UUID):
        self.app_service.stop_debug_chat(app_id, task_id, current_user)
        return success_message("停止应用调试会话成功")


    @login_required
    def get_debug_conversation_messages_with_page(self, app_id: UUID):
        """根据传递的应用id，获取该应用的调试会话分页列表记录"""
        req = GetDebugConversationMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        messages, paginator = self.app_service.get_debug_conversation_messages_with_page(app_id, req, current_user)

        resp = GetDebugConversationMessagesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))



    @login_required
    def ping(self):
        ...
        # from internal.entity.dataset_entity import  RetrievalStrategy, RetrievalSource
        # dataset_retrieval = self.retrieval_service.create_langchain_tool_from_search(
        #     dataset_ids=["e68cc0fd-7c20-4a36-a6c5-fb82f97e6584", "dc824569-ffbf-4079-83b0-9d04d815e24c"],
        #     account=current_user,
        #     retrieval_strategy=RetrievalStrategy.SEMANTIC,
        #     k=10,
        #     score=0.5,
        #     retrival_source=RetrievalSource.DEBUGGER
        # )
        # print(dataset_retrieval.name)
        # print(dataset_retrieval.description)
        # print(dataset_retrieval.args)
        #
        # content = dataset_retrieval.invoke({"query": "什么是ChromeDriver"})
        # return success_json({"content": content})



        # from internal.core.agent.agents import FunctionCallAgent
        # from internal.core.agent.entities.agent_entity import AgentConfig
        # agent = FunctionCallAgent(
        #     AgentConfig(
        #         llm=ChatOpenAI(
        #             model=os.getenv("LLM_MODEL"),
        #             api_key=os.getenv("OPENAI_API_KEY"),
        #             base_url=os.getenv("OPENAI_API_BASE_URL"),
        #         ),
        #         preset_prompt="你是一位年长的诗人 根据用户的主题 作诗"
        #     )
        # )
        # state = agent.run("程序员",[], "")
        # content = state["messages"][-1].content
        # return success_json({"content": content})
        human_message = "你好我叫野猪佩奇, 喜欢唱 跳 rap 篮球~,"
        q = self.coversation_service.generate_suggested_questions(human_message)
        return success_json({"questions": q})
        # cn = self.coversation_service.generate_conversation_name(human_message)
        # return success_message({"conversation_name": cn})
        # return success_json({"message": "pong"})
        # demo_task.delay(uuid.uuid4())
        # return self.api_tool_service.api_tool_invoke()

