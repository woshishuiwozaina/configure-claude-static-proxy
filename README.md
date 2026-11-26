# 配置 Claude 静态代理

这个 Codex Skill 把你已有的静态 SOCKS5 代理配置提交给 Claude 安全助手，由客户端自动检测。

## 1. 安装

在 Codex 里发送下面两行。安装后如果找不到这个 Skill，重启 Codex 再试。

```text
$skill-installer 请安装这个 Skill
https://github.com/woshishuiwozaina/configure-claude-static-proxy/tree/main/configure-claude-static-proxy
```

## 2. 调起并发代理信息

在 Codex 输入 `/skills`，选择「配置 Claude 静态代理」。也可以在输入框输入 `$`，选择 `configure-claude-static-proxy`。

打开 IPFly 的 SOCKS5 代理信息页，任选一种方式发给自己的 Codex 会话。

- **发截图**。截取同一条代理记录，确保代理主机、端口号、账号和密码都清晰可见。
- **发文字**。复制同一条记录的四项信息。下面是填写格式，示例值请换成自己的。

  ```text
  代理主机  proxy.example
  端口号    1080
  账号      example-user
  密码      example-password
  ```

真实截图和代理凭据仅用于自己的 Codex 会话，请勿贴到仓库或公开讨论区。

## 3. 等待检测

看到「静态代理配置已提交」后，保持 Claude 安全助手打开。检测通过后，客户端会自动进入功能页。

运行脚本需要本机安装 Python 3。使用方式参见 [Codex Skills 文档](https://learn.chatgpt.com/zh-Hans/docs/build-skills)。
