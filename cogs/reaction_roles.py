import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class ReactionRoles(commands.Cog):
    """反應角色系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.reaction_roles = {}
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_data_file(self, guild_id: str):
        """獲取伺服器數據檔案路徑"""
        guild_dir = os.path.join(self.data_dir, guild_id)
        os.makedirs(guild_dir, exist_ok=True)
        return os.path.join(guild_dir, "reaction_roles.json")
    
    def load_data(self, guild_id: str):
        """載入反應角色數據"""
        data_file = self.get_data_file(guild_id)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_data(self, guild_id: str):
        """保存反應角色數據"""
        data_file = self.get_data_file(guild_id)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.reaction_roles.get(guild_id, {}), f, indent=2, ensure_ascii=False)
    
    def get_reaction_roles(self, guild_id: str):
        """獲取反應角色數據"""
        if guild_id not in self.reaction_roles:
            self.reaction_roles[guild_id] = self.load_data(guild_id)
        return self.reaction_roles[guild_id]
    
    # 創建指令組
    rr_group = app_commands.Group(name="反應角色", description="反應角色系統")
    
    @rr_group.command(name="創建", description="創建反應角色訊息")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        channel="選擇發送訊息的頻道",
        title="訊息標題",
        description="訊息描述"
    )
    async def create(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        title: str,
        description: str = "點擊下方表情符號獲取對應身分組"
    ):
        """創建反應角色訊息"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="點擊表情符號自動獲取/移除身分組")
        
        message = await channel.send(embed=embed)
        
        await interaction.response.send_message(
            f"✅ 反應角色訊息已在 {channel.mention} 創建\n訊息 ID: `{message.id}`\n請使用 `/反應角色 添加` 指令添加角色",
            ephemeral=True
        )
    
    @rr_group.command(name="添加", description="為訊息添加反應角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        message_id="訊息 ID",
        emoji="表情符號",
        role="要綁定的身分組"
    )
    async def add(
        self, 
        interaction: discord.Interaction, 
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """添加反應角色"""
        guild_id = str(interaction.guild.id)
        data = self.get_reaction_roles(guild_id)
        
        # 嘗試獲取訊息並添加反應
        try:
            # 在所有文字頻道中搜索訊息
            message = None
            for channel in interaction.guild.text_channels:
                try:
                    message = await channel.fetch_message(int(message_id))
                    if message:
                        break
                except:
                    continue
            
            if not message:
                await interaction.response.send_message("❌ 找不到指定的訊息", ephemeral=True)
                return
            
            # 添加反應
            await message.add_reaction(emoji)
            
            # 保存數據
            if message_id not in data:
                data[message_id] = {
                    "channel_id": message.channel.id,
                    "roles": {}
                }
            
            data[message_id]["roles"][emoji] = role.id
            self.save_data(guild_id)
            
            await interaction.response.send_message(
                f"✅ 已添加反應角色：{emoji} → {role.mention}",
                ephemeral=True
            )
        
        except discord.HTTPException:
            await interaction.response.send_message("❌ 無法添加表情符號，請確保表情符號有效", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 發生錯誤：{str(e)}", ephemeral=True)
    
    @rr_group.command(name="移除", description="移除反應角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        message_id="訊息 ID",
        emoji="要移除的表情符號"
    )
    async def remove(
        self, 
        interaction: discord.Interaction, 
        message_id: str,
        emoji: str
    ):
        """移除反應角色"""
        guild_id = str(interaction.guild.id)
        data = self.get_reaction_roles(guild_id)
        
        if message_id not in data or emoji not in data[message_id]["roles"]:
            await interaction.response.send_message("❌ 找不到指定的反應角色", ephemeral=True)
            return
        
        del data[message_id]["roles"][emoji]
        
        # 如果訊息沒有任何角色了，刪除整個訊息記錄
        if not data[message_id]["roles"]:
            del data[message_id]
        
        self.save_data(guild_id)
        
        await interaction.response.send_message(
            f"✅ 已移除反應角色：{emoji}",
            ephemeral=True
        )
    
    @rr_group.command(name="列表", description="查看所有反應角色訊息")
    async def list(self, interaction: discord.Interaction):
        """列出所有反應角色"""
        guild_id = str(interaction.guild.id)
        data = self.get_reaction_roles(guild_id)
        
        if not data:
            await interaction.response.send_message("❌ 目前沒有任何反應角色訊息", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 反應角色列表",
            color=discord.Color.blue()
        )
        
        for message_id, info in data.items():
            roles_text = "\n".join([
                f"{emoji} → <@&{role_id}>"
                for emoji, role_id in info["roles"].items()
            ])
            
            embed.add_field(
                name=f"訊息 ID: {message_id}",
                value=f"頻道: <#{info['channel_id']}>\n{roles_text}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """處理反應添加"""
        # 忽略機器人自己的反應
        if payload.user_id == self.bot.user.id:
            return
        
        guild_id = str(payload.guild_id)
        message_id = str(payload.message_id)
        data = self.get_reaction_roles(guild_id)
        
        # 檢查是否是反應角色訊息
        if message_id not in data:
            return
        
        emoji = str(payload.emoji)
        if emoji not in data[message_id]["roles"]:
            return
        
        # 添加角色
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        role = guild.get_role(data[message_id]["roles"][emoji])
        
        if member and role:
            try:
                await member.add_roles(role)
            except:
                pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """處理反應移除"""
        guild_id = str(payload.guild_id)
        message_id = str(payload.message_id)
        data = self.get_reaction_roles(guild_id)
        
        # 檢查是否是反應角色訊息
        if message_id not in data:
            return
        
        emoji = str(payload.emoji)
        if emoji not in data[message_id]["roles"]:
            return
        
        # 移除角色
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        role = guild.get_role(data[message_id]["roles"][emoji])
        
        if member and role:
            try:
                await member.remove_roles(role)
            except:
                pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')
        # 載入所有伺服器的數據
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            self.reaction_roles[guild_id] = self.load_data(guild_id)
        print(f'👆 已載入 {len(self.reaction_roles)} 個伺服器的反應角色數據')

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
