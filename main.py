import os
import re
import shutil
import aiohttp  # 导入 aiohttp 用于发送 HTTP 请求
from datetime import datetime
from astrbot.api.event.filter import *
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.all import *  # 导入所有API

@register("mccloud_command", "MC云-小馒头", "用于修改插件命令的工具，支持备份和恢复，仅限管理员使用。/cmd 查看帮助", "1.0")
class CmdManager(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @command("cmd")  # 使用从 event.filter 导入的 command
    @permission_type(PermissionType.ADMIN)  # 仅限管理员使用
    async def handle_cmd_change(self, event: AstrMessageEvent):
        '''修改插件命令
        用法: /cmd 插件名 旧命令 新命令
        例如: /cmd mccloud_site sitehelp sitecmd'''
        
        # 获取消息内容
        messages = event.get_messages()
        if not messages:
            yield event.plain_result("请输入正确的格式：/cmd 插件名 旧命令 新命令")
            return
        
        message_text = messages[0].text
        print("handle_cmd_change called with:", message_text)  # 调试输出
        parts = message_text.split()
        
        if len(parts) != 4:
            print(f"参数数量错误: {len(parts)}，期望4个参数")  # 调试输出
            yield event.plain_result("请输入正确的格式：/cmd 插件名 旧命令 新命令")
            return
        
        plugin_name = parts[1]
        old_command = parts[2]
        new_command = parts[3]
        
        print(f"插件名: {plugin_name}, 旧命令: {old_command}, 新命令: {new_command}")  # 调试输出
        
        # 验证新命令格式
        if not re.match(r'^[a-zA-Z0-9_]+$', new_command):
            yield event.plain_result("新命令只能包含字母、数字和下划线")
            return
        
        # 构建插件文件路径
        plugin_path = f"./data/plugins/{plugin_name}/main.py"
        
        # 检查文件是否存在
        if not os.path.exists(plugin_path):
            print(f"找不到插件文件: {plugin_path}")  # 调试输出
            yield event.plain_result(f"找不到插件 {plugin_name} 的主文件")
            return
        
        try:
            # 创建备份
            backup_path = f"{plugin_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(plugin_path, backup_path)
            
            # 读取文件内容
            with open(plugin_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 使用正则表达式查找并替换命令
            pattern = f'command\("{old_command}"\)'  # 修改为 command
            if not re.search(pattern, content):
                print(f"未找到命令: {old_command} 在 {plugin_path} 中")  # 调试输出
                yield event.plain_result(f"未找到命令 {old_command}")
                return
            
            replacement = f'command("{new_command}")'  # 修改为 command
            new_content = re.sub(pattern, replacement, content)
            
            # 写入修改后的内容
            with open(plugin_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # 发送请求到指定的 API
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:6185/api/plugin/reload", json={"name": plugin_name}) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "ok":
                            yield event.plain_result(f"成功将命令 {old_command} 修改为 {new_command}，并重载插件 {plugin_name}。\n原文件已备份为: {os.path.basename(backup_path)}")
                        else:
                            yield event.plain_result(f"成功将命令 {old_command} 修改为 {new_command}，但重载插件时出错：{result.get('message')}")
                    else:
                        yield event.plain_result(f"成功将命令 {old_command} 修改为 {new_command}，但重载插件时请求失败，状态码：{response.status}")
        
        except Exception as e:
            yield event.plain_result(f"修改命令时出错：{str(e)}\n如有备份文件请检查 {plugin_path}.*.bak")