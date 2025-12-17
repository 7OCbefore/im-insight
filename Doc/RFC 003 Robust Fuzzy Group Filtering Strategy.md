# **RFC 003: Robust Fuzzy Group Filtering Strategy**

# **鲁棒的模糊群名匹配策略**

Status: Proposed  
Date: 2025-12-17  
Priority: Critical

## **1\. Problem Diagnosis**

User reports failure to capture messages from specific groups even when names appear identical.  
Root causes identified:

1. **Exact Match Failure:** settings.monitor\_groups currently requires an exact string match.  
2. **Invisible Characters:** WeChat room names often contain trailing spaces (\\x20) or zero-width spaces (\\u200b).  
3. **Case Sensitivity:** "Msg" does not match "msg".

## **2\. Technical Specification**

### **2.1 Logic Overhaul**

The filtering method \_is\_target\_group(room\_name) must implement **Case-Insensitive Substring Matching**.

**Algorithm:**

1. Let $T$ be the list of configured targets (e.g., \["msg", "酒商"\]).  
2. Let $R$ be the incoming room name (e.g., "Msg ").  
3. Normalize $T$ and $R$ to lowercase.  
4. Match if $\\exists t \\in T$ such that $t\_{lower} \\subseteq R\_{lower}$.

### **2.2 Debugging Requirements**

To allow users to "see" invisible characters, the system must log the repr() of the room name when a match fails in Debug mode.

* *Standard Log:* Ignored message from room: msg  
* *Debug Log:* \[FILTER\_FAIL\] Target='msg' NOT FOUND in Room='msg ' (Hex: 'msg\\x20')

## **3\. Configuration Impact**

No changes to settings.yaml structure, but users can now use partial names (e.g., "酒商" instead of full name).

\---

\#\#\# 3\. 给 AI 的 Master Prompt (修复版)

请复制以下 Prompt 发送给你的 AI。我专门加入了一段\*\*“调试探针”\*\*代码，如果还不行，控制台会把隐藏字符“扒光”给你看。

\> \*\*Copy & Paste below:\*\*

\`\`\`text  
Role: Python Backend Engineer.  
Project: "IM-Insight" (Core Logic Repair).

Context:  
The user is unable to filter messages by specific group names. "all" works, but specific names fail.  
This is likely due to invisible characters (spaces, zero-width) or case mismatch.  
We need to switch to \*\*Case-Insensitive Substring Matching\*\* and add \*\*Deep Debugging Logs\*\*.

Task:  
Refactor \`src/core/monitor.py\` completely to fix the filtering logic.

Requirements:

1\. Method \`\_is\_target\_group(self, room\_name: str) \-\> bool\`:  
   \- \*\*Step 1:\*\* Check if \`self.settings.ingestion.monitor\_groups\` contains "all" (case-insensitive). If yes, return \`True\`.  
   \- \*\*Step 2:\*\* Normalize \`room\_name\` to lowercase.  
   \- \*\*Step 3:\*\* Iterate through \`monitor\_groups\`. For each \`target\`:  
     \- Normalize \`target\` to lowercase.  
     \- Check if \`target\` is a \*\*substring\*\* of \`room\_name\` (e.g., \`if target in room\_name:\`).  
     \- If match, return \`True\`.  
   \- \*\*Step 4:\*\* If loop finishes without match, return \`False\`.

2\. Deep Debug Logging (Critical):  
   \- In \`get\_recent\_messages\`, BEFORE yielding:  
     \- Call \`self.\_is\_target\_group(msg.room)\`.  
     \- \*\*If it returns False (Filtered out):\*\*  
       \- Log a WARNING (temporarily, so user can see it):  
         \`f"⛔ IGNORED: Room='{msg.room}' | Repr={repr(msg.room)} | Targets={self.settings.ingestion.monitor\_groups}"\`  
     \- \*\*If it returns True (Accepted):\*\*  
       \- Log a INFO:  
         \`f"✅ ACCEPTED: Room='{msg.room}' matched target."\`

3\. Implementation Details:  
   \- Ensure you handle \`None\` or empty strings safely.  
   \- Keep the existing \`wxauto\` polling logic, just replace the filtering conditional inside the loop.

Constraints:  
\- Use \`repr()\` in the log to reveal hidden characters like \`\\u200b\` or trailing spaces.  
\- Do not change the \`main.py\` interface.

### **修复后的预期操作**

1. **运行代码：** AI 修改完后，运行 main.py。  
2. **观察控制台：**  
   * 如果匹配成功，你会看到 ✅ ACCEPTED: ...。  
   * 如果还是匹配失败，你会看到类似这样的红字警告：  
     ⛔ IGNORED: Room='msg' | Repr='msg ' | Targets=\['msg'\]  
