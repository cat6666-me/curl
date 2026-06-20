import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime

class Birthday(commands.Cog):
    """生日提醒系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.birthdays = {}
        self.settings = {}
        os.makedirs(self.data_dir, exist_ok=True)
        self.check_birthdays.start()
    
    def cog_unload(self):
        """停止背景任務"""
        self.check_birthdays.cancel()
    
    def get_data_file(self, guild_id: str, file_type: str):
        """獲取伺服器數據檔案路徑"""
        guild_dir = os.path.join(self.data_dir, guild_id)
        os.makedirs(guild_dir, exist_ok=True)
        return os.path.join(guild_dir, f"{file_type}.json")
    
    def load_birthdays(self, guild_id: str):
        """載入生日數據"""
        data_file = self.get_data_file(guild_id, "birthdays")
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_birthdays(self, guild_id: str):
        """保存生日數據"""
        data_file = self.get_data_file(guild_id, "birthdays")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.birthdays.get(guild_id, {}), f, indent=2, ensure_ascii=False)
    
    def load_settings(self, guild_id: str):
        """載入設定"""
        data_file = self.get_data_file(guild_id, "birthday_settings")
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "enabled": False,
            "channel_id": None,
            "message": "🎂 今天是 {user} 的生日！祝生日快樂！🎉"
        }
    
    def save_settings(self, guild_id: str):
        """保存設定"""
        data_file = self.get_data_file(guild_id, "birthday_settings")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings.get(guild_id, {}), f, indent=2, ensure_ascii=False)
    
    def get_birthdays(self, guild_id: str):
        """獲取生日數據"""
        if guild_id not in self.birthdays:
            self.birthdays[guild_id] = self.load_birthdays(guild_id)
        return self.birthdays[guild_id]
    
    def get_settings(self, guild_id: str):
        """獲取設定"""
        if guild_id not in self.settings:
            self.settings[guild_id] = self.load_settings(guild_id)
        return self.settings[guild_id]
    
    # 創建指令組
    birthday_group = app_commands.Group(name="生日", description="生日提醒系統")
    
    @birthday_group.command(name="設定", description="設定你的生日")
    @app_commands.describe(
        month="月份 (1-12)",
        day="日期 (1-31)"
    )
    async def set_birthday(self, interaction: discord.Interaction, month: int, day: int):
        """設定生日"""
        # 驗證日期
        if month < 1 or month > 12:
            await interaction.response.send_message("❌ 月份必須在 1-12 之間", ephemeral=True)
            return
        
        if day < 1 or day > 31:
            await interaction.response.send_message("❌日期必須在 1-31 之間", ephemeral=True)
            return
        
        try:
            # 檢查日期是否有效
            datetime(2024, month, day)
        except ValueError:
            await interaction.response.send_message("❌ 無效的日期", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        birthdays = self.get_birthdays(guild_id)
        birthdays[user_id] = {
            "month": month,
            "day": day,
            "username": interaction.user.name
        }
        
        self.save_birthdays(guild_id)
        
        await interaction.response.send_message(
            f"✅ 生日已設定為 **{month} 月 {day} 日**",
            ephemeral=True
        )
    
    @birthday_group.command(name="查看", description="查看生日")
    @app_commands.describe(user="要查看的用戶（可選）")
    async def view_birthday(self, interaction: discord.Interaction, user: discord.Member = None):
        """查看生日"""
        user = user or interaction.user
        
        if user.bot:
            await interaction.response.send_message("❌ 機器人沒有生日！", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        birthdays = self.get_birthdays(guild_id)
        
        if user_id not in birthdays:
            await interaction.response.send_message(
                f"❌ {user.mention} 還沒有設定生日",
                ephemeral=True
            )
            return
        
        bd = birthdays[user_id]
        
        embed = discord.Embed(
            title=f"🎂 {user.name} 的生日",
            description=f"**{bd['month']} 月 {bd['day']} 日**",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # 計算距離生日還有多少天
        today = datetime.now()
        next_birthday = datetime(today.year, bd['month'], bd['day'])
        
        if next_birthday < today:
            next_birthday = datetime(today.year + 1, bd['month'], bd['day'])
        
        days_until = (next_birthday - today).days
        
        if days_until == 0:
            embed.add_field(name="距離生日", value="🎉 今天就是生日！", inline=False)
        else:
            embed.add_field(name="距離生日", value=f"還有 **{days_until}** 天", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @birthday_group.command(name="列表", description="查看本月壽星")
    async def list_birthdays(self, interaction: discord.Interaction):
        """列出本月生日"""
        guild_id = str(interaction.guild.id)
        birthdays = self.get_birthdays(guild_id)
        
        if not birthdays:
            await interaction.response.send_message("❌ 目前沒有任何生日記錄", ephemeral=True)
            return
        
        current_month = datetime.now().month
        
        # 過濾本月生日
        month_birthdays = [
            (user_id, bd) for user_id, bd in birthdays.items()
            if bd["month"] == current_month
        ]
        
        month_birthdays.sort(key=lambda x: x[1]["day"])
        
        if not month_birthdays:
            await interaction.response.send_message("❌ 本月沒有壽星", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎂 {current_month} 月壽星",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        for user_id, bd in month_birthdays:
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f"{bd['month']}/{bd['day']} - {user.name}",
                    value=f"{user.mention}",
                    inline=False
                )
            except:
                continue
        
        await interaction.response.send_message(embed=embed)
    
    @birthday_group.command(name="刪除", description="刪除你的生日")
    async def delete_birthday(self, interaction: discord.Interaction):
        """刪除生日"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        birthdays = self.get_birthdays(guild_id)
        
        if user_id not in birthdays:
            await interaction.response.send_message("❌ 你還沒有設定生日", ephemeral=True)
            return
        
        del birthdays[user_id]
        self.save_birthdays(guild_id)
        
        await interaction.response.send_message("✅ 已刪除你的生日", ephemeral=True)
    
    @birthday_group.command(name="設定頻道", description="設定生日提醒頻道（需要管理員權限）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="選擇生日提醒頻道")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """設定生日頻道"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["channel_id"] = channel.id
        settings["enabled"] = True
        self.save_settings(guild_id)
        
        await interaction.response.send_message(
            f"✅ 生日提醒頻道已設定為 {channel.mention}",
            ephemeral=True
        )
    
    @birthday_group.command(name="開關", description="開啟或關閉生日提醒（需要管理員權限）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(enabled="開啟或關閉")
    async def toggle(self, interaction: discord.Interaction, enabled: bool):
        """開關生日提醒"""
        guild_id = str(interaction.guild.id)
        settings = self.get_settings(guild_id)
        
        settings["enabled"] = enabled
        self.save_settings(guild_id)
        
        status = "開啟" if enabled else "關閉"
        await interaction.response.send_message(
            f"✅ 生日提醒已{status}",
            ephemeral=True
        )
    
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """每天檢查生日"""
        today = datetime.now()
        
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            settings = self.get_settings(guild_id)
            
            if not settings["enabled"] or not settings["channel_id"]:
                continue
            
            channel = guild.get_channel(settings["channel_id"])
            if not channel:
                continue
            
            birthdays = self.get_birthdays(guild_id)
            
            # 檢查今天是否有人生日
            for user_id, bd in birthdays.items():
                if bd["month"] == today.month and bd["day"] == today.day:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        
                        message = settings["message"].format(
                            user=user.mention,
                            server=guild.name
                        )
                        
                        embed = discord.Embed(
                            title="🎂 生日快樂！",
                            description=message,
                            color=discord.Color.purple()
                        )
                        embed.set_thumbnail(url=user.display_avatar.url)
                        embed.timestamp = discord.utils.utcnow()
                        
                        await channel.send(embed=embed)
                    except:
                        continue
    
    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        """等待機器人準備就緒"""
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')
        # 載入所有伺服器的數據
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            self.birthdays[guild_id] = self.load_birthdays(guild_id)
            self.settings[guild_id] = self.load_settings(guild_id)
        print(f'🎂 已載入 {len(self.birthdays)} 個伺服器的生日數據')

async def setup(bot):
    await bot.add_cog(Birthday(bot))
