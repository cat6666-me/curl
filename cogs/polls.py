import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio
from typing import Optional

class PollButton(discord.ui.Button):
    """投票按鈕"""
    def __init__(self, option_index: int, option_text: str, emoji: str = None):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=option_text,
            custom_id=f"poll_option_{option_index}",
            emoji=emoji
        )
        self.option_index = option_index
        self.option_text = option_text
    
    async def callback(self, interaction: discord.Interaction):
        """處理投票按鈕點擊"""
        view: PollView = self.view
        await view.handle_vote(interaction, self.option_index)

class EndPollButton(discord.ui.Button):
    """結束投票按鈕"""
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="結束投票",
            emoji="🔒",
            custom_id="end_poll"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """處理結束投票"""
        view: PollView = self.view
        
        # 檢查權限（只有創建者或管理員可以結束）
        if interaction.user.id != view.creator_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 只有投票創建者或管理員可以結束投票！", ephemeral=True)
            return
        
        await view.end_poll(interaction)

class ResultsButton(discord.ui.Button):
    """查看結果按鈕"""
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="查看結果",
            emoji="📊",
            custom_id="view_results"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """顯示當前投票結果"""
        view: PollView = self.view
        await view.show_results(interaction)

class PollView(discord.ui.View):
    """投票視圖"""
    def __init__(self, poll_data: dict, cog):
        super().__init__(timeout=None)  # 永不超時
        self.poll_data = poll_data
        self.cog = cog
        self.creator_id = poll_data['creator_id']
        self.multi_choice = poll_data['multi_choice']
        self.anonymous = poll_data.get('anonymous', False)
        
        # 添加選項按鈕
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, option in enumerate(poll_data['options']):
            emoji = emojis[i] if i < len(emojis) else None
            self.add_item(PollButton(i, option, emoji))
        
        # 添加功能按鈕
        self.add_item(ResultsButton())
        self.add_item(EndPollButton())
    
    async def handle_vote(self, interaction: discord.Interaction, option_index: int):
        """處理投票"""
        user_id = str(interaction.user.id)
        
        # 獲取當前投票數據
        poll_id = self.poll_data['id']
        current_data = self.cog.get_poll(poll_id)
        
        if not current_data or current_data.get('ended', False):
            await interaction.response.send_message("❌ 此投票已結束！", ephemeral=True)
            return
        
        # 檢查用戶是否已投票
        if user_id in current_data['votes']:
            if not self.multi_choice:
                # 單選模式：改投
                old_choice = current_data['votes'][user_id]
                if old_choice == option_index:
                    # 取消投票
                    del current_data['votes'][user_id]
                    await interaction.response.send_message(f"✅ 已取消投票", ephemeral=True)
                else:
                    # 改投
                    current_data['votes'][user_id] = option_index
                    await interaction.response.send_message(
                        f"✅ 已改投為：**{current_data['options'][option_index]}**", 
                        ephemeral=True
                    )
            else:
                # 多選模式：切換選項
                if not isinstance(current_data['votes'][user_id], list):
                    current_data['votes'][user_id] = [current_data['votes'][user_id]]
                
                if option_index in current_data['votes'][user_id]:
                    current_data['votes'][user_id].remove(option_index)
                    if not current_data['votes'][user_id]:
                        del current_data['votes'][user_id]
                    await interaction.response.send_message(
                        f"✅ 已取消選擇：**{current_data['options'][option_index]}**", 
                        ephemeral=True
                    )
                else:
                    current_data['votes'][user_id].append(option_index)
                    await interaction.response.send_message(
                        f"✅ 已添加選擇：**{current_data['options'][option_index]}**", 
                        ephemeral=True
                    )
        else:
            # 首次投票
            if self.multi_choice:
                current_data['votes'][user_id] = [option_index]
            else:
                current_data['votes'][user_id] = option_index
            
            await interaction.response.send_message(
                f"✅ 已投票：**{current_data['options'][option_index]}**", 
                ephemeral=True
            )
        
        # 保存數據
        self.cog.save_poll(current_data)
        
        # 更新顯示
        await self.update_poll_message(interaction.message)
    
    async def show_results(self, interaction: discord.Interaction):
        """顯示投票結果"""
        poll_id = self.poll_data['id']
        current_data = self.cog.get_poll(poll_id)
        
        if not current_data:
            await interaction.response.send_message("❌ 找不到投票數據", ephemeral=True)
            return
        
        embed = self.create_results_embed(current_data)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def end_poll(self, interaction: discord.Interaction):
        """結束投票"""
        poll_id = self.poll_data['id']
        current_data = self.cog.get_poll(poll_id)
        
        if not current_data:
            await interaction.response.send_message("❌ 找不到投票數據", ephemeral=True)
            return
        
        current_data['ended'] = True
        current_data['end_time'] = datetime.now().isoformat()
        self.cog.save_poll(current_data)
        
        # 禁用所有按鈕
        for item in self.children:
            item.disabled = True
        
        # 更新消息
        embed = self.create_results_embed(current_data, ended=True)
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def update_poll_message(self, message):
        """更新投票消息"""
        poll_id = self.poll_data['id']
        current_data = self.cog.get_poll(poll_id)
        
        if current_data:
            embed = self.create_poll_embed(current_data)
            try:
                await message.edit(embed=embed)
            except:
                pass
    
    def create_poll_embed(self, poll_data: dict) -> discord.Embed:
        """創建投票 Embed"""
        embed = discord.Embed(
            title=f"📊 {poll_data['question']}",
            description=poll_data.get('description', ''),
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(poll_data['created_at'])
        )
        
        # 統計投票
        vote_counts = self.calculate_votes(poll_data)
        total_votes = sum(vote_counts.values())
        
        # 顯示選項和當前票數
        options_text = ""
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, option in enumerate(poll_data['options']):
            count = vote_counts.get(i, 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            bar_length = int(percentage / 5)  # 20格
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            emoji = emojis[i] if i < len(emojis) else "▪️"
            options_text += f"{emoji} **{option}**\n"
            options_text += f"{bar} {percentage:.1f}% ({count} 票)\n\n"
        
        embed.add_field(name="選項", value=options_text or "暫無選項", inline=False)
        
        # 投票設置
        settings = []
        if poll_data['multi_choice']:
            settings.append("✅ 多選")
        else:
            settings.append("🔘 單選")
        
        if poll_data.get('anonymous'):
            settings.append("🕶️ 匿名")
        
        embed.add_field(name="設置", value=" | ".join(settings), inline=True)
        embed.add_field(name="總票數", value=f"**{total_votes}** 票", inline=True)
        
        embed.set_footer(text=f"創建者: {poll_data['creator_name']}")
        
        return embed
    
    def create_results_embed(self, poll_data: dict, ended: bool = False) -> discord.Embed:
        """創建結果 Embed（詳細版）"""
        embed = discord.Embed(
            title=f"📊 投票結果：{poll_data['question']}",
            color=discord.Color.green() if ended else discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if poll_data.get('description'):
            embed.description = poll_data['description']
        
        # 統計投票
        vote_counts = self.calculate_votes(poll_data)
        total_votes = sum(vote_counts.values())
        
        # 排序選項（按票數）
        sorted_options = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        
        results_text = ""
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        medals = ["🥇", "🥈", "🥉"]
        
        for rank, (index, count) in enumerate(sorted_options):
            option = poll_data['options'][index]
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            bar_length = int(percentage / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            medal = medals[rank] if rank < 3 else emojis[index] if index < len(emojis) else "▪️"
            results_text += f"{medal} **{option}**\n"
            results_text += f"{bar} {percentage:.1f}% ({count} 票)\n\n"
        
        embed.add_field(name="結果統計", value=results_text or "暫無投票", inline=False)
        
        # 顯示投票者（如果不是匿名）
        if not poll_data.get('anonymous') and poll_data['votes']:
            voters_text = f"共 {len(poll_data['votes'])} 人參與投票"
            embed.add_field(name="參與人數", value=voters_text, inline=False)
        
        if ended:
            embed.add_field(name="狀態", value="🔒 **投票已結束**", inline=False)
        
        embed.set_footer(text=f"創建者: {poll_data['creator_name']}")
        
        return embed
    
    def calculate_votes(self, poll_data: dict) -> dict:
        """計算投票結果"""
        vote_counts = {i: 0 for i in range(len(poll_data['options']))}
        
        for user_id, vote in poll_data['votes'].items():
            if isinstance(vote, list):
                for v in vote:
                    vote_counts[v] = vote_counts.get(v, 0) + 1
            else:
                vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        return vote_counts

class Polls(commands.Cog):
    """投票/問卷系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = bot.storage
        self.load_polls()
    
    def load_polls(self):
        """載入投票數據"""
        self.polls = self.storage.load_global_data(
            'polls',
            default={},
            legacy_filename='polls.json'
        )
    
    def save_polls(self):
        """保存所有投票數據"""
        self.storage.save_global_data('polls', self.polls)
    
    def get_poll(self, poll_id: str) -> dict:
        """獲取投票數據"""
        return self.polls.get(poll_id)
    
    def save_poll(self, poll_data: dict):
        """保存單個投票數據"""
        self.polls[poll_data['id']] = poll_data
        self.save_polls()
    
    # 創建指令組
    poll_group = app_commands.Group(name="投票", description="投票/問卷功能")
    
    @poll_group.command(name="創建", description="創建一個新投票")
    @app_commands.describe(
        問題="投票問題",
        選項="選項，用逗號分隔（例如：選項1,選項2,選項3）",
        多選="是否允許多選（預設：否）",
        匿名="是否匿名投票（預設：否）",
        說明="投票說明（可選）"
    )
    async def create_poll(
        self, 
        interaction: discord.Interaction, 
        問題: str,
        選項: str,
        多選: bool = False,
        匿名: bool = False,
        說明: Optional[str] = None
    ):
        """創建投票"""
        # 解析選項
        options = [opt.strip() for opt in 選項.split(',') if opt.strip()]
        
        if len(options) < 2:
            await interaction.response.send_message("❌ 至少需要 2 個選項！", ephemeral=True)
            return
        
        if len(options) > 10:
            await interaction.response.send_message("❌ 最多支持 10 個選項！", ephemeral=True)
            return
        
        # 創建投票數據
        poll_id = f"{interaction.guild.id}_{interaction.channel.id}_{int(datetime.now().timestamp())}"
        poll_data = {
            'id': poll_id,
            'question': 問題,
            'description': 說明,
            'options': options,
            'multi_choice': 多選,
            'anonymous': 匿名,
            'creator_id': interaction.user.id,
            'creator_name': interaction.user.name,
            'guild_id': interaction.guild.id,
            'channel_id': interaction.channel.id,
            'created_at': datetime.now().isoformat(),
            'votes': {},
            'ended': False
        }
        
        # 創建視圖
        view = PollView(poll_data, self)
        embed = view.create_poll_embed(poll_data)
        
        # 發送投票
        await interaction.response.send_message(embed=embed, view=view)
        
        # 獲取消息並保存
        message = await interaction.original_response()
        poll_data['message_id'] = message.id
        
        # 保存投票
        self.save_poll(poll_data)
    
    @poll_group.command(name="列表", description="查看當前頻道的所有投票")
    async def list_polls(self, interaction: discord.Interaction):
        """列出投票"""
        channel_polls = [
            p for p in self.polls.values() 
            if p['channel_id'] == interaction.channel.id and not p.get('ended', False)
        ]
        
        if not channel_polls:
            await interaction.response.send_message("📊 當前頻道沒有進行中的投票", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 進行中的投票",
            color=discord.Color.blue()
        )
        
        for poll in channel_polls[:10]:  # 最多顯示10個
            total_votes = len(poll['votes'])
            embed.add_field(
                name=poll['question'],
                value=f"選項數: {len(poll['options'])} | 投票數: {total_votes}\n創建者: {poll['creator_name']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """機器人準備就緒"""
        # 重新註冊所有持久化視圖
        for poll_data in self.polls.values():
            if not poll_data.get('ended', False):
                view = PollView(poll_data, self)
                self.bot.add_view(view, message_id=poll_data.get('message_id'))
        
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Polls(bot))
