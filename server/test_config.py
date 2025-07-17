#!/usr/bin/env python3
"""
测试更新后的配置类
演示使用 Field 定义的配置类功能
"""

from config.agent_config import AgentConfig, ModelConfig, KnowledgeConfig, McpConfig, RetrievalConfig

def test_basic_config():
    """测试基础配置创建"""
    print("=== 测试基础配置 ===")
    
    # 创建基础配置
    config = AgentConfig(
        name="测试智能体",
        description="这是一个测试智能体",
        system_prompt="你是一个有用的助手"
    )
    
    print(f"智能体名称: {config.name}")
    print(f"智能体描述: {config.description}")
    print(f"系统提示词: {config.system_prompt}")
    print(f"LLM提供商: {config.llm_config.provider}")
    print(f"LLM模型: {config.llm_config.model}")
    print(f"知识库启用: {config.knowledge_config.enabled}")
    print(f"MCP启用: {config.mcp_config.enabled}")
    print()

def test_complete_config():
    """测试完整配置创建"""
    print("=== 测试完整配置 ===")
    
    # 创建完整的配置
    agent = AgentConfig(
        name="完整测试智能体",
        description="这是一个完整的测试智能体配置",
        system_prompt="你是一个专业的AI助手，可以帮助用户解决各种问题。",
        llm_config=ModelConfig(
            provider="openai",
            model="gpt-4",
            config={"temperature": 0.7, "max_tokens": 4096}
        ),
        knowledge_config=KnowledgeConfig(
            enabled=True,
            databases=["知识库1", "知识库2"],
            retrieval_config=RetrievalConfig(
                top_k=5,
                similarity_threshold=0.8
            )
        ),
        mcp_config=McpConfig(
            enabled=True,
            servers=["文件管理器", "计算器", "网络工具"]
        ),
        tools=["web_search", "calculator", "file_reader"]
    )
    
    print(f"智能体名称: {agent.name}")
    print(f"智能体描述: {agent.description}")
    print(f"系统提示词: {agent.system_prompt}")
    print(f"LLM提供商: {agent.llm_config.provider}")
    print(f"LLM模型: {agent.llm_config.model}")
    print(f"LLM温度: {agent.llm_config.config.get('temperature')}")
    print(f"知识库启用: {agent.knowledge_config.enabled}")
    print(f"知识库数量: {len(agent.knowledge_config.databases)}")
    print(f"检索文档数: {agent.knowledge_config.retrieval_config.top_k}")
    print(f"相似度阈值: {agent.knowledge_config.retrieval_config.similarity_threshold}")
    print(f"MCP启用: {agent.mcp_config.enabled}")
    print(f"MCP服务器数量: {len(agent.mcp_config.servers)}")
    print(f"工具数量: {len(agent.tools)}")
    print()

def test_default_values():
    """测试默认值"""
    print("=== 测试默认值 ===")
    
    # 创建使用默认值的配置
    default_config = AgentConfig()
    
    print(f"默认智能体名称: '{default_config.name}'")
    print(f"默认智能体描述: '{default_config.description}'")
    print(f"默认系统提示词: '{default_config.system_prompt}'")
    print(f"默认LLM提供商: '{default_config.llm_config.provider}'")
    print(f"默认LLM模型: '{default_config.llm_config.model}'")
    print(f"默认LLM温度: {default_config.llm_config.config.get('temperature')}")
    print(f"默认知识库启用: {default_config.knowledge_config.enabled}")
    print(f"默认检索文档数: {default_config.knowledge_config.retrieval_config.top_k}")
    print(f"默认相似度阈值: {default_config.knowledge_config.retrieval_config.similarity_threshold}")
    print(f"默认MCP启用: {default_config.mcp_config.enabled}")
    print(f"默认工具列表: {default_config.tools}")
    print()

if __name__ == "__main__":
    print("开始测试更新后的配置类...\n")
    
    test_basic_config()
    test_complete_config()
    test_default_values()
    
    print("所有测试完成！") 