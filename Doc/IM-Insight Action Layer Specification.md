# **IM-Insight: Action Layer Specification**

# **Phase 4: Silent Recorder & Dual-Table Persistence**

**Objective:** Implement a silent, robust data persistence layer with dual-table strategy (Session vs. History) for post-market analysis.

## **1\. Architecture: The Silent Recorder**

The ActionDispatcher will now focus exclusively on data serialization. The DesktopStrategy and SoundStrategy are deprecated/disabled by default.

graph LR  
    Signal\[Market Signal\] \--\> Dispatcher{Action Dispatcher}  
      
    Dispatcher \--\>|Stream A: Session Data| TmpFile\[data/session\_latest.csv\]  
    Dispatcher \--\>|Stream B: Historical Data| HistFile\[data/history\_2025-12.csv\]

## **2\. Persistence Strategy (Dual-Table)**

### **2.1 Table A: The Session Log (临时表)**

* **Filename:** data/session\_latest.csv  
* **Behavior:** **Truncate on Start.** Every time main.py starts, this file is cleared (or overwritten).  
* **Use Case:** "What happened *just now* since I started the bot?" \- Useful for quick checks during a trading session.

### **2.2 Table B: The Historical Log (总表)**

* **Filename:** data/history\_{YYYY-MM}.csv (Monthly Rotation) or data/master\_history.csv.  
* **Behavior:** **Append Only.** Never deletes data.  
* **Use Case:** "What was the price trend of 'Feitian' over the last 30 days?" \- Useful for evening analysis.

### **2.3 Schema Specification (Standardized)**

Both tables share the exact same column structure for easy merging.

| Column | Example | Description |
| :---- | :---- | :---- |
| **Time** | 2025-12-17 16:34:05 | ISO 8601 Format |
| **Group** | Apex资源群 | Source Room Name |
| **Sender** | 张三 | Username |
| **Intent** | Sell | Buy / Sell / Unknown |
| **Item** | 飞天茅台 | Extracted Product Name |
| **Price** | 2800 | Numeric Price |
| **Specs** | 24年/散瓶 | Attributes |
| **Raw** | ... | Original Message Content |

## **3\. Implementation Details (src/action/recorder.py)**

### **3.1 Class DualTableRecorder**

* **Init:**  
  * Ensure data/ directory exists.  
  * Open session\_latest.csv in write mode (w, clears content) to write headers.  
  * Check history\_{month}.csv. If not exists, create and write headers.  
* **Method record(signal):**  
  * Append row to session\_latest.csv.  
  * Append row to history\_{month}.csv.  
  * Flush buffers immediately to prevent data loss on crash.

### **3.2 Configuration Updates (settings.yaml)**

Remove desktop\_popup and sound. Focus on storage.

notifications:  
  enabled: true  
  mode: "silent"        \# silent \= no popups  
  storage:  
    session\_file: "data/session\_latest.csv"  
    history\_mode: "monthly" \# monthly / single  
