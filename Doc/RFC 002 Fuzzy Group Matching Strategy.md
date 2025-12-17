# **RFC 002: Fuzzy Group Matching Strategy**

# **模糊群名匹配策略变更说明**

Status: Approved  
Date: 2025-12-17  
Context: Users report failure in targeting specific groups despite visual exact matches.

## **1\. Problem Statement**

Current implementation uses strict string equality (if configured\_name \== actual\_window\_name).  
This is brittle due to:

1. **Dynamic Suffixes:** WeChat often appends user counts (e.g., "Group Name (499)").  
2. **Invisible Characters:** Zero-width spaces or trailing whitespaces in window titles.  
3. **Case Sensitivity:** "vip group" fails to match "VIP Group".

## **2\. Proposed Solution**

Migrate to a **Case-Insensitive Substring Matching** strategy.

### **2.1 Logic Definition**

Let $N\_{config}$ be the list of configured target keywords.  
Let $S\_{room}$ be the actual detected room name from wxauto.  
The system shall process the message if:

$$\\exists n \\in N\_{config} : \\text{lowercase}(n) \\in \\text{lowercase}(S\_{room})$$

### **2.2 Examples**

| Configured Target (monitor\_groups) | Incoming Room Name (msg.room) | Result | Reason |
| :---- | :---- | :---- | :---- |
| \["酒商"\] | "华东酒商交流群" | **Match** | Substring found |
| \["vip"\] | "核心VIP资源群(500)" | **Match** | Case-insensitive substring |
| \["A群"\] | "A群 " (trailing space) | **Match** | Substring handles space |

## **3\. Debugging Enhancement**

To assist troubleshooting, the monitor module must log the **exact raw repr** of the detected room name when in debug mode, allowing users to identify encoding anomalies.