import { message } from 'ant-design-vue';

/**
 * 统一错误处理工具
 */
export class ErrorHandler {
  /**
   * 处理API key配置错误
   * @param {Error} error - 错误对象
   * @param {string} provider - 模型提供商名称
   * @returns {boolean} 是否已处理该错误
   */
  static handleApiKeyError(error, provider = '') {
    if (error.message && (
      error.message.includes('API密钥未配置') || 
      error.message.includes('API key not found') ||
      error.message.includes('API key is required')
    )) {
      const providerText = provider ? `(${provider})` : '';
      message.error(`模型提供商${providerText}的API密钥未配置，请前往设置页面进行配置`);
      return true;
    }
    return false;
  }

  /**
   * 处理认证错误
   * @param {Error} error - 错误对象
   * @returns {boolean} 是否已处理该错误
   */
  static handleAuthError(error) {
    if (error.message && (
      error.message.includes('未授权') || 
      error.message.includes('令牌已过期') ||
      error.message.includes('token expired')
    )) {
      message.error('登录已过期，请重新登录');
      return true;
    }
    return false;
  }

  /**
   * 处理网络错误
   * @param {Error} error - 错误对象
   * @returns {boolean} 是否已处理该错误
   */
  static handleNetworkError(error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      message.error('网络连接失败，请检查网络连接');
      return true;
    }
    return false;
  }

  /**
   * 通用错误处理
   * @param {Error} error - 错误对象
   * @param {string} defaultMessage - 默认错误消息
   * @param {string} provider - 模型提供商名称
   */
  static handleError(error, defaultMessage = '操作失败', provider = '') {
    console.error('错误详情:', error);

    // 按优先级处理不同类型的错误
    if (this.handleAuthError(error)) {
      return;
    }
    
    if (this.handleApiKeyError(error, provider)) {
      return;
    }
    
    if (this.handleNetworkError(error)) {
      return;
    }

    // 默认错误处理
    const errorMessage = error.message || defaultMessage;
    message.error(errorMessage);
  }

  /**
   * 格式化API key配置错误消息
   * @param {string} provider - 模型提供商名称
   * @param {string} envVar - 环境变量名
   * @param {string} url - 获取API key的网址
   * @returns {string} 格式化的错误消息
   */
  static formatApiKeyErrorMessage(provider, envVar, url) {
    return `
模型提供商 ${provider} 的API密钥未配置。

请按以下方式之一进行配置：

1. 设置环境变量：
   export ${envVar}=your_api_key_here

2. 在配置文件中添加API密钥：
   编辑文件：config/model_provider.private.yml
   添加以下内容：
   MODEL_NAMES:
     ${provider}:
       api_key: your_api_key_here

3. 通过Web界面配置：
   访问设置页面 -> 模型提供商 -> 配置 ${provider}

获取API密钥：
- 访问：${url}
- 注册账号并获取API密钥
    `.trim();
  }
}

export default ErrorHandler; 