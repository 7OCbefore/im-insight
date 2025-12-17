# **Technical Advisory 001: Incorrect Room Name Parsing**

# **技术顾问报告：群名解析错误修正方案**

Status: Critical Fix  
Date: 2025-12-17  
Component: src/core/monitor.py  
Affected Version: Phase 3.0

## **1\. 故障现象 (Symptom)**

在执行 monitor\_groups 过滤时，所有群聊的名称（Room）均被识别为字符串 "msg"，导致白名单过滤逻辑（if target in room\_name）失效，所有消息被错误拦截。

* **Log Evidence:** ⛔ IGNORED: Room='msg' | Repr='msg'  
* **Expected:** Room='apex白给小分队'

## **2\. 根因分析 (Root Cause Analysis)**

该问题源于 wxauto 库的数据返回结构与 monitor.py 的解析逻辑不匹配。

### **2.1 数据结构对比**

* wxauto (Current) 返回结构：  
  GetNextNewMessage() 返回的是一个包含元数据的字典 (Dictionary)，而非简单的键值对映射。  
  {  
      'chat\_name': 'apex白给小分队',  \# \<--- 真实的群名在这里  
      'chat\_type': 'group',  
      'msg': \[MessageObject1, ...\]   \# \<--- 这里的 key 是 'msg'  
  }

* monitor.py (Current) 错误逻辑：  
  当前代码采用了遍历字典 (Iterate Items) 的方式：  
  \# 错误代码逻辑推演  
  msgs\_dict \= self.client.GetNextNewMessage()  
  for room\_name, msg\_list in msgs\_dict.items():  
      \# ... 处理逻辑

### **2.2 故障复现流程**

1. 代码开始遍历字典。  
2. 遇到 Key 为 'chat\_name'，Value 为 'apex...' \-\> 代码可能因类型不匹配（期望 List 却得到 String）而跳过或报错。  
3. 遇到 Key 为 'msg'，Value 为 \[MessageList\] \-\> 代码认为 **Room Name 是 'msg'**，且 Value 是合法的消息列表。  
4. **结果：** 代码提取到了消息，但把群名错误地标记为了 "msg"。

## **3\. 修复方案 (Resolution)**

必须弃用遍历逻辑，改为**显式字段提取 (Explicit Key Access)**。

### **3.1 逻辑伪代码 (Pseudo-code)**

**修正前 (Before):**

data \= wx.GetNextNewMessage()  
for room, msgs in data.items():  \# \<--- 错误源头  
    validate(room)

**修正后 (After):**

data \= wx.GetNextNewMessage()  
if data:  
    \# 1\. 显式提取群名  
    actual\_room\_name \= data.get('chat\_name', 'Unknown')  
      
    \# 2\. 显式提取消息列表  
    msg\_list \= data.get('msg', \[\])  
      
    \# 3\. 统一处理  
    if self.\_is\_target\_group(actual\_room\_name):  
        for msg in msg\_list:  
            msg.room \= actual\_room\_name  \# 修正消息对象的 source 属性  
            process(msg)

## **4\. 验证标准 (Verification)**

修复后，Debug 日志应显示：  
✅ ACCEPTED: Room='apex白给小分队' matched target.