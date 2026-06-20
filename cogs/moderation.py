import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class Moderation(commands.Cog):
    """管理指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def get_data_path(self, guild_id):
        """獲取數據路徑"""
        path = f'./data/{guild_id}'
        os.makedirs(path, exist_ok=True)
        return path
    
    def load_warnings(self, guild_id):
        """載入警告數據"""
        file_path = f'{self.get_data_path(guild_id)}/warnings.json'
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_warnings(self, guild_id, data):
        """保存警告數據"""
        file_path = f'{self.get_data_path(guild_id)}/warnings.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    async def check_auto_punishment(self, interaction: discord.Interaction, member: discord.Member, warn_count: int):
        """檢查並執行自動處罰"""
        if warn_count >= 5:
            try:
                await member.ban(reason=f"警告次數達到 {warn_count} 次（自動封禁）")
                embed = discord.Embed(
                    title="🔨 自動封禁",
                    description=f"{member.mention} 因累積 {warn_count} 次警告已被自動封禁",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
            except:
                pass
        elif warn_count >= 3:
            try:
                await member.kick(reason=f"警告次數達到 {warn_count} 次（自動踢出）")
                embed = discord.Embed(
                    title="⚠️ 自動踢出",
                    description=f"{member.mention} 因累積 {warn_count} 次警告已被自動踢出",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
            except:
                pass
    
    # 創建指令組
    mod_group = app_commands.Group(name="管理", description="管理功能指令")
    
    @mod_group.command(name="踢出用戶", description="踢出用戶")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無理由"):
        """踢出成員"""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="✅ 成員已踢出",
                description=f"{member.mention} 已被踢出",
                color=discord.Color.orange()
            )
            embed.add_field(name="理由", value=reason)
            embed.set_footer(text=f"操作者: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 我沒有權限踢出此用戶", ephemeral=True)
    
    @mod_group.command(name="封鎖用戶", description="封鎖用戶")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無理由"):
        """封鎖成員"""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 成員已封鎖",
                description=f"{member.mention} 已被封鎖",
                color=discord.Color.red()
            )
            embed.add_field(name="理由", value=reason)
            embed.set_footer(text=f"操作者: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 我沒有權限封鎖此用戶", ephemeral=True)
    
    @mod_group.command(name="清除訊息", description="清除訊息")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        """清除指定數量的訊息"""
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ 請輸入1-100之間的數字", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ 已刪除 {len(deleted)} 則訊息", ephemeral=True)
    
    @mod_group.command(name="警告", description="警告用戶")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無理由"):
        """警告用戶"""
        if member == interaction.user:
            await interaction.response.send_message("❌ 你不能警告自己", ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message("❌ 不能警告機器人", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        warnings = self.load_warnings(interaction.guild_id)
        user_id = str(member.id)
        
        if user_id not in warnings:
            warnings[user_id] = []
        
        warning_data = {
            "reason": reason,
            "moderator": str(interaction.user.id),
            "moderator_name": str(interaction.user),
            "timestamp": datetime.now().isoformat()
        }
        
        warnings[user_id].append(warning_data)
        self.save_warnings(interaction.guild_id, warnings)
        
        warn_count = len(warnings[user_id])
        
        embed = discord.Embed(
            title="⚠️ 用戶已被警告",
            description=f"{member.mention} 已收到警告",
            color=discord.Color.yellow()
        )
        embed.add_field(name="理由", value=reason, inline=False)
        embed.add_field(name="警告次數", value=f"{warn_count} 次", inline=True)
        embed.add_field(name="操作者", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"• 3次警告 = 自動踢出\n• 5次警告 = 自動封禁")
        
        await interaction.followup.send(embed=embed)
        
        # 檢查自動處罰
        await self.check_auto_punishment(interaction, member, warn_count)
        
        # 嘗試私信用戶
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ 你在 {interaction.guild.name} 收到了警告",
                description=f"**理由：** {reason}",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="警告次數", value=f"{warn_count} 次")
            dm_embed.add_field(name="操作者", value=str(interaction.user))
            dm_embed.set_footer(text="請遵守伺服器規則")
            await member.send(embed=dm_embed)
        except:
            pass
    
    @mod_group.command(name="取消警告", description="取消用戶的最近一次警告")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unwarn(self, interaction: discord.Interaction, member: discord.Member):
        """取消用戶的最近一次警告"""
        warnings = self.load_warnings(interaction.guild_id)
        user_id = str(member.id)
        
        if user_id not in warnings or len(warnings[user_id]) == 0:
            await interaction.response.send_message(f"❌ {member.mention} 沒有警告記錄", ephemeral=True)
            return
        
        removed_warning = warnings[user_id].pop()
        
        if len(warnings[user_id]) == 0:
            del warnings[user_id]
        
        self.save_warnings(interaction.guild_id, warnings)
        
        embed = discord.Embed(
            title="✅ 警告已取消",
            description=f"已取消 {member.mention} 的最近一次警告",
            color=discord.Color.green()
        )
        embed.add_field(name="被取消的警告理由", value=removed_warning['reason'])
        embed.add_field(name="剩餘警告", value=f"{len(warnings.get(user_id, []))} 次")
        embed.set_footer(text=f"操作者: {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @mod_group.command(name="警告記錄", description="查看用戶的警告記錄")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member = None):
        """查看警告記錄"""
        target = member or interaction.user
        warnings = self.load_warnings(interaction.guild_id)
        user_id = str(target.id)
        
        if user_id not in warnings or len(warnings[user_id]) == 0:
            await interaction.response.send_message(f"✅ {target.mention} 沒有警告記錄", ephemeral=True)
            return
        
        user_warnings = warnings[user_id]
        
        embed = discord.Embed(
            title=f"⚠️ {target.display_name} 的警告記錄",
            description=f"總計：{len(user_warnings)} 次警告",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        for idx, warn in enumerate(user_warnings[-10:], 1):  # 只顯示最近10次
            moderator = warn.get('moderator_name', '未知')
            timestamp = warn.get('timestamp', '未知時間')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = timestamp
            
            embed.add_field(
                name=f"警告 #{idx}",
                value=f"**理由：** {warn['reason']}\n**操作者：** {moderator}\n**時間：** {time_str}",
                inline=False
            )
        
        if len(user_warnings) > 10:
            embed.set_footer(text=f"僅顯示最近10次警告，共有 {len(user_warnings)} 次")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @mod_group.command(name="清除警告", description="清除用戶的所有警告")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        """清除用戶的所有警告"""
        warnings = self.load_warnings(interaction.guild_id)
        user_id = str(member.id)
        
        if user_id not in warnings or len(warnings[user_id]) == 0:
            await interaction.response.send_message(f"❌ {member.mention} 沒有警告記錄", ephemeral=True)
            return
        
        warn_count = len(warnings[user_id])
        del warnings[user_id]
        self.save_warnings(interaction.guild_id, warnings)
        
        embed = discord.Embed(
            title="🗑️ 警告已清除",
            description=f"已清除 {member.mention} 的所有警告記錄",
            color=discord.Color.green()
        )
        embed.add_field(name="清除數量", value=f"{warn_count} 次")
        embed.set_footer(text=f"操作者: {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
