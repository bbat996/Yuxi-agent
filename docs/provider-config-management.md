# 供应商配置管理功能

## 概述

本功能允许管理员在Web界面上直接管理模型提供商的配置，包括：

1. **连接配置管理** - 配置API Base URL和API Key
2. **模型管理** - 添加/删除供应商的模型
3. **连接测试** - 测试API连接是否正常
4. **配置保存** - 自动保存到`models.private.yml`配置文件

## 功能特性

### 1. 连接配置管理

- **API Base URL配置**: 支持自定义API端点
- **API Key管理**: 安全存储API密钥
- **配置验证**: 确保配置参数的有效性
- **自动保存**: 配置更改后自动保存到配置文件

### 2. 模型管理

- **添加模型**: 为供应商添加新的模型
- **删除模型**: 从供应商中删除不需要的模型
- **批量操作**: 支持批量选择和管理模型
- **实时更新**: 模型列表实时同步

### 3. 连接测试

- **连接验证**: 测试API连接是否正常
- **模型列表获取**: 验证API Key权限
- **错误提示**: 详细的错误信息反馈

## 使用方法

### 访问配置管理

1. 登录系统（需要管理员权限）
2. 进入设置页面
3. 选择"模型管理"标签
4. 在左侧选择要配置的供应商

### 配置连接参数

1. 点击"连接配置"按钮
2. 填写API Base URL（例如：`https://api.openai.com/v1`）
3. 填写API Key
4. 点击"测试连接"验证配置
5. 点击"保存配置"保存更改

### 管理模型

#### 添加模型
1. 点击"添加模型"按钮
2. 输入模型名称（例如：`gpt-4-turbo`）
3. 点击"添加模型"确认

#### 删除模型
1. 在模型列表中，点击模型卡片右侧的删除按钮
2. 确认删除操作

#### 批量配置模型
1. 点击"配置模型"按钮
2. 在弹窗中搜索和选择需要的模型
3. 点击"保存配置"确认选择

## API接口

### 获取供应商配置
```
GET /api/chat/provider/{provider}/config
```

### 更新供应商配置
```
POST /api/chat/provider/{provider}/config
Content-Type: application/json

{
  "base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here"
}
```

### 添加模型
```
POST /api/chat/provider/{provider}/models/add
Content-Type: application/json

"model_name_here"
```

### 删除模型
```
DELETE /api/chat/provider/{provider}/models/{model_name}
```

### 测试连接
```
POST /api/chat/provider/{provider}/test
Content-Type: application/json

{
  "base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here"
}
```

## 配置文件

所有配置都会自动保存到 `server/config/models.private.yml` 文件中：

```yaml
MODEL_NAMES:
  openai:
    name: OpenAI
    url: https://platform.openai.com/docs/models
    base_url: https://api.openai.com/v1  # 可自定义
    default: gpt-3.5-turbo
    env:
      - OPENAI_API_KEY
    models:
      - gpt-4
      - gpt-4o
      - gpt-4o-mini
      - gpt-3.5-turbo
      - gpt-4-turbo  # 新添加的模型
```

## 权限要求

- **管理员权限**: 所有配置管理功能都需要管理员权限
- **API访问权限**: 需要有效的API Key才能进行连接测试

## 注意事项

1. **API Key安全**: API Key会保存到环境变量中，请确保系统安全
2. **配置备份**: 建议定期备份 `models.private.yml` 文件
3. **服务重启**: 某些配置更改可能需要重启服务才能生效
4. **网络连接**: 连接测试需要网络访问权限

## 故障排除

### 连接测试失败
- 检查API Base URL是否正确
- 验证API Key是否有效
- 确认网络连接正常
- 检查防火墙设置

### 配置保存失败
- 确认有写入配置文件的权限
- 检查磁盘空间是否充足
- 验证配置文件格式是否正确

### 模型添加失败
- 确认模型名称格式正确
- 检查模型是否已存在
- 验证供应商配置是否正确

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的连接配置管理
- 支持模型的添加和删除
- 支持连接测试功能 