import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class ServerInfo(commands.Cog):
    """伺服器資訊和統計功能"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # 創建指令組
    info_group = app_commands.Group(name="伺服器", description="伺服器資訊和統計")
    
    @info_group.command(name="資訊", description="查看伺服器詳細資訊")
    async def serverinfo(self, interaction: discord.Interaction):
        """顯示伺服器資訊"""
        guild = interaction.guild
        
        # 計算成員統計
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        
        # 線上狀態統計
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # 頻道統計
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed = discord.Embed(
            title=f"📊 {guild.name} 伺服器資訊",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(
            name="👑 伺服器所有者",
            value=guild.owner.mention if guild.owner else "未知",
            inline=True
        )
        embed.add_field(
            name="🆔 伺服器ID",
            value=f"`{guild.id}`",
            inline=True
        )
        embed.add_field(
            name="📅 創建時間",
            value=discord.utils.format_dt(guild.created_at, style='R'),
            inline=True
        )
        
        embed.add_field(
            name=f"👥 成員 ({total_members})",
            value=f"👤 人類: {humans}\n🤖 機器人: {bots}",
            inline=True
        )
        embed.add_field(
            name="📡 線上狀態",
            value=f"🟢 線上: {online}\n🟡 閒置: {idle}\n🔴 勿擾: {dnd}\n⚫ 離線: {offline}",
            inline=True
        )
        embed.add_field(
            name=f"📁 頻道 ({text_channels + voice_channels})",
            value=f"💬 文字: {text_channels}\n🔊 語音: {voice_channels}\n📂 分類: {categories}",
            inline=True
        )
        
        embed.add_field(
            name="😊 表情符號",
            value=f"{len(guild.emojis)} 個",
            inline=True
        )
        embed.add_field(
            name="🎭 角色",
            value=f"{len(guild.roles)} 個",
            inline=True
        )
        embed.add_field(
            name="🚀 加成等級",
            value=f"等級 {guild.premium_tier} ({guild.premium_subscription_count} 加成)",
            inline=True
        )
        
        embed.set_footer(text=f"伺服器驗證等級: {guild.verification_level}")
        
        await interaction.response.send_message(embed=embed)
    
    @info_group.command(name="圖標", description="查看伺服器圖標")
    async def servericon(self, interaction: discord.Interaction):
        """顯示伺服器圖標"""
        guild = interaction.guild
        
        if not guild.icon:
            await interaction.response.send_message("❌ 該伺服器沒有設定圖標", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🖼️ {guild.name} 的圖標",
            color=discord.Color.blue()
        )
        embed.set_image(url=guild.icon.url)
        embed.add_field(name="下載連結", value=f"[點擊查看原圖]({guild.icon.url})")
        
        await interaction.response.send_message(embed=embed)
    
    @info_group.command(name="成員統計", description="查看成員詳細統計")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def memberstats(self, interaction: discord.Interaction):
        """顯示成員統計資訊"""
        guild = interaction.guild
        
        # 成員統計
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        
        # 線上狀態
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # 角色統計 - 前5個最多人的角色
        role_counts = {}
        for member in guild.members:
            for role in member.roles:
                if role.name != "@everyone":
                    role_counts[role] = role_counts.get(role, 0) + 1
        
        top_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        embed = discord.Embed(
            title="📊 成員統計",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="總覽",
            value=f"總成員: **{total}**\n👤 人類: **{humans}**\n🤖 機器人: **{bots}**",
            inline=False
        )
        
        # 創建線上狀態進度條
        def create_bar(value, total, length=10):
            filled = int((value / total) * length)
            bar = "█" * filled + "░" * (length - filled)
            percentage = (value / total) * 100
            return f"{bar} {percentage:.1f}%"
        
        embed.add_field(
            name="線上狀態分佈",
            value=f"🟢 線上: {online}\n{create_bar(online, total)}\n\n"
                  f"🟡 閒置: {idle}\n{create_bar(idle, total)}\n\n"
                  f"🔴 勿擾: {dnd}\n{create_bar(dnd, total)}\n\n"
                  f"⚫ 離線: {offline}\n{create_bar(offline, total)}",
            inline=False
        )
        
        if top_roles:
            role_text = "\n".join([f"{role.mention}: **{count}** 人" for role, count in top_roles])
            embed.add_field(
                name="🎭 人數最多的角色 (Top 5)",
                value=role_text,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @info_group.command(name="角色列表", description="查看伺服器所有角色")
    async def rolelist(self, interaction: discord.Interaction):
        """顯示所有角色"""
        guild = interaction.guild
        roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
        
        # 移除@everyone
        roles = [r for r in roles if r.name != "@everyone"]
        
        embed = discord.Embed(
            title=f"🎭 {guild.name} 的角色列表",
            description=f"共有 **{len(roles)}** 個角色",
            color=discord.Color.purple()
        )
        
        # 分頁顯示，每頁20個角色
        role_chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]
        
        for chunk in role_chunks[:1]:  # 只顯示第一頁
            role_text = "\n".join([
                f"{role.mention} - {len(role.members)} 人" 
                for role in chunk
            ])
            embed.add_field(name="角色", value=role_text or "無", inline=False)
        
        if len(role_chunks) > 1:
            embed.set_footer(text=f"第 1/{len(role_chunks)} 頁 | 使用指令查看更多")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
