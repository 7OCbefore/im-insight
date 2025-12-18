# **Issue Ticket: Ingestion Leakage & Filter Bypass**

# **故障单：采集源泄露与白名单失效**

Priority: P0 (Critical)  
Component: src/core/monitor.py, src/engine/processor.py  
Status: Open

## **1\. Executive Summary**

The system is currently failing to enforce two critical guardrails:

1. **Source-Level Leakage:** The bot interacts with (clicks and reads) chat sessions that are NOT listed in the monitor\_groups configuration.  
2. **Content Filter Bypass:** Messages that do NOT contain any whitelist keywords are being processed, sent to the LLM, and persisted to the CSV logs.

## **2\. Detailed Issue Description**

### **Issue A: Source-Level Ingestion Leak (src/core/monitor.py)**

Context:  
The system is designed to use a "Look-Before-Leap" strategy (\_scan\_target\_sessions) to only interact with specific UI elements (groups) defined in settings.yaml.  
**Observed Behavior:**

* The system continues to read messages from non-target groups.  
* This suggests that either:  
  1. The \_scan\_target\_sessions logic is incorrectly identifying non-target groups as targets.  
  2. The code is falling back to the legacy GetNextNewMessage method (which auto-clicks any red dot).  
  3. The iteration loop over SessionBox children is not correctly checking \_is\_target\_group(name) before triggering the Click event.

**Expected Behavior:**

* The bot must iterate through the session list.  
* For each session S:  
  * If S.Name is NOT in monitor\_groups \-\> **SKIP** (No Click, No Read).  
  * If S.Name IS in monitor\_groups \-\> **CLICK & READ**.

### **Issue B: Processor Filter Bypass (src/engine/processor.py)**

Context:  
The system enforces a strict funnel: Blacklist \-\> Whitelist \-\> LLM. Messages must contain at least one Whitelist keyword to proceed.  
**Observed Behavior:**

* Irrelevant messages (e.g., chitchat, non-trading text) are appearing in session\_latest.csv.  
* This indicates that the SignalProcessor.process method is returning valid MarketSignal objects even when the whitelist check fails.

**Expected Behavior:**

* Input: "今天天气不错" (No whitelist keywords).  
* Logic: \_contains\_any(text, whitelist) returns False.  
* Action: process() returns \[\] (Empty List).  
* Result: main.py loop receives empty list \-\> Nothing recorded to CSV.

## **3\. Action Plan for AI Developer**

### **Task 1: Fix src/core/monitor.py**

1. **Audit get\_recent\_messages:** Ensure it **exclusively** calls \_scan\_target\_sessions and **NEVER** calls GetNextNewMessage.  
2. **Debug \_scan\_target\_sessions:**  
   * Verify the loop: for item in session\_box.GetChildren()  
   * Verify the check: if not self.\_is\_target\_group(name): continue must happen **BEFORE** item.Click().  
   * Add DEBUG log: logger.debug(f"Skipping non-target session: {name}").

### **Task 2: Fix src/engine/processor.py**

1. **Enforce Guardrails:** Refactor process method to ensure the **Whitelist Check** is the absolute gatekeeper.  
2. **Logic Flow:**  
   \# Pseudo-code Requirement  
   if not self.\_contains\_any(content, self.whitelist):  
       logger.debug(f"Dropped (No Whitelist): {content}")  
       return \[\] \# MUST return empty list

3. **Verify Return Type:** Ensure that when a message is dropped, it returns an empty list, NOT a MarketSignal with "Unknown" values.

## **4\. Verification Criteria**

* **Test 1:** Send a message to a non-monitored group \-\> Bot does NOT click the chat; Log shows nothing or "Skipping".  
* **Test 2:** Send "Hello" to a monitored group \-\> Bot clicks, reads, but Log shows "Dropped (No Whitelist)"; CSV remains unchanged.  
* **Test 3:** Send "求购 飞天" to a monitored group \-\> Bot clicks, reads, LLM analyzes, CSV updates.