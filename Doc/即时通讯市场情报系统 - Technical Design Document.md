# **IM-Insight: Real-Time Market Intelligence System**

# **即时通讯市场情报系统 \- Technical Design Document**

Author: Architecture Team  
Date: 2025-12-17  
Version: 1.0.0 (RFC)  
Status: Approved  
Classification: Confidential

## **1\. Executive Summary (执行摘要)**

**IM-Insight** 是一个针对非结构化即时通讯（IM）数据流的自动化情报采集与分析系统。其核心目标是从高频、高噪声的群组聊天流中，实时识别并提取特定二级流通市场的套利信号（如买入意向 Buy Intent、卖出报价 Sell Offer）。

系统采用 **"规则+AI" 双引擎架构 (Hybrid Dual-Engine Architecture)**：利用正则表达式引擎处理 90% 的低延迟过滤需求，利用大语言模型（LLM）处理复杂的语义理解与非标准化实体提取。系统设计严格遵循“被动遥测 (Passive Telemetry)”原则，以确保宿主账户的安全性和业务连续性。

## **2\. Terminology & Conventions (术语与约定)**

* **HVA (High-Value Asset):** 高价值资产，指代系统中监控的特定流通商品。  
* **Ingestion Node:** 运行在 Windows 环境下的采集节点，负责与 IM 客户端交互。  
* **Signal:** 经过清洗和验证的有效市场情报。  
* **Sanitization:** 数据脱敏与清洗过程，去除无关的 PII (个人身份信息) 和噪声。

## **3\. System Architecture (系统架构)**

系统采用微服务化的 **ETL (Extract-Transform-Load)** 模式，部署于受控的 Windows 宿主机。

### **3.1 High-Level Diagram**

graph TD  
    subgraph "Ingestion Layer (采集层)"  
        Client\[IM Client v3.9.x\]  
        Adapter\[UI Automation Adapter\]  
        Watchdog\[Process Watchdog\]  
    end

    subgraph "Processing Layer (处理层)"  
        Stream\[Message Stream\]  
        Sanitizer\[Data Sanitizer\]  
          
        Router{Router / 分流器}  
          
        RegexEngine\[L1: Regex Engine\]  
        LLMGateway\[L2: LLM Gateway\]  
    end

    subgraph "Action Layer (执行层)"  
        Notifier\[Push Notification Service\]  
        Logger\[Structured Logger\]  
    end

    Client \--\> Adapter  
    Adapter \--\> Stream  
    Watchdog \-.-\> Client  
      
    Stream \--\> Sanitizer  
    Sanitizer \--\> Router  
      
    Router \-- "High Confidence Keywords" \--\> RegexEngine  
    Router \-- "Complex/Ambiguous" \--\> LLMGateway  
      
    RegexEngine \-- "Matched Signal" \--\> Notifier  
    LLMGateway \-- "Extracted Intent" \--\> Notifier  
      
    Notifier \--\> Logger

### **3.2 Component Specifications (组件规范)**

#### **3.2.1 Ingestion Service (采集服务)**

* **Technology:** Python 3.10+, wxauto (Wrapper for MS UI Automation).  
* **Responsibility:**  
  * 维护与 IM 客户端窗口的句柄连接。  
  * 实现 Polling Loop (轮询循环)，周期 $T=1.0s$。  
  * **Jitter Mechanism (抖动机制):** 在操作间引入 $\\Delta t \\sim U(0.5, 1.5)$ 的随机延迟，模拟人类行为特征 (HCI Simulation)。

#### **3.2.2 Processing Engine (处理引擎)**

* **L1 Filter (Regex):** \* 基于 Aho-Corasick 算法或预编译正则进行关键词快速匹配。  
  * **Latency Target:** \< 10ms.  
* **L2 Inference (LLM):** \* **Interface:** OpenAI-Compatible REST API.  
  * **Fallback Strategy:** 若 API 响应时间 \> 5000ms 或返回 5xx 错误，自动降级回 L1 引擎，并记录遥测日志。

#### **3.2.3 Notification Service (通知服务)**

* **Protocol:** HTTPS Webhook.  
* **Payload Schema:** Standardized JSON.

## **4\. Data Pipeline & Logic (数据流与逻辑)**

### **4.1 Message Processing Flow**

1. **Ingest:** 捕获原始文本 $M\_{raw}$。  
2. **Pre-process:** \* 去除空白符、特殊表情符号。  
   * 过滤系统消息（如“XXX撤回了一条消息”）。  
3. **L1 Evaluate:**  
   * $Score \= \\sum (Keyword\_i \\in M\_{sanitized})$  
   * If $Score \> Threshold$, 标记为 Suspected Signal。  
4. **L2 Evaluate (Optional):**  
   * 若配置开启且 L1 命中，构建 Prompt 调用 LLM。  
   * 提取 Intent (Buy/Sell), Price, Item, Quantity。  
5. **Dispatch:** 发送至下游 Webhook。

## **5\. Non-Functional Requirements (非功能性需求)**

### **5.1 Security & Compliance (安全与合规)**

* **Read-Only Policy:** 系统必须配置为**只读模式**。严禁向任何群组自动发送消息。  
* **Local Processing:** 所有 L1 处理在本地完成；L2 处理需确保仅发送必要文本片段，不包含用户 ID 等元数据。

### **5.2 Reliability (可靠性)**

* **Crash Recovery:** Watchdog 进程需每 60 秒检测一次主进程心跳。若心跳丢失，自动重启 Ingestion Service。

## **6\. Configuration Schema (配置范式)**

所有业务规则必须从代码中剥离，使用 YAML 管理。

\# config.yaml (Schema Definition)  
app:  
  version: "1.0.0"  
  environment: "production"

ingestion:  
  target\_window\_title: "WeChat"  
  scan\_interval\_ms: 1000  
  human\_simulation:  
    jitter\_enabled: true  
    jitter\_range: \[0.5, 1.5\]

intelligence:  
  provider: "deepseek" \# or "openai"  
  api\_key\_env\_var: "LLM\_API\_KEY" \# Load from environment variable  
  base\_url: "\[https://api.deepseek.com/v1\](https://api.deepseek.com/v1)"  
  model: "deepseek-chat"  
  temperature: 0.1

rules:  
  whitelist:   
    \- "求购"  
    \- "收"  
    \- "出"  
  blacklist:  
    \- "代开"  
    \- "拼单"  
