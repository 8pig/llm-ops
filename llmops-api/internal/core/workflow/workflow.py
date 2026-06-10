
from typing import Any, Optional, Iterator

from flask import current_app
from pydantic import PrivateAttr, BaseModel, Field, create_model
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.exception import ValidateException as ValidateErrorException
from .entities.node_entity import NodeType
from .entities.variable_entity import VARIABLE_TYPE_MAP
from .entities.workflow_entity import WorkflowConfig, WorkflowState
from .nodes import (
    StartNode,
    LLMNode,
    TemplateTransformNode,
    DatasetRetrievalNode,
    CodeNode,
    ToolNode,
    HttpRequestNode,
    EndNode,
)

# 节点类映射
NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.TEMPLATE_TRANSFORM: TemplateTransformNode,
    NodeType.DATASET_RETRIEVAL: DatasetRetrievalNode,
    NodeType.CODE: CodeNode,
    NodeType.TOOL: ToolNode,
    NodeType.HTTP_REQUEST: HttpRequestNode,
}


class Workflow(BaseTool):
    """工作流LangChain工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        """构造函数，完成工作流函数的初始化"""
        # 1.调用父类构造函数完成基础数据初始化
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            args_schema=self._build_args_schema(workflow_config),
            **kwargs
        )

        # 2.完善工作流配置与工作流图结构程序的初始化
        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    @classmethod
    def _build_args_schema(cls, workflow_config: WorkflowConfig) -> type[BaseModel]:
        """构建输入参数结构体"""
        # 1.提取开始节点的输入参数信息
        fields = {}
        inputs = next(
            (node.inputs for node in workflow_config.nodes if node.node_type == NodeType.START),
            []
        )

        # 2.循环遍历所有输入信息并创建字段映射
        for input in inputs:
            field_name = input.name
            field_type = VARIABLE_TYPE_MAP.get(input.type, str)
            field_required = input.required
            field_description = input.description

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description),
            )

        # 3.调用create_model创建一个BaseModel类，并使用上述分析好的字段
        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        """构建编译后的工作流图程序"""
        # 1.创建graph图程序结构
        graph = StateGraph(WorkflowState)

        # 2.提取nodes和edges信息
        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges

        # 3.如果nodes为空，创建默认的START和END节点
        if len(nodes) == 0:
            from uuid import uuid4
            from .nodes.start.start_entity import StartNodeData
            from .nodes.end.end_entity import EndNodeData
            start_id = uuid4()
            end_id = uuid4()
            start_node_data = StartNodeData(id=start_id, node_type=NodeType.START, title="开始")
            end_node_data = EndNodeData(id=end_id, node_type=NodeType.END, title="结束")
            nodes = [start_node_data, end_node_data]

        # 4.循环遍历nodes节点信息添加节点
        for node in nodes:
            node_flag = f"{node.node_type.value}_{node.id}"
            if node.node_type == NodeType.START:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.START](node_data=node),
                )
            elif node.node_type == NodeType.LLM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.LLM](node_data=node),
                )
            elif node.node_type == NodeType.TEMPLATE_TRANSFORM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TEMPLATE_TRANSFORM](node_data=node),
                )
            elif node.node_type == NodeType.DATASET_RETRIEVAL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.DATASET_RETRIEVAL](
                        flask_app=current_app._get_current_object(),
                        account_id=self._workflow_config.account_id,
                        node_data=node,
                    ),
                )
            elif node.node_type == NodeType.CODE:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.CODE](node_data=node),
                )
            elif node.node_type == NodeType.TOOL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TOOL](node_data=node),
                )
            elif node.node_type == NodeType.HTTP_REQUEST:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.HTTP_REQUEST](node_data=node),
                )
            elif node.node_type == NodeType.END:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.END](node_data=node),
                )
            else:
                raise ValidateErrorException("工作流节点类型错误，请核实后重试")

        # 5.循环遍历edges信息添加边
        parallel_edges = {}  # key:终点，value:起点列表
        start_node = ""
        end_node = ""
        for edge in edges:
            # 6.计算并获取并行边
            source_node = f"{edge.source_type.value}_{edge.source}"
            target_node = f"{edge.target_type.value}_{edge.target}"
            if target_node not in parallel_edges:
                parallel_edges[target_node] = [source_node]
            else:
                parallel_edges[target_node].append(source_node)

            # 7.检测特殊节点（开始节点、结束节点），需要写成两个if的格式，避免只有一条边的情况识别失败
            if edge.source_type == NodeType.START:
                start_node = f"{edge.source_type.value}_{edge.source}"
            if edge.target_type == NodeType.END:
                end_node = f"{edge.target_type.value}_{edge.target}"

        # 8.如果没有边，自动创建从START到END的边
        if len(edges) == 0:
            start_nodes = [f"{node.node_type.value}_{node.id}" for node in nodes if node.node_type == NodeType.START]
            end_nodes = [f"{node.node_type.value}_{node.id}" for node in nodes if node.node_type == NodeType.END]
            if start_nodes and end_nodes:
                graph.set_entry_point(start_nodes[0])
                graph.add_edge(start_nodes[0], end_nodes[0])
                graph.set_finish_point(end_nodes[0])
        else:
            # 9.设置开始和终点
            graph.set_entry_point(start_node)
            graph.set_finish_point(end_node)

            # 10.循环遍历合并边
            for target_node, source_nodes in parallel_edges.items():
                graph.add_edge(source_nodes, target_node)

        # 11.构建图程序并编译
        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """工作流组件基础run方法"""
        result = self._workflow.invoke({"inputs": kwargs})
        # 将NodeResult对象转换为可序列化的字典
        if "node_results" in result:
            result["node_results"] = [
                node_result.model_dump() if hasattr(node_result, "model_dump") else node_result
                for node_result in result["node_results"]
            ]
        return result

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        """工作流流式输出每个节点对应的结果"""
        return self._workflow.stream({"inputs": input})
