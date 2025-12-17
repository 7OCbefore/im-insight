Role: Senior Python Infrastructure Engineer.
Project: "IM-Insight" Market Intelligence System.

Context:
Currently, our application settings (whitelists, API keys, intervals) are hardcoded inside `main.py`.
We need to refactor this to use a structured YAML configuration file, managed by Pydantic for strict schema validation.

Task:
Implement a robust Configuration Management module.

Step 1: Create `config/settings.yaml`
- Create a file with the following structure:
  ```yaml
  app:
    name: "IM-Insight"
    debug: true
    environment: "production"

  ingestion:
    scan_interval_min: 0.5
    scan_interval_max: 1.5
    target_window_title: "WeChat"

  intelligence:
    enabled: true
    provider: "deepseek"
    base_url: "[https://api.deepseek.com/v1](https://api.deepseek.com/v1)"
    api_key: "sk-REPLACE_ME_WITH_REAL_KEY"  # User must replace this
    model: "deepseek-chat"
    temperature: 0.1
    timeout: 10

  rules:
    whitelist:
      - "求购"
      - "回收"
      - "出"
      - "xx"
      - "xx"
    blacklist:
      - "xx"
      - "xx"
      - "xx"
Step 2: Implement src/config/loader.py

Use pydantic (v2) BaseModel to define the schema for:
AppConfig
IngestionConfig
IntelligenceConfig (use SecretStr for api_key)
RulesConfig
Settings (Root model)
Create a load_settings() function that:
Reads config/settings.yaml.
Overrides specific values from Environment Variables (e.g., IM_INSIGHT_API_KEY -> settings.intelligence.api_key) for security.
Returns a validated Settings object.
Implement a get_settings() singleton pattern to be used across the app.
Step 3: Refactor main.py
Remove all hardcoded variables (WHITELIST, LLM Gateway setup).
Import get_settings.
Update WeChatMonitor and SignalProcessor initialization to use values from settings.
Constraints:
Add proper Docstrings.
Ensure SecretStr is handled correctly (use .get_secret_value() when passing to API clients).
If settings.yaml is missing, raise a clear FileNotFoundError with instructions to create it.