import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class TempVoice(commands.Cog):
    """臨時語音頻道系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = bot.storage
        # 追蹤臨時頻道 {channel_id: owner_id}
        self.temp_channels = {}
    
    def load_config(self, guild_id: int) -> dict:
        """載入臨時語音配置"""
        return self.storage.load_guild_data(guild_id, 'temp_voice', default={
            'enabled': False,
            'trigger_channel_id': None,
            'category_id': None,
            'channel_name_format': '{username} 的頻道',
            'user_limit': 0,
            'default_bitrate': 64000
        })
    
    def save_config(self, guild_id: int, config: dict):
        """儲存臨時語音配置"""
        self.storage.save_guild_data(guild_id, 'temp_voice', config)
    
    voice_group = app_commands.Group(name="臨時語音", description="臨時語音頻道管理")
    
    @voice_group.command(name="設定", description="設定臨時語音頻道系統")
    @app_commands.describe(
        觸發頻道="加入此頻道將創建臨時語音頻道",
        分類="臨時頻道將創建在此分類下（可選）",
        頻道名稱格式="頻道名稱格式，{username}將被替換為用戶名"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        觸發頻道: discord.VoiceChannel,
        分類: Optional[discord.CategoryChannel] = None,
        頻道名稱格式: Optional[str] = None
    ):
        """設定臨時語音頻道系統"""
        guild_id = interaction.guild.id
        config = self.load_config(guild_id)
        
        config['enabled'] = True
        config['trigger_channel_id'] = 觸發頻道.id
        if 分類:
            config['category_id'] = 分類.id
        if 頻道名稱格式:
            config['channel_name_format'] = 頻道名稱格式
        
        self.save_config(guild_id, config)
        
        embed = discord.Embed(
            title="✅ 臨時語音系統已設定",
            color=discord.Color.from_rgb(37, 99, 235),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="觸發頻道",
            value=觸發頻道.mention,
            inline=False
        )
        if 分類:
            embed.add_field(
                name="頻道分類",
                value=分類.name,
                inline=False
            )
        embed.add_field(
            name="頻道名稱格式",
            value=config['channel_name_format'],
            inline=False
        )
        embed.set_footer(text="用戶加入觸發頻道將自動創建臨時語音頻道")
        
        await interaction.response.send_message(embed=embed)
    
    @voice_group.command(name="停用", description="停用臨時語音頻道系統")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def disable(self, interaction: discord.Interaction):
        """停用臨時語音頻道系統"""
        guild_id = interaction.guild.id
        config = self.load_config(guild_id)
        config['enabled'] = False
        self.save_config(guild_id, config)
        
        await interaction.response.send_message("✅ 臨時語音系統已停用")
    
    @voice_group.command(name="狀態", description="查看臨時語音系統狀態")
    async def status(self, interaction: discord.Interaction):
        """查看臨時語音系統狀態"""
        guild_id = interaction.guild.id
        config = self.load_config(guild_id)
        
        embed = discord.Embed(
            title="🎤 臨時語音系統狀態",
            color=discord.Color.from_rgb(37, 99, 235),
            timestamp=discord.utils.utcnow()
        )
        
        status = "✅ 已啟用" if config['enabled'] else "❌ 已停用"
        embed.add_field(name="狀態", value=status, inline=False)
        
        if config['trigger_channel_id']:
            channel = interaction.guild.get_channel(config['trigger_channel_id'])
            embed.add_field(
                name="觸發頻道",
                value=channel.mention if channel else "頻道已被刪除",
                inline=False
            )
        
        if config['category_id']:
            category = interaction.guild.get_channel(config['category_id'])
            embed.add_field(
                name="頻道分類",
                value=category.name if category else "分類已被刪除",
                inline=False
            )
        
        embed.add_field(
            name="頻道名稱格式",
            value=config['channel_name_format'],
            inline=False
        )
        
        # 統計當前臨時頻道數量
        temp_count = len([ch for ch in self.temp_channels if interaction.guild.get_channel(ch)])
        embed.add_field(
            name="當前臨時頻道",
            value=f"{temp_count} 個",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @voice_group.command(name="限制人數", description="設定你的臨時頻道人數限制")
    @app_commands.describe(人數="最大人數（0為無限制）")
    async def limit(self, interaction: discord.Interaction, 人數: int):
        """設定臨時頻道人數限制"""
        if 人數 < 0 or 人數 > 99:
            await interaction.response.send_message(
                "❌ 人數限制必須在 0-99 之間！",
                ephemeral=True
            )
            return
        
        # 找到用戶的臨時頻道
        user_channel = None
        for channel_id, owner_id in self.temp_channels.items():
            if owner_id == interaction.user.id:
                user_channel = interaction.guild.get_channel(channel_id)
                break
        
        if not user_channel:
            await interaction.response.send_message(
                "❌ 你目前沒有臨時語音頻道！",
                ephemeral=True
            )
            return
        
        await user_channel.edit(user_limit=人數)
        
        limit_text = "無限制" if 人數 == 0 else f"{人數} 人"
        await interaction.response.send_message(
            f"✅ 已將頻道人數限制設為：{limit_text}"
        )
    
    @voice_group.command(name="重命名", description="重命名你的臨時頻道")
    @app_commands.describe(新名稱="新的頻道名稱")
    async def rename(self, interaction: discord.Interaction, 新名稱: str):
        """重命名臨時頻道"""
        if len(新名稱) > 100:
            await interaction.response.send_message(
                "❌ 頻道名稱不能超過 100 個字符！",
                ephemeral=True
            )
            return
        
        # 找到用戶的臨時頻道
        user_channel = None
        for channel_id, owner_id in self.temp_channels.items():
            if owner_id == interaction.user.id:
                user_channel = interaction.guild.get_channel(channel_id)
                break
        
        if not user_channel:
            await interaction.response.send_message(
                "❌ 你目前沒有臨時語音頻道！",
                ephemeral=True
            )
            return
        
        old_name = user_channel.name
        await user_channel.edit(name=新名稱)
        
        await interaction.response.send_message(
            f"✅ 頻道已重命名：`{old_name}` → `{新名稱}`"
        )
    
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """處理語音狀態變化"""
        guild_id = member.guild.id
        config = self.load_config(guild_id)
        
        # 如果系統未啟用，直接返回
        if not config['enabled']:
            return
        
        # 用戶加入觸發頻道 - 創建臨時頻道
        if after.channel and after.channel.id == config['trigger_channel_id']:
            # 獲取分類
            category = None
            if config['category_id']:
                category = member.guild.get_channel(config['category_id'])
            
            # 創建頻道名稱
            channel_name = config['channel_name_format'].replace('{username}', member.display_name)
            
            # 創建臨時頻道
            temp_channel = await member.guild.create_voice_channel(
                name=channel_name,
                category=category,
                bitrate=config['default_bitrate'],
                user_limit=config['user_limit']
            )
            
            # 記錄臨時頻道
            self.temp_channels[temp_channel.id] = member.id
            
            # 移動用戶到新頻道
            try:
                await member.move_to(temp_channel)
            except:
                # 如果移動失敗，刪除頻道
                await temp_channel.delete()
                del self.temp_channels[temp_channel.id]
        
        # 用戶離開頻道 - 檢查是否需要刪除臨時頻道
        if before.channel and before.channel.id in self.temp_channels:
            # 如果頻道沒有人了，刪除它
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    del self.temp_channels[before.channel.id]
                except:
                    pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(TempVoice(bot))
