import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import random

class Leveling(commands.Cog):
    """等級系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.cooldowns = {}  # 防止刷經驗
        self.levels = {}
        # 確保 data 目錄存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_data_file(self, guild_id: str):
        """獲取伺服器數據檔案路徑"""
        guild_dir = os.path.join(self.data_dir, guild_id)
        os.makedirs(guild_dir, exist_ok=True)
        return os.path.join(guild_dir, "levels.json")
    
    def load_data(self, guild_id: str):
        """載入伺服器等級數據"""
        data_file = self.get_data_file(guild_id)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_data(self, guild_id: str):
        """保存伺服器等級數據"""
        data_file = self.get_data_file(guild_id)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.levels.get(guild_id, {}), f, indent=2, ensure_ascii=False)
    
    def get_user_data(self, guild_id: str, user_id: str):
        """获取用戶数据"""
        if guild_id not in self.levels:
            self.levels[guild_id] = self.load_data(guild_id)
        
        if user_id not in self.levels[guild_id]:
            self.levels[guild_id][user_id] = {
                "xp": 0,
                "level": 1,
                "messages": 0,
                "last_message": None
            }
        
        return self.levels[guild_id][user_id]
    
    def calculate_xp_for_level(self, level: int) -> int:
        """計算升到下一級所需經驗"""
        return 100 + (level - 1) * 50
    
    def calculate_level(self, xp: int) -> int:
        """根據經驗計算等級"""
        level = 1
        xp_needed = 100
        
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = self.calculate_xp_for_level(level)
        
        return level
    
    # 創建指令组
    level_group = app_commands.Group(name="等級", description="等級系統")
    
    @level_group.command(name="查看", description="查看等級資訊")
    @app_commands.describe(user="要查看的用戶（可選）")
    async def level(self, interaction: discord.Interaction, user: discord.Member = None):
        """查看等級"""
        user = user or interaction.user
        
        if user.bot:
            await interaction.response.send_message("❌ 機器人沒有等級！", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        data = self.get_user_data(guild_id, user_id)
        
        current_level = data["level"]
        current_xp = data["xp"]
        xp_for_next = self.calculate_xp_for_level(current_level)
        
        # 計算当前等級已獲得的經驗
        total_xp = 0
        for lvl in range(1, current_level):
            total_xp += self.calculate_xp_for_level(lvl)
        
        xp_in_level = current_xp - total_xp
        
        # 創建進度條
        progress = int((xp_in_level / xp_for_next) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        
        embed = discord.Embed(
            title=f"📊 {user.name} 的等級",
            color=user.color or discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(name="等級", value=f"**{current_level}**", inline=True)
        embed.add_field(name="總經驗", value=f"{current_xp} XP", inline=True)
        embed.add_field(name="訊息数", value=f"{data['messages']}", inline=True)
        
        embed.add_field(
            name="升級进度",
            value=f"{bar}\n{xp_in_level}/{xp_for_next} XP ({(xp_in_level/xp_for_next)*100:.1f}%)",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @level_group.command(name="排行榜", description="查看伺服器排行榜")
    async def leaderboard(self, interaction: discord.Interaction):
        """顯示排行榜"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.levels or not self.levels[guild_id]:
            await interaction.response.send_message("❌ 該伺服器还沒有等級数据", ephemeral=True)
            return
        
        # 排序用戶
        sorted_users = sorted(
            self.levels[guild_id].items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )[:10]  # 只顯示前10名
        
        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} 等級排行榜",
            description="前10名用戶",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                medal = medals[idx-1] if idx <= 3 else f"#{idx}"
                
                embed.add_field(
                    name=f"{medal} {user.name}",
                    value=f"等級: **{data['level']}** | 經驗: {data['xp']} XP\n訊息: {data['messages']}",
                    inline=False
                )
            except:
                continue
        
        await interaction.response.send_message(embed=embed)
    
    @level_group.command(name="重置", description="重置用戶等級（需要管理员权限）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user="要重置等級的用戶")
    async def reset(self, interaction: discord.Interaction, user: discord.Member):
        """重置用戶等級"""
        if user.bot:
            await interaction.response.send_message("❌ 无法重置機器人等級", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        # 確保載入數據
        if guild_id not in self.levels:
            self.levels[guild_id] = self.load_data(guild_id)
        
        if guild_id in self.levels and user_id in self.levels[guild_id]:
            del self.levels[guild_id][user_id]
            self.save_data(guild_id)
            await interaction.response.send_message(f"✅ 已重置 {user.mention} 的等級", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 該用戶沒有等級数据", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """监听訊息以增加經驗"""
        # 忽略機器人和私信
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        
        # 冷却時間檢查（60秒内只能獲得一次經驗）
        cooldown_key = f"{guild_id}_{user_id}"
        now = datetime.utcnow()
        
        if cooldown_key in self.cooldowns:
            if now < self.cooldowns[cooldown_key]:
                return
        
        self.cooldowns[cooldown_key] = now + timedelta(seconds=60)
        
        # 获取用戶数据
        data = self.get_user_data(guild_id, user_id)
        
        # 增加訊息计数
        data["messages"] += 1
        
        # 随机增加15-25經驗
        xp_gain = random.randint(15, 25)
        old_level = data["level"]
        data["xp"] += xp_gain
        
        # 計算新等級
        new_level = self.calculate_level(data["xp"])
        data["level"] = new_level
        data["last_message"] = now.isoformat()
        
        # 保存数据
        self.save_data(guild_id)
        
        # 如果升級了，發送訊息
        if new_level > old_level:
            embed = discord.Embed(
                title="🎉 恭喜升級！",
                description=f"{message.author.mention} 升到了 **等級 {new_level}**！",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
    # 載入所有伺服器的數據
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            self.levels[guild_id] = self.load_data(guild_id)
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')
        print(f'📊 已載入 {len(self.levels)} 個伺服器的等級数据')

async def setup(bot):
    await bot.add_cog(Leveling(bot))
