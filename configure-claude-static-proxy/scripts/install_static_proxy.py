#!/usr/bin/env python3
"""Write a pending static SOCKS5 proxy request for Claude 安全助手."""

from __future__ import annotations

import argparse
import json
import os
import platform
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit


APP_NAMES = ("Claude 安全助手", "claude-safe-client")
STATE_FILES = ("license-session.json", "local-proxy.json", "claude-env", "settings.json")


class ConfigurationError(ValueError):
    pass


def read_proxy_url(args: argparse.Namespace) -> str:
    if args.proxy_url_stdin:
        return sys.stdin.read().strip()
    if args.proxy_url:
        return args.proxy_url.strip()
    raise ConfigurationError("请通过 --proxy-url-stdin 或 --proxy-url 提供静态 SOCKS5 地址。")


def normalize_proxy_url(value: str) -> str:
    if not value:
        raise ConfigurationError("静态 SOCKS5 地址不能为空。")
    if any(character.isspace() for character in value):
        raise ConfigurationError("静态 SOCKS5 地址不能包含空格或换行。")

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"socks5", "socks5h"}:
        raise ConfigurationError("静态 SOCKS5 地址必须以 socks5:// 或 socks5h:// 开头。")
    try:
        port = parsed.port
    except ValueError as error:
        raise ConfigurationError("静态 SOCKS5 端口无效。") from error
    if not parsed.hostname or not port or not 1 <= port <= 65535:
        raise ConfigurationError("静态 SOCKS5 地址必须包含有效的主机和端口。")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ConfigurationError("静态 SOCKS5 地址不能包含路径、查询参数或片段。")
    if bool(parsed.username) != bool(parsed.password):
        raise ConfigurationError("静态 SOCKS5 用户名和密码必须同时提供，或同时省略。")

    # Re-encode credentials so reserved characters cannot break the URL.
    username = quote(unquote(parsed.username or ""), safe="")
    password = quote(unquote(parsed.password or ""), safe="")
    credentials = f"{username}:{password}@" if username else ""
    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    return urlunsplit((parsed.scheme.lower(), f"{credentials}{hostname}:{port}", "", "", ""))


def candidate_app_dirs() -> list[Path]:
    system = platform.system().lower()
    home = Path.home()
    if system == "darwin":
        bases = [home / "Library" / "Application Support"]
    elif system == "windows":
        configured = os.environ.get("APPDATA")
        if not configured:
            raise ConfigurationError("无法读取 APPDATA，请使用 --app-data-dir 指定客户端数据目录。")
        bases = [Path(configured)]
    else:
        configured = os.environ.get("XDG_CONFIG_HOME")
        bases = [Path(configured)] if configured else [home / ".config"]
    return [base / app_name for base in bases for app_name in APP_NAMES]


def resolve_app_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    candidates = candidate_app_dirs()
    existing = [
        candidate
        for candidate in candidates
        if any((candidate / state_file).is_file() for state_file in STATE_FILES)
    ]
    if len(existing) == 1:
        return existing[0]
    if len(existing) > 1:
        raise ConfigurationError(
            "发现多个客户端数据目录，请使用 --app-data-dir 指定正确目录。"
        )
    return candidates[0]


def write_atomic(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        os.chmod(temporary_path, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            # Windows uses ACLs and does not apply POSIX mode bits.
            pass
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="为 Claude 安全助手写入静态 SOCKS5 请求；客户端会自动检测并解锁。",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--proxy-url", help="完整 SOCKS5 地址")
    source.add_argument(
        "--proxy-url-stdin",
        action="store_true",
        help="从标准输入读取完整 SOCKS5 地址，避免出现在命令行参数中",
    )
    parser.add_argument(
        "--app-data-dir",
        help="客户端用户数据目录；仅在自动定位失败时使用",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        proxy_url = normalize_proxy_url(read_proxy_url(args))
        app_dir = resolve_app_dir(args.app_data_dir)
        target = app_dir / "static-proxy-request.json"
        write_atomic(target, {
            "proxyUrl": proxy_url,
            "source": "configure-claude-static-proxy",
            "requestedAt": datetime.now(timezone.utc).isoformat(),
        })
    except (ConfigurationError, OSError) as error:
        print(f"配置失败：{error}", file=sys.stderr)
        return 1

    print(f"静态代理配置已提交：{target}")
    print("请保持 Claude 安全助手打开。客户端会自动检测，成功后进入功能页。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
