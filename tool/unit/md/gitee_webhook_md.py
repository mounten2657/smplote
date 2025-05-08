import hmac
import hashlib
from flask import request
from tool.core.env import Env


class GiteeWebhookMd:

    @staticmethod
    def get_push_md(secret_token=None):
        """
        处理 Gitee Webhook 推送 (push 事件)
        返回格式化后的 Markdown 消息

        参数:
            secret_token: Gitee Webhook 的签名密钥（可选）

        返回:
            Tuple (status_code, response_data)
        """
        # 验证签名（如果配置了密钥）
        secret_token = secret_token if secret_token else Env.get('GITEE_SECRETE_TOKEN')
        if secret_token and False:  # 暂时屏蔽签名验证
            signature = request.headers.get('X-Gitee-Token')
            if not signature:
                return 401, {"error": "Missing signature"}

            # 计算 HMAC SHA256 签名
            computed_signature = hmac.new(
                secret_token.encode('utf-8'),
                request.data,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, computed_signature):
                return 403, {"error": "Invalid signature"}

        # 解析推送数据
        try:
            payload = request.json
            hook_name = payload['hook_name']
            repo = payload['repository']['name']
            branch = payload['ref'].split('/')[-1]
            pusher = payload['pusher']['name']
            compare_url = payload['compare']
            commits = payload['commits']

            # 只处理 push 事件
            if hook_name != 'push_hooks':
                return 200, {"message": "Ignored non-push event"}

            # 生成 Markdown 消息
            md_message = f"""🚀 **Gitee 代码推送通知**  

    📦 仓库: [{repo}]({payload['repository']['html_url']})  
    🌿 分支: {branch}
    🦸‍♂️ 成员: {pusher}

    📝 **提交记录** ({len(commits)}个):  
    {compare_url}
"""
            # 添加每个提交的详细信息
            for commit in commits[:3]:  # 最多显示3个提交
                for file in commit['modified']:
                    md_message += f"     - {file}\r\n"
                md_message += f"     - [{commit['id'][:7]}]({commit['url']}): {commit['message']}\r\n"
                md_message += f"    ⏱️️ {str(commit['timestamp']).replace('T', ' ')[:19]}\r\n"
                md_message += f"    👨‍💻️ {commit['author']['name']}\r\n"

            if len(commits) > 3:
                md_message += f"\n...等 {len(commits) - 3}个提交"

            return 200, {
                "markdown": md_message,
                "compare_url": compare_url,
                "repo_name": repo
            }

        except Exception as e:
            return 400, {"error": f"Invalid payload: {str(e)}"}

