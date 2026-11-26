---
name: configure-claude-static-proxy
description: 为“Claude 安全助手”配置或更换静态 IP（静态 SOCKS5 代理），并配合客户端自动检测进入功能页；不用于配置系统代理、Clash/Mihomo 规则或其他应用。
---

# 配置 Claude 静态代理

使用随附脚本把静态 SOCKS5 配置提交给“Claude 安全助手”。客户端会自行校验入口代理、静态代理出口、时区和授权，成功后自动进入功能页；不要直接修改客户端的 `local-proxy.json`、`claude-env` 或授权文件。

## 工作流程

1. 请用户提供完整的静态代理地址：`socks5://用户名:密码@主机:端口` 或 `socks5h://用户名:密码@主机:端口`。如果用户只提供主机、端口、用户名和密码，组合成完整地址；没有凭据时省略用户名和密码。
2. 运行本 skill 的 `scripts/install_static_proxy.py`，通过标准输入传入地址：

   ```bash
   python3 <skill-dir>/scripts/install_static_proxy.py --proxy-url-stdin
   ```

3. 看到“静态代理配置已提交”后，告诉用户保持“Claude 安全助手”打开。客户端会每几秒自动检测一次，成功后会直接进入功能页，无需重启客户端。
4. 如果用户反馈没有成功，先让用户确认本机代理已开启并已设置系统代理，再核对静态代理地址。修正后重新运行脚本；客户端会采用最新请求。

脚本会自动定位 macOS、Windows 或 Linux 上“Claude 安全助手”的用户数据目录，并原子写入权限受限的 `static-proxy-request.json`。仅在自动定位失败时才使用 `--app-data-dir <目录>` 覆盖；不要凭猜测把配置写到其他目录。

## 安全与边界

- 不要把密码写进回复、日志、命令参数或诊断信息。优先使用 `--proxy-url-stdin`，展示地址时只显示已脱敏的主机和端口。
- 不要修改系统代理、静态代理供应商配置、Clash/Mihomo 配置、授权信息或客户端源码；本 skill 的职责仅限提交静态 SOCKS5 地址。
- 如果静态代理连接失败，原样转述客户端显示的“本机代理”和“静态代理”两项状态，帮助用户区分入口网络问题和静态出口问题。
