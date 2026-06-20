import discord
from discord import app_commands
from discord.ext import commands
import urllib.parse
from datetime import datetime, timedelta
import re

class Utilities(commands.Cog):
    """實用工具指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # 創建指令组
    util_group = app_commands.Group(name="工具", description="實用工具")
    
    @util_group.command(name="頭像", description="查看用戶頭像")
    @app_commands.describe(user="要查看頭像的用戶")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        """顯示用戶頭像"""
        user = user or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {user.name} 的頭像",
            color=discord.Color.blue()
        )
        embed.set_image(url=user.display_avatar.url)
        embed.add_field(
            name="下載連結",
            value=f"[PNG]({user.display_avatar.with_format('png').url}) | "
                  f"[JPG]({user.display_avatar.with_format('jpg').url}) | "
                  f"[WEBP]({user.display_avatar.with_format('webp').url})"
        )
        
        await interaction.response.send_message(embed=embed)
    
    @util_group.command(name="計算器", description="簡單計算器")
    @app_commands.describe(expression="数学表達式，例如: 2+2 或 10*5")
    async def calculator(self, interaction: discord.Interaction, expression: str):
        """計算数学表達式"""
        try:
            # 只允許安全的字符
            if not re.match(r'^[0-9+\-*/().\s]+$', expression):
                await interaction.response.send_message("❌ 表達式包含非法字符！只允許數字和運算符", ephemeral=True)
                return
            
            # 計算結果
            result = eval(expression)
            
            embed = discord.Embed(
                title="🧮 計算器",
                color=discord.Color.green()
            )
            embed.add_field(name="表達式", value=f"`{expression}`", inline=False)
            embed.add_field(name="結果", value=f"**{result}**", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 計算錯誤: {str(e)}", ephemeral=True)
    
    @util_group.command(name="倒數計時", description="創建一個倒數計時")
    @app_commands.describe(
        minutes="分鐘數",
        reason="倒數計時原因（可選）"
    )
    async def countdown(self, interaction: discord.Interaction, minutes: int, reason: str = "倒數計時"):
        """創建倒數計時"""
        if minutes < 1 or minutes > 60:
            await interaction.response.send_message("❌ 時間必須在1-60分鐘之間", ephemeral=True)
            return
        
        end_time = datetime.utcnow() + timedelta(minutes=minutes)
        
        embed = discord.Embed(
            title="⏰ 倒數計時开始",
            description=f"**{reason}**",
            color=discord.Color.orange()
        )
        embed.add_field(name="时长", value=f"{minutes} 分鐘", inline=True)
        embed.add_field(name="结束時間", value=discord.utils.format_dt(end_time, style='R'), inline=True)
        embed.timestamp = end_time
        
        await interaction.response.send_message(embed=embed)
    
    @util_group.command(name="提醒我", description="設定一個提醒")
    @app_commands.describe(
        duration="时长（分鐘）",
        message="提醒内容"
    )
    async def remind(self, interaction: discord.Interaction, duration: int, message: str):
        """設定提醒"""
        if duration < 1 or duration > 1440:  # 最多24小時
            await interaction.response.send_message("❌ 時間必須在1-1440分鐘之間（最多24小時）", ephemeral=True)
            return
        
        remind_time = datetime.utcnow() + timedelta(minutes=duration)
        
        embed = discord.Embed(
            title="⏰ 提醒已設定",
            description=f"我会在 {discord.utils.format_dt(remind_time, style='R')} 提醒你",
            color=discord.Color.green()
        )
        embed.add_field(name="提醒内容", value=message, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 等待指定時間
        await discord.utils.sleep_until(remind_time)
        
        # 發送提醒
        remind_embed = discord.Embed(
            title="🔔 提醒",
            description=message,
            color=discord.Color.gold()
        )
        remind_embed.set_footer(text=f"你在 {duration} 分鐘前設定了这個提醒")
        
        try:
            await interaction.user.send(embed=remind_embed)
        except:
            # 如果无法私信，就在頻道提醒
            await interaction.channel.send(f"{interaction.user.mention}", embed=remind_embed)
    
    @util_group.command(name="縮短文字", description="縮短长文字")
    @app_commands.describe(
        text="要縮短的文字",
        length="最大長度（預設100）"
    )
    async def shorten(self, interaction: discord.Interaction, text: str, length: int = 100):
        """縮短文字"""
        if len(text) <= length:
            await interaction.response.send_message(f"✅ 文字已经够短了！({len(text)} 字符)", ephemeral=True)
            return
        
        shortened = text[:length-3] + "..."
        
        embed = discord.Embed(
            title="✂️ 文字縮短",
            color=discord.Color.blue()
        )
        embed.add_field(name="原文字", value=f"{text[:100]}..." if len(text) > 100 else text, inline=False)
        embed.add_field(name="縮短后", value=shortened, inline=False)
        embed.add_field(name="統計", value=f"原長度: {len(text)} → 新長度: {len(shortened)}", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @util_group.command(name="隨機數", description="生成隨機數")
    @app_commands.describe(
        minimum="最小值",
        maximum="最大值"
    )
    async def random_number(self, interaction: discord.Interaction, minimum: int, maximum: int):
        """生成隨機數"""
        if minimum >= maximum:
            await interaction.response.send_message("❌ 最小值必須小于最大值", ephemeral=True)
            return
        
        import random
        result = random.randint(minimum, maximum)
        
        embed = discord.Embed(
            title="🎲 隨機數生成器",
            color=discord.Color.purple()
        )
        embed.add_field(name="範圍", value=f"{minimum} - {maximum}", inline=True)
        embed.add_field(name="結果", value=f"**{result}**", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Utilities(bot))
