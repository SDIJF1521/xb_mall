# 启动说明

## ⚠️ 重要提示

**请务必使用 Python 3.10.5 运行应用！**

直接运行 `fastapi dev` 会使用 Python 3.12.9（PATH 中的默认版本），这会导致模块缺失错误。

## 正确的启动方式

### 方式 1：使用启动脚本（推荐）⭐

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

启动脚本会自动：
- 使用 Python 3.10.5
- 设置 UTF-8 编码
- 使用单进程模式（避免 Windows 多进程问题）

### 方式 2：直接使用 Python 3.10.5

```powershell
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
C:\Python3.10.5\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 --workers 1
```

**注意：** 必须使用 `--workers 1` 参数，避免 Windows 多进程导入问题。

### 方式 3：使用 fastapi dev（备选，不推荐）

```powershell
cd C:\Users\Lkpap\Desktop\porject\xb_mall\serve
C:\Python3.10.5\python.exe -m fastapi dev main.py --workers 1
```

**注意：** `fastapi dev` 命令可能会使用多进程，如果遇到导入错误，请使用方式1或方式2。

## ❌ 错误的方式

**不要直接运行：**
```powershell
fastapi dev main.py  # ❌ 这会使用 Python 3.12.9
uvicorn main:app --reload --workers 4  # ❌ Windows 上多进程会有问题
```

## Windows 多进程问题修复

如果遇到以下错误：
- `KeyboardInterrupt` 在导入模块时
- `distutils.version` 导入错误
- 多进程启动失败

**解决方案：**
1. 使用启动脚本（推荐）
2. 或确保使用 `--workers 1` 参数
3. 应用已添加 Windows 兼容性修复代码

## 验证 Python 版本

运行前可以验证：
```powershell
C:\Python3.10.5\python.exe --version
# 应该显示: Python 3.10.5
```












