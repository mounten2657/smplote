# Smplote 工具集
[项目地址](https://gitee.com/mounten2657/smplote/)
一个基于python的个人小工具，如微信本地数据库解密、信息导出、聊天总结，自动回复，AI问答，消息通知，量化交易等服务。

## 功能特点

- 🔒 本地数据库解密
- 🤖 支持多种AI服务（DeepSeek、Kimi、通义千问、豆包等）
- 📝 自定义提示词模板
- 💬 自动获取群聊消息
- 📊 生成结构化总结
- ✉️ 自动回话或通知
- 🎨 最小化代码设计
- 💾 API密钥安全存储
- 📈 量化交易模型训练

## 安装说明

### 环境要求

- Python 3.12+
- Windows 操作系统
- 微信桌面版 + 微信手机版

### 依赖安装

```bash
cp .env.example .env  # 自行更改好配置项
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 运行程序
```bash
python main.py    # 启动 flask 通过接口激活各模块功能，访问： http://localhost:9090
python main.py -m bot.index.index                                # 首页基本信息
python main.py -m bot.send_msg.auto_reply                        # 自动回复机器人（进程常驻+扫码登陆）
python main.py -m db.refresh_chat_db.refresh_wx_info             # 解密并刷新本地微信账户信息
python main.py -m db.refresh_chat_db.refresh_wx_core_db          # 解密并刷新本地微信核心数据库
python main.py -m db.refresh_chat_db.refresh_wx_real_time_db     # 解密并刷新本地微信实时数据库
python main.py -m db.get_chat_info.check_info                    # 检查当前微信配置
python main.py -m db.get_chat_info.get_wx_info                   # 获取本地保存的微信信息
python main.py -m db.get_chat_info.get_users                     # 获取所有能见的微信用户信息并保存
python main.py -m db.get_chat_info.get_chats                     # 获取所有聊天记录信息并保存
python main.py -m db.get_chat_info.get_sessions                  # 获取所有会话基本信息并保存
python main.py -m db.get_chat_info.get_rooms                     # 获取每个群聊的全部用户信息并保存
python main.py -m db.export_chat.export_group_users              # 导出特定群成员信息
python main.py -m db.export_chat.export_group_chats              # 导出特定群聊天记录
python main.py -m report.daily_report.gen_report                 # 生成日报并保存md文件
python main.py -m report.daily_report.gen_md_img                 # 基于md日报生成图片
```

## 使用说明

### 1. 配置AI服务

在首次使用前，需要配置AI服务的API密钥、自己的wxid以及目标群聊的wxid，修改 `.env` ：
````.env
# ai configure
AI_SERVICE=DeepSeek
AI_API_KEY_DEEPSEEK=xxx
AI_API_KEY_KIMI=
AI_API_KEY_TONGYI=
AI_API_KEY_DOUBAO=

# wx configure
WX_WXID_A1=wxid_xxx
WX_WXID_A2=
WX_WXID_G1=xxx@chatroom
WX_WXID_G2=
````


## 目录结构

- `app`：应用入口文件夹
- `config`：配置文件夹
- `data`：数据文件夹
- `model`：数据库模型文件夹
- `service`：业务服务文件夹
- `storage`：临时文件夹
- `tool`：基础工具文件夹
- `utils`：模型工具文件夹
- `vpp`：虚拟服务文件夹
- `vps`：vps微服务文件夹
- `main.py`：主程序文件

## 免责声明
- 这个项目免费开源，不存在收费。
- 本工具仅供学习和技术研究使用，不得用于任何商业或非法行为。
- 本工具的作者不对本工具的安全性、完整性、可靠性、有效性、正确性或适用性做任何明示或暗示的保证，也不对本工具的使用或滥用造成的任何直接或间接的损失、责任、索赔、要求或诉讼承担任何责任。
- 本工具的作者保留随时修改、更新、删除或终止本工具的权利，无需事先通知或承担任何义务。
- 本工具的使用者应遵守相关法律法规，尊重微信的版权和隐私，不得侵犯微信或其他第三方的合法权益，不得从事任何违法或不道德的行为。
- 本工具的使用者在下载、安装、运行或使用本工具时，即表示已阅读并同意本免责声明。如有异议，请立即停止使用本工具，并删除所有相关文件。
- 代码仅用于对技术的交流学习使用，禁止用于实际生产项目，请勿用于非法用途和商业用途！如因此产生任何法律纠纷，均与作者无关！


## 联系方式

请加QQ(591017031)联系作者本人。

---

