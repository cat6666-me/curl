import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

class PostInfoButton(discord.ui.Button):
    """貼文資訊按鈕（僅管理員可見）"""
    
    def __init__(self, cog):
        super().__init__(
            label="貼文資訊",
            style=discord.ButtonStyle.secondary,
            emoji="ℹ️",
            custom_id="anonymous_post_info"
        )
        self.cog = cog
    
    async def callback(self, interaction: discord.Interaction):
        # 檢查是否為開發者
        load_dotenv()
        dev_ids = os.getenv('DEV_ID', '')
        dev_id_list = [int(id.strip()) for id in dev_ids.split(',') if id.strip()]
        
        if interaction.user.id not in dev_id_list:
            await interaction.response.send_message(
                "❌ 只有機器人開發者才能查看貼文資訊",
                ephemeral=True
            )
            return
        
        # 從數據中查找貼文資訊
        guild_id = str(interaction.guild.id)
        message_id = str(interaction.message.id)
        data = self.cog.load_data(guild_id)
        
        post_data = data.get('posts', {}).get(message_id)
        if not post_data:
            await interaction.response.send_message(
                "❌ 找不到此貼文的資訊",
                ephemeral=True
            )
            return
        
        author_id = int(post_data['author_id'])
        author_name = post_data['author_name']
        timestamp = post_data['timestamp']
        
        embed = discord.Embed(
            title="📋 匿名貼文資訊",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(timestamp)
        )
        
        embed.add_field(
            name="原始發送者",
            value=f"<@{author_id}> ({author_name})",
            inline=False
        )
        
        embed.add_field(
            name="用戶 ID",
            value=f"`{author_id}`",
            inline=True
        )
        
        embed.add_field(
            name="發送時間",
            value=f"<t:{int(datetime.fromisoformat(timestamp).timestamp())}:F>",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AnonymousView(discord.ui.View):
    """匿名貼文視圖"""
    
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(PostInfoButton(cog))

class Anonymous(commands.Cog):
    """匿名發言系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = bot.storage
        self.anonymous_posts = {}  # {guild_id: {message_id: {author_id, author_name, timestamp}}}
    
    def load_data(self, guild_id):
        """載入匿名貼文數據"""
        return self.storage.load_guild_data(guild_id, 'anonymous', default={
            'enabled_channels': [],  # 允許匿名發言的頻道
            'posts': {}  # 貼文記錄
        })
    
    def save_data(self, guild_id, data):
        """保存匿名貼文數據"""
        self.storage.save_guild_data(guild_id, 'anonymous', data)
    
    # 創建匿名指令組
    anonymous_group = app_commands.Group(name="匿名", description="匿名發言系統")
    
    @anonymous_group.command(name="發言", description="發送匿名訊息")
    @app_commands.describe(
        訊息="要匿名發送的訊息內容",
        頻道="發送到的頻道（不指定則發送到當前頻道）"
    )
    async def send_anonymous(
        self, 
        interaction: discord.Interaction, 
        訊息: str,
        頻道: discord.TextChannel = None
    ):
        """發送匿名訊息"""
        guild_id = str(interaction.guild.id)
        data = self.load_data(guild_id)
        
        target_channel = 頻道 or interaction.channel
        
        # 檢查頻道是否允許匿名發言（如果設置了限制）
        if data.get('enabled_channels') and str(target_channel.id) not in data['enabled_channels']:
            await interaction.response.send_message(
                f"❌ 此頻道不允許匿名發言",
                ephemeral=True
            )
            return
        
        # 檢查訊息長度
        if len(訊息) > 2000:
            await interaction.response.send_message(
                "❌ 訊息長度不能超過 2000 個字元",
                ephemeral=True
            )
            return
        
        # 創建匿名貼文嵌入
        embed = discord.Embed(
            title="💬 匿名貼文",
            description=訊息,
            color=discord.Color.greyple(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="匿名發言系統")
        
        # 創建視圖
        timestamp = datetime.now().isoformat()
        view = AnonymousView(self)
        
        try:
            # 發送匿名訊息
            message = await target_channel.send(embed=embed, view=view)
            
            # 保存貼文資訊
            if 'posts' not in data:
                data['posts'] = {}
            
            data['posts'][str(message.id)] = {
                'author_id': str(interaction.user.id),
                'author_name': str(interaction.user),
                'timestamp': timestamp,
                'channel_id': str(target_channel.id),
                'content': 訊息
            }
            
            self.save_data(guild_id, data)
            
            # 給用戶確認
            confirm_embed = discord.Embed(
                title="✅ 匿名訊息已發送",
                description=f"您的匿名訊息已發送至 {target_channel.mention}",
                color=discord.Color.green()
            )
            confirm_embed.add_field(
                name="內容預覽",
                value=訊息[:100] + ("..." if len(訊息) > 100 else ""),
                inline=False
            )
            
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ 機器人沒有權限在該頻道發送訊息",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 發送失敗: {str(e)}",
                ephemeral=True
            )
    
    @anonymous_group.command(name="設定頻道", description="設定允許匿名發言的頻道")
    @app_commands.describe(頻道="要設定的頻道")
    @app_commands.default_permissions(manage_guild=True)
    async def set_channel(
        self, 
        interaction: discord.Interaction, 
        頻道: discord.TextChannel
    ):
        """設定匿名發言頻道（管理員）"""
        guild_id = str(interaction.guild.id)
        data = self.load_data(guild_id)
        
        if 'enabled_channels' not in data:
            data['enabled_channels'] = []
        
        channel_id = str(頻道.id)
        
        if channel_id in data['enabled_channels']:
            await interaction.response.send_message(
                f"ℹ️ {頻道.mention} 已經允許匿名發言",
                ephemeral=True
            )
            return
        
        data['enabled_channels'].append(channel_id)
        self.save_data(guild_id, data)
        
        await interaction.response.send_message(
            f"✅ 已允許在 {頻道.mention} 使用匿名發言",
            ephemeral=True
        )
    
    @anonymous_group.command(name="移除頻道", description="移除匿名發言頻道")
    @app_commands.describe(頻道="要移除的頻道")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_channel(
        self, 
        interaction: discord.Interaction, 
        頻道: discord.TextChannel
    ):
        """移除匿名發言頻道（管理員）"""
        guild_id = str(interaction.guild.id)
        data = self.load_data(guild_id)
        
        channel_id = str(頻道.id)
        
        if channel_id not in data.get('enabled_channels', []):
            await interaction.response.send_message(
                f"ℹ️ {頻道.mention} 未設定為匿名發言頻道",
                ephemeral=True
            )
            return
        
        data['enabled_channels'].remove(channel_id)
        self.save_data(guild_id, data)
        
        await interaction.response.send_message(
            f"✅ 已移除 {頻道.mention} 的匿名發言權限",
            ephemeral=True
        )
    
    @anonymous_group.command(name="允許全部", description="允許所有頻道使用匿名發言")
    @app_commands.default_permissions(manage_guild=True)
    async def allow_all(self, interaction: discord.Interaction):
        """允許所有頻道使用匿名發言（管理員）"""
        guild_id = str(interaction.guild.id)
        data = self.load_data(guild_id)
        
        data['enabled_channels'] = []  # 空列表表示允許所有頻道
        self.save_data(guild_id, data)
        
        await interaction.response.send_message(
            "✅ 已允許在所有頻道使用匿名發言",
            ephemeral=True
        )
    
    @anonymous_group.command(name="列表", description="查看匿名發言設定")
    @app_commands.default_permissions(manage_guild=True)
    async def list_settings(self, interaction: discord.Interaction):
        """查看匿名發言設定（管理員）"""
        guild_id = str(interaction.guild.id)
        data = self.load_data(guild_id)
        
        embed = discord.Embed(
            title="🔍 匿名發言設定",
            color=discord.Color.blue()
        )
        
        enabled_channels = data.get('enabled_channels', [])
        
        if not enabled_channels:
            embed.add_field(
                name="允許的頻道",
                value="✅ 所有頻道",
                inline=False
            )
        else:
            channels_text = "\n".join([f"<#{ch_id}>" for ch_id in enabled_channels])
            embed.add_field(
                name=f"允許的頻道 ({len(enabled_channels)})",
                value=channels_text or "無",
                inline=False
            )
        
        total_posts = len(data.get('posts', {}))
        embed.add_field(
            name="匿名貼文總數",
            value=f"`{total_posts}` 則",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """機器人準備就緒時註冊持久化視圖"""
        print(f'📦 {self.__class__.__name__} cog已載入')
        
        # 載入所有伺服器的數據並註冊視圖
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            data = self.load_data(guild_id)
            
            # 為每個保存的貼文註冊視圖
            for message_id, post_data in data.get('posts', {}).items():
                view = AnonymousView(self)
                self.bot.add_view(view, message_id=int(message_id))

async def setup(bot):
    await bot.add_cog(Anonymous(bot))
