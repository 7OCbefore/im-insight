# **IM-Insight: Implementation Guide (Phase 1 & 2\)**

本指南定义了 IM-Insight 系统的代码结构、接口定义和开发步骤。

## **1\. Project Structure (项目结构)**

im-insight/  
├── config/  
│   ├── config.yaml          \# 业务规则配置  
│   └── secrets.yaml.example \# API Key 模板 (gitignored)  
├── src/  
│   ├── \_\_init\_\_.py  
│   ├── core/  
│   │   ├── monitor.py       \# wxauto 封装与监听循环  
│   │   └── watchdog.py      \# 进程守护  
│   ├── engine/  
│   │   ├── parser.py        \# L1 正则匹配逻辑  
│   │   └── llm\_client.py    \# L2 LLM API 客户端  
│   ├── utils/  
│   │   └── logger.py        \# 结构化日志  
│   └── main.py              \# 入口文件  
├── tests/                   \# 单元测试  
├── requirements.txt  
└── README.md

## **2\. Key Interfaces (关键接口定义)**

### **2.1 Engine Interface (src/engine/parser.py)**

from dataclasses import dataclass  
from typing import Optional, Dict

@dataclass  
class MarketSignal:  
    timestamp: float  
    sender: str  
    room\_name: str  
    raw\_content: str  
    intent: str  \# 'buy' | 'sell' | 'unknown'  
    extracted\_data: Dict  \# {"price": 100, "item": "hva\_01"}

class SignalEngine:  
    def process(self, message: str, meta: Dict) \-\> Optional\[MarketSignal\]:  
        """  
        Main entry point for message processing.  
        1\. Runs Regex filter.  
        2\. If match, optionally runs LLM enrichment.  
        """  
        pass

### **2.2 LLM Client (src/engine/llm\_client.py)**

class IntelligenceGateway:  
    def extract\_structured\_data(self, text: str) \-\> Dict:  
        """  
        Calls external LLM API to extract JSON data.  
        Must implement timeout and retry logic.  
        """  
        pass

## **3\. Implementation Steps (开发步骤)**

### **Step 1: Core Skeleton**

* 初始化项目目录。  
* 编写 config/loader.py 用于安全加载 YAML 配置。  
* 编写 src/utils/logger.py 设置控制台与文件日志。

### **Step 2: Ingestion Logic**

* 在 src/core/monitor.py 中集成 wxauto。  
* 实现 get\_latest\_messages() 方法，确保去重逻辑（避免处理同一条消息两次）。

### **Step 3: Rule Engine**

* 实现 src/engine/parser.py。  
* 加载 whitelist 关键词。  
* 编写正则表达式提取基础价格信息。

### **Step 4: Intelligence Layer (Phase 2\)**

* 实现 src/engine/llm\_client.py。  
* 设计 System Prompt，强制输出 JSON 格式。

## **4\. Testing Strategy (测试策略)**

* **Mock Testing:** 在不打开真实 IM 客户端的情况下，使用 Mock 数据流测试解析引擎。  
* **Dry Run:** 开启 dry\_run: true 模式，只打印日志，不发送通知。