import discord
from discord.ext import commands
import os
import asyncio

class LoggingSystem(commands.Cog):
    """日誌系統 - 記錄所有指令使用"""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = os.getenv('LOG_CHANNEL_ID')
    
    async def send_log(self, user_name: str, command_name: str, response: str):
        """發送日誌到指定頻道"""
        if not self.log_channel_id:
            return
        
        try:
            channel = self.bot.get_channel(int(self.log_channel_id))
            if not channel:
                print(f"⚠️  找不到日誌頻道 ID: {self.log_channel_id}")
                return
            
            # 根據指令類型选择顏色
            if "娛樂" in command_name:
                color = discord.Color.purple()  # 紫色 - 娛樂
                emoji = "🎮"
            elif "管理" in command_name:
                color = discord.Color.red()  # 红色 - 管理
                emoji = "🔨"
            elif "一般" in command_name:
                color = discord.Color.blue()  # 蓝色 - 一般
                emoji = "ℹ️"
            else:
                color = discord.Color.green()  # 绿色 - 其他
                emoji = "📝"
            
            # 創建彩色Embed
            embed = discord.Embed(
                title=f"{emoji} 指令日誌",
                color=color,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="👤 用戶", value=f"`{user_name}`", inline=True)
            embed.add_field(name="⚡ 指令", value=f"`{command_name}`", inline=True)
            embed.add_field(name="💬 響應", value=response, inline=False)
            embed.set_footer(text="指令執行記錄")
            
            # 發送日誌
            await channel.send(embed=embed)
        except (ValueError, AttributeError) as e:
            print(f"❌ 日誌發送失败: {e}")
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")
    
    def _extract_response_content(self, message):
        """从訊息对象提取響應内容"""
        try:
            # 优先获取文字内容
            if message.content:
                content = message.content
            # 如果是embed訊息
            elif message.embeds:
                embed = message.embeds[0]
                if embed.title:
                    content = embed.title
                elif embed.description:
                    content = embed.description
                else:
                    content = "Embed訊息"
            else:
                content = "已響應"
            
            # 限制長度，避免日誌过长
            if len(content) > 100:
                content = content[:97] + "..."
            
            return content
        except Exception as e:
            print(f"❌ 提取響應内容失败: {e}")
            return "已響應"
    
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        """当slash command完成时触发"""
        try:
            # 获取用戶名
            user_name = str(interaction.user)
            
            # 获取完整指令名（包括组名）
            command_name = command.name
            if hasattr(command, 'parent') and command.parent:
                command_name = f"/{command.parent.name} {command.name}"
            else:
                command_name = f"/{command_name}"
            
            # 等待一小段時間确保響應已發送
            await asyncio.sleep(0.5)
            
            # 尝试获取原始響應訊息
            try:
                original_message = await interaction.original_response()
                response = self._extract_response_content(original_message)
            except:
                # 如果无法获取原始響應，使用預設文字
                response = "已執行指令"
            
            # 記錄日誌
            await self.send_log(user_name, command_name, response)
                
        except Exception as e:
            print(f"❌ 記錄日誌时出錯: {e}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')
        if self.log_channel_id:
            print(f'📝 日誌頻道ID: {self.log_channel_id}')
        else:
            print('⚠️  未設定日誌頻道ID (LOG_CHANNEL_ID) - 日誌功能已禁用')

async def setup(bot):
    await bot.add_cog(LoggingSystem(bot))
