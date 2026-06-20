# Discord OAuth2 設定指南

## 步驟 1: 前往 Discord Developer Portal

1. 訪問 https://discord.com/developers/applications
2. 選擇你的機器人應用
3. 點擊左側的 "OAuth2" → "General"

## 步驟 2: 設定 Redirect URI

在 "Redirects" 區域添加：
```
http://localhost:8080/callback
```

如果你使用不同的端口或域名，請相應修改。

## 步驟 3: 獲取 Client ID 和 Client Secret

1. **Client ID**: 在 OAuth2 頁面頂部可以看到
2. **Client Secret**: 點擊 "Reset Secret" 按鈕生成新的密鑰（只會顯示一次，請妥善保存）

## 步驟 4: 更新 .env 文件

將以下資訊填入 `.env` 文件：

```env
DISCORD_CLIENT_ID=你的客戶端ID
DISCORD_CLIENT_SECRET=你的客戶端密鑰
DISCORD_REDIRECT_URI=http://localhost:8080/callback
```

## 步驟 5: 生成 Session Secret

在終端運行以下指令生成安全的 session 密鑰：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

將輸出的字串填入 `.env` 文件：

```env
SESSION_SECRET=生成的密鑰
```

## 步驟 6: 啟動機器人

```bash
python bot.py
```

## 步驟 7: 訪問控制台

打開瀏覽器訪問：
```
http://localhost:8080
```

點擊 "使用 Discord 登錄" 按鈕即可登入後台！

## 安全提醒

⚠️ **重要**: 
- 永遠不要將 `.env` 文件提交到 Git
- CLIENT_SECRET 和 SESSION_SECRET 必須保密
- 如果密鑰洩露，請立即在 Discord Developer Portal 重置

## 功能說明

登錄後可以查看：
- ✅ 機器人統計數據（伺服器數、用戶數、頻道數）
- ✅ 運行時間
- ✅ 快速功能入口

## 疑難排解

### 登錄失敗
- 確認 CLIENT_ID 和 CLIENT_SECRET 正確
- 確認 Redirect URI 完全匹配
- 檢查瀏覽器控制台是否有錯誤

### Session 失效
- 確認 SESSION_SECRET 已設定
- 重新生成 SESSION_SECRET 並重啟機器人
