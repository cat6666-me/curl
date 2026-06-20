import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class Welcome(commands.Cog):
    """歡迎與離開系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.settings = {}
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_data_file(self, guild_id: str):
        """獲取伺服器數據檔案路徑"""
        guild_dir = os.path.join(self.data_dir, guild_id)
        os.makedirs(guild_dir, exist_ok=True)
        return os.path.join(guild_dir, "welcome.json")
    
    def load_settings(self, guild_id: str):
        """載入伺服器設定"""
        data_file = self.get_data_file(guild_id)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "welcome_enabled": False,
            "welcome_channel": None,
            "welcome_message": "歡迎 {user} 加入 {server}！",
            "leave_enabled": False,
            "leave_channel": None,
            "leave_message": "{user} 離開了 {server}..."
        }
    
    def save_settings(self, guild_id: str):
        """保存伺服器設定"""
        data_file = self.get_data_file(guild_id)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings.get(guild_id, {}), f, indent=2, ensure_ascii=False)
    
    def get_settings(self, guild_id: str):
        """獲取伺服器設定（每次都重新載入以確保同步網頁修改）"""
        # 每次都重新讀取檔案，確保與網頁修改同步
        self.settings[guild_id] = self.load_settings(guild_id)
        return self.settings[guild_id]
    
    # 創建指令組
    welcome_group = app_commands.Group(name="歡迎系統", description="歡迎與離開系統設定")
    
    @welcome_group.command(name="設定歡迎頻道", description="設定歡迎訊息發送頻道")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="選擇歡迎訊息發送的頻道")
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """設定歡迎頻道"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["welcome_channel"] = channel.id
        settings["welcome_enabled"] = True
        self.save_settings(guild_id)
        
        await interaction.response.send_message(
            f"✅ 歡迎訊息頻道已設定為 {channel.mention}",
            ephemeral=True
        )
    
    @welcome_group.command(name="設定歡迎訊息", description="自訂歡迎訊息")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(message="歡迎訊息內容（使用 {user} 代表用戶，{server} 代表伺服器名稱）")
    async def set_welcome_message(self, interaction: discord.Interaction, message: str):
        """設定歡迎訊息"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["welcome_message"] = message
        self.save_settings(guild_id)
        
        await interaction.response.send_message(
            f"✅ 歡迎訊息已設定為：\n{message}",
            ephemeral=True
        )
    
    @welcome_group.command(name="設定離開頻道", description="設定離開訊息發送頻道")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="選擇離開訊息發送的頻道")
    async def set_leave_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """設定離開頻道"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["leave_channel"] = channel.id
        settings["leave_enabled"] = True
        self.save_settings(guild_id)
        
        await interaction.response.send_message(
            f"✅ 離開訊息頻道已設定為 {channel.mention}",
            ephemeral=True
        )
    
    @welcome_group.command(name="設定離開訊息", description="自訂離開訊息")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(message="離開訊息內容（使用 {user} 代表用戶，{server} 代表伺服器名稱）")
    async def set_leave_message(self, interaction: discord.Interaction, message: str):
        """設定離開訊息"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["leave_message"] = message
        self.save_settings(guild_id)
        
        await interaction.response.send_message(
            f"✅ 離開訊息已設定為：\n{message}",
            ephemeral=True
        )
    
    @welcome_group.command(name="開關", description="開啟或關閉歡迎/離開系統")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        system="選擇系統",
        enabled="開啟或關閉"
    )
    @app_commands.choices(system=[
        app_commands.Choice(name="歡迎系統", value="welcome"),
        app_commands.Choice(name="離開系統", value="leave")
    ])
    async def toggle(self, interaction: discord.Interaction, system: str, enabled: bool):
        """開關系統"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        if system == "welcome":
            settings["welcome_enabled"] = enabled
            system_name = "歡迎系統"
        else:
            settings["leave_enabled"] = enabled
            system_name = "離開系統"
        
        self.save_settings(guild_id)
        
        status = "開啟" if enabled else "關閉"
        await interaction.response.send_message(
            f"✅ {system_name}已{status}",
            ephemeral=True
        )
    
    @welcome_group.command(name="查看設定", description="查看當前設定")
    async def view_settings(self, interaction: discord.Interaction):
        """查看設定"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        embed = discord.Embed(
            title="👋 歡迎系統設定",
            color=discord.Color.green()
        )
        
        # 歡迎系統
        welcome_status = "✅ 已開啟" if settings["welcome_enabled"] else "❌ 已關閉"
        welcome_channel = f"<#{settings['welcome_channel']}>" if settings["welcome_channel"] else "未設定"
        
        embed.add_field(
            name="歡迎系統",
            value=f"狀態：{welcome_status}\n頻道：{welcome_channel}\n訊息：{settings['welcome_message']}",
            inline=False
        )
        
        # 離開系統
        leave_status = "✅ 已開啟" if settings["leave_enabled"] else "❌ 已關閉"
        leave_channel = f"<#{settings['leave_channel']}>" if settings["leave_channel"] else "未設定"
        
        embed.add_field(
            name="離開系統",
            value=f"狀態：{leave_status}\n頻道：{leave_channel}\n訊息：{settings['leave_message']}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """成員加入事件"""
        guild_id = str(member.guild.id)
        # 每次都從檔案重新讀取，確保同步網頁修改
        settings = self.load_settings(guild_id)
        
        if not settings["welcome_enabled"] or not settings["welcome_channel"]:
            return
        
        channel = member.guild.get_channel(settings["welcome_channel"])
        if not channel:
            return
        
        message = settings["welcome_message"].format(
            user=member.mention,
            server=member.guild.name
        )
        
        embed = discord.Embed(
            title="👋 新成員加入！",
            description=message,
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="成員數量", value=f"{member.guild.member_count} 位成員")
        embed.timestamp = discord.utils.utcnow()
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """成員離開事件"""
        guild_id = str(member.guild.id)
        # 每次都從檔案重新讀取，確保同步網頁修改
        settings = self.load_settings(guild_id)
        
        if not settings["leave_enabled"] or not settings["leave_channel"]:
            return
        
        channel = member.guild.get_channel(settings["leave_channel"])
        if not channel:
            return
        
        message = settings["leave_message"].format(
            user=member.name,
            server=member.guild.name
        )
        
        embed = discord.Embed(
            title="👋 成員離開",
            description=message,
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="剩餘成員", value=f"{member.guild.member_count} 位成員")
        embed.timestamp = discord.utils.utcnow()
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')
        # 載入所有伺服器的設定
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            self.settings[guild_id] = self.load_settings(guild_id)
        print(f'👋 已載入 {len(self.settings)} 個伺服器的歡迎系統設定')

async def setup(bot):
    await bot.add_cog(Welcome(bot))
