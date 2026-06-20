import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv

class Developer(commands.Cog):
    """開發者專用指令"""
    
    def __init__(self, bot):
        self.bot = bot
        # 从 .env 读取开发者 ID 列表
        load_dotenv()
        dev_ids = os.getenv('DEV_ID', '')
        self.dev_ids = [int(id.strip()) for id in dev_ids.split(',') if id.strip()]
    
    def is_developer(self, user_id: int) -> bool:
        """检查用户是否为开发者"""
        return user_id in self.dev_ids
    
    # 创建开发者指令组
    dev_group = app_commands.Group(name="開發", description="開發者專用指令")
    
    @dev_group.command(name="重啟", description="重新啟動機器人")
    async def restart(self, interaction: discord.Interaction):
        """重启机器人（仅开发者）"""
        # 检查权限
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🔄 重新啟動機器人",
            description="機器人正在重新啟動...\n請稍候片刻",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"執行者: {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)
        
        print('\n' + '═' * 62)
        print(f'🔄 開發者 {interaction.user.name} ({interaction.user.id}) 觸發重啟')
        print('═' * 62 + '\n')
        
        # 关闭机器人并重启
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    @dev_group.command(name="資訊", description="顯示開發者資訊")
    async def dev_info(self, interaction: discord.Interaction):
        """显示开发者信息"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="👨‍💻 開發者資訊",
            color=discord.Color.blue()
        )
        
        # 显示授权的开发者
        dev_list = []
        for dev_id in self.dev_ids:
            try:
                user = await self.bot.fetch_user(dev_id)
                dev_list.append(f"• {user.name} (`{dev_id}`)")
            except:
                dev_list.append(f"• Unknown User (`{dev_id}`)")
        
        embed.add_field(
            name="授權開發者",
            value="\n".join(dev_list) if dev_list else "無",
            inline=False
        )
        
        # 系统信息
        embed.add_field(
            name="Python 版本",
            value=f"`{sys.version.split()[0]}`",
            inline=True
        )
        
        embed.add_field(
            name="Discord.py 版本",
            value=f"`{discord.__version__}`",
            inline=True
        )
        
        embed.add_field(
            name="伺服器數量",
            value=f"`{len(self.bot.guilds)}`",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @dev_group.command(name="執行", description="執行 Python 代碼")
    @app_commands.describe(代碼="要執行的 Python 代碼")
    async def eval_code(self, interaction: discord.Interaction, 代碼: str):
        """执行 Python 代码（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 执行代码
            result = eval(代碼)
            
            embed = discord.Embed(
                title="✅ 執行成功",
                color=discord.Color.green()
            )
            embed.add_field(name="代碼", value=f"```python\n{代碼}\n```", inline=False)
            embed.add_field(name="結果", value=f"```python\n{result}\n```", inline=False)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ 執行錯誤",
                color=discord.Color.red()
            )
            embed.add_field(name="代碼", value=f"```python\n{代碼}\n```", inline=False)
            embed.add_field(name="錯誤", value=f"```python\n{type(e).__name__}: {str(e)}\n```", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @dev_group.command(name="同步", description="同步斜線命令")
    async def sync_commands(self, interaction: discord.Interaction):
        """同步斜线命令到 Discord（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            synced = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="✅ 命令同步成功",
                description=f"已同步 **{len(synced)}** 個斜線命令",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"執行者: {interaction.user.name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            print(f'✅ 開發者 {interaction.user.name} 同步了 {len(synced)} 個命令')
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ 同步失敗",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @dev_group.command(name="伺服器列表", description="查看所有伺服器")
    async def list_guilds(self, interaction: discord.Interaction):
        """列出所有服务器（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        guilds = self.bot.guilds
        
        embed = discord.Embed(
            title=f"📊 伺服器列表 ({len(guilds)})",
            color=discord.Color.blue()
        )
        
        # 按成员数排序
        sorted_guilds = sorted(guilds, key=lambda g: g.member_count, reverse=True)
        
        guild_list = []
        for i, guild in enumerate(sorted_guilds[:25], 1):  # 最多显示25个
            guild_list.append(
                f"{i}. **{guild.name}**\n"
                f"   └ ID: `{guild.id}` | 成員: `{guild.member_count}`"
            )
        
        embed.description = "\n".join(guild_list)
        
        if len(guilds) > 25:
            embed.set_footer(text=f"僅顯示前 25 個伺服器，共 {len(guilds)} 個")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @dev_group.command(name="更新", description="檢查並安裝更新")
    async def check_update(self, interaction: discord.Interaction):
        """检查更新（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # 获取 Updater cog
        updater = self.bot.get_cog('Updater')
        if not updater:
            embed = discord.Embed(
                title="❌ 錯誤",
                description="無法找到更新模組",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # 检查版本
        local_version = updater.get_local_version()
        remote_version = await updater.get_remote_version()
        
        if not local_version or not remote_version:
            embed = discord.Embed(
                title="❌ 無法檢查更新",
                description="無法讀取版本信息",
                color=discord.Color.red()
            )
            embed.add_field(name="本地版本", value=local_version or "讀取失敗", inline=True)
            embed.add_field(name="遠程版本", value=remote_version or "讀取失敗", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # 比较版本
        if local_version == remote_version:
            embed = discord.Embed(
                title="✅ 已是最新版本",
                description=f"當前版本：`{local_version}`",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"執行者: {interaction.user.name}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # 发现新版本
        embed = discord.Embed(
            title="🎉 發現新版本",
            description=f"正在從 **{local_version}** 更新至 **{remote_version}**",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # 执行更新
        print(f'\n🔄 開發者 {interaction.user.name} ({interaction.user.id}) 觸發手動更新')
        await updater.check_and_update()
    
    @dev_group.command(name="全局封銮", description="在所有伺服器中封銮用戶")
    @app_commands.describe(
        user_id="要封銮的用戶ID",
        reason="封銮原因"
    )
    async def global_ban(self, interaction: discord.Interaction, user_id: str, reason: str = "開發者全局封銮"):
        """全局封銮用戶（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            uid = int(user_id)
            user = await self.bot.fetch_user(uid)
        except ValueError:
            await interaction.followup.send(
                "❌ 無效的用戶ID，請輸入數字ID",
                ephemeral=True
            )
            return
        except discord.NotFound:
            await interaction.followup.send(
                "❌ 找不到該用戶",
                ephemeral=True
            )
            return
        
        success_count = 0
        fail_count = 0
        banned_guilds = []
        
        for guild in self.bot.guilds:
            try:
                # 檢查用戶是否在伺服器中
                member = guild.get_member(uid)
                if member or True:  # 即使不在伺服器也嘗試封銮
                    await guild.ban(
                        user,
                        reason=f"全局封銮 by {interaction.user} | {reason}",
                        delete_message_seconds=0
                    )
                    success_count += 1
                    banned_guilds.append(guild.name)
            except discord.Forbidden:
                fail_count += 1
            except discord.HTTPException:
                fail_count += 1
            except Exception:
                fail_count += 1
        
        embed = discord.Embed(
            title="🚫 全局封銮完成",
            color=discord.Color.red()
        )
        embed.add_field(name="目標用戶", value=f"{user.name} (`{user.id}`)", inline=False)
        embed.add_field(name="封銮原因", value=reason, inline=False)
        embed.add_field(name="成功", value=f"`{success_count}` 個伺服器", inline=True)
        embed.add_field(name="失敗", value=f"`{fail_count}` 個伺服器", inline=True)
        embed.add_field(name="總計", value=f"`{len(self.bot.guilds)}` 個伺服器", inline=True)
        
        if success_count > 0:
            # 只顯示前10個伺服器
            guilds_preview = "\n".join(banned_guilds[:10])
            if len(banned_guilds) > 10:
                guilds_preview += f"\n... 還有 {len(banned_guilds) - 10} 個伺服器"
            embed.add_field(name="已封銮的伺服器", value=guilds_preview, inline=False)
        
        embed.set_footer(text=f"執行者: {interaction.user.name}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        print(f'\n🚫 開發者 {interaction.user.name} 對 {user.name}({user.id}) 執行全局封銮')
        print(f'   原因: {reason}')
        print(f'   結果: {success_count} 成功 / {fail_count} 失敗')
    
    @dev_group.command(name="全局解封", description="在所有伺服器中解封用戶")
    @app_commands.describe(user_id="要解封的用戶ID")
    async def global_unban(self, interaction: discord.Interaction, user_id: str):
        """全局解封用戶（仅开发者）"""
        if not self.is_developer(interaction.user.id):
            await interaction.response.send_message(
                "❌ 此命令僅限開發者使用！", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            uid = int(user_id)
            user = await self.bot.fetch_user(uid)
        except ValueError:
            await interaction.followup.send(
                "❌ 無效的用戶ID，請輸入數字ID",
                ephemeral=True
            )
            return
        except discord.NotFound:
            await interaction.followup.send(
                "❌ 找不到該用戶",
                ephemeral=True
            )
            return
        
        success_count = 0
        fail_count = 0
        unbanned_guilds = []
        
        for guild in self.bot.guilds:
            try:
                await guild.unban(
                    user,
                    reason=f"全局解封 by {interaction.user}"
                )
                success_count += 1
                unbanned_guilds.append(guild.name)
            except discord.NotFound:
                # 用戶未被封銮
                fail_count += 1
            except discord.Forbidden:
                fail_count += 1
            except discord.HTTPException:
                fail_count += 1
            except Exception:
                fail_count += 1
        
        embed = discord.Embed(
            title="✅ 全局解封完成",
            color=discord.Color.green()
        )
        embed.add_field(name="目標用戶", value=f"{user.name} (`{user.id}`)", inline=False)
        embed.add_field(name="成功", value=f"`{success_count}` 個伺服器", inline=True)
        embed.add_field(name="失敗/未封銮", value=f"`{fail_count}` 個伺服器", inline=True)
        embed.add_field(name="總計", value=f"`{len(self.bot.guilds)}` 個伺服器", inline=True)
        
        if success_count > 0:
            # 只顯示前10個伺服器
            guilds_preview = "\n".join(unbanned_guilds[:10])
            if len(unbanned_guilds) > 10:
                guilds_preview += f"\n... 還有 {len(unbanned_guilds) - 10} 個伺服器"
            embed.add_field(name="已解封的伺服器", value=guilds_preview, inline=False)
        
        embed.set_footer(text=f"執行者: {interaction.user.name}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        print(f'\n✅ 開發者 {interaction.user.name} 對 {user.name}({user.id}) 執行全局解封')
        print(f'   結果: {success_count} 成功 / {fail_count} 失敗')
    
    @commands.Cog.listener()
    async def on_ready(self):
        """機器人準備就緒"""
        if self.dev_ids:
            print(f'👨‍💻 開發者模組已載入 ({len(self.dev_ids)} 位開發者)')
        else:
            print('⚠️  開發者模組已載入，但未設定 DEV_ID')

async def setup(bot):
    await bot.add_cog(Developer(bot))
