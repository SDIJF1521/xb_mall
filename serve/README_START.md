# 启动说明

## ⚠️ 重要提示

**请务必使用 Python 3.10.5 运行应用！**

直接运行 `fastapi dev` 会使用 Python 3.12.9（PATH 中的默认版本），这会导致模块缺失错误。

## 正确的启动方式

### 方式 1：使用启动脚本（推荐）

**PowerShell:**
```powershell
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
.\start.ps1
```

**CMD:**
```cmd
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
start.bat
```

### 方式 2：直接使用 Python 3.10.5

```powershell
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
C:\Python3.10.5\python.exe -m fastapi dev main.py
```

### 方式 3：使用 uvicorn（备选）

```powershell
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
C:\Python3.10.5\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## ❌ 错误的方式

**不要直接运行：**
```powershell
fastapi dev main.py  # ❌ 这会使用 Python 3.12.9
```

## 验证 Python 版本

运行前可以验证：
```powershell
C:\Python3.10.5\python.exe --version
# 应该显示: Python 3.10.5
```












