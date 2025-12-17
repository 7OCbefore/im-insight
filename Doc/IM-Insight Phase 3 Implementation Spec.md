# **IM-Insight: Phase 3 Implementation Spec**

# **Feature: Targeted Monitoring & Structured Persistence**

## **1\. Targeted Monitoring (精准监控)**

### **1.1 Configuration Update**

Modify settings.yaml under ingestion or rules section to include a target list.

ingestion:  
  \# 监控模式：  
  \# \- \["all"\]: 监控所有群消息 (默认)  
  \# \- \["A群", "B群"\]: 仅监控指定群名  
  monitor\_groups:   
    \- "全国酒商交流群"  
    \- "华东资源对接群"

### **1.2 Filtering Logic (In src/core/monitor.py)**

Before processing any message, the system must validate the room\_name (Chat Room Name).

* **Logic:**  
  if "all" in settings.monitor\_groups:  
      process(message)  
  elif message.room in settings.monitor\_groups:  
      process(message)  
  else:  
      drop(message) \# Ignore

## **2\. Structured Persistence (Excel/CSV 落地)**

### **2.1 Schema Definition**

The output CSV must contain the following columns to support business operations:

| Column Header | Data Source | Description |
| :---- | :---- | :---- |
| **Time** | signal.timestamp | 消息捕获时间 (YYYY-MM-DD HH:MM:SS) |
| **Source Group** | signal.room | **(Critical)** 来源群聊名称 |
| **Sender** | signal.sender | 发送者昵称 |
| **Intent** | signal.intent | 买(Buy) / 卖(Sell) |
| **Item** | signal.item | 商品名 (如: 飞天茅台) |
| **Price** | signal.price | 提取的价格 (如: 2800\) |
| **Specs** | signal.specs | 规格/备注 (如: 24年/散瓶) |
| **Raw Content** | signal.raw\_content | 原始消息内容 (用于人工核对) |

### **2.2 File Strategy**

* **Format:** CSV with utf-8-sig encoding (compatible with Excel).  
* **Rotation:** Daily rotation (e.g., data/market\_log\_2025-12-17.csv).  
* **Write Mode:** Append-only (a+).