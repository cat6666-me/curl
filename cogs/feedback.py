import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
from dotenv import load_dotenv

class FeedbackModal(discord.ui.Modal, title='💬 提交反饋'):
    """反饋提交表單"""
    
    feedback_title = discord.ui.TextInput(
        label='反饋標題',
        placeholder='簡短描述你的反饋...',
        required=True,
        max_length=100
    )
    
    feedback_content = discord.ui.TextInput(
        label='反饋內容',
        placeholder='詳細說明你的問題、建議或想法...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        """處理反饋提交"""
        # 生成反饋 ID
        feedback_id = self.cog.generate_feedback_id()
        
        # 創建反饋記錄
        feedback_data = {
            'id': feedback_id,
            'user_id': interaction.user.id,
            'user_name': str(interaction.user),
            'title': self.feedback_title.value,
            'content': self.feedback_content.value,
            'status': 'pending',  # pending, replied, closed
            'created_at': datetime.now().isoformat(),
            'guild_id': interaction.guild.id if interaction.guild else None,
            'guild_name': interaction.guild.name if interaction.guild else 'DM',
            'replies': []
        }
        
        # 保存反饋
        self.cog.save_feedback(feedback_data)
        
        # 回應用戶
        embed = discord.Embed(
            title="✅ 反饋已提交",
            description="感謝你的反饋！我們會盡快處理。",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="反饋編號", value=f"`{feedback_id}`", inline=False)
        embed.add_field(name="標題", value=self.feedback_title.value, inline=False)
        embed.set_footer(text="你可以隨時使用反饋編號查詢狀態")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 通知開發者
        await self.cog.notify_developers(feedback_data)

class Feedback(commands.Cog):
    """反饋系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = bot.storage
        self._ensure_data_file()
        
        # 載入開發者 ID
        load_dotenv()
        dev_ids = os.getenv('DEV_ID', '')
        self.dev_ids = [int(id.strip()) for id in dev_ids.split(',') if id.strip()]
    
    def _ensure_data_file(self):
        """確保數據文件存在"""
        self.storage.load_global_data(
            'feedback',
            default={'feedbacks': [], 'counter': 0},
            legacy_filename='feedback.json'
        )
    
    def load_data(self):
        """載入反饋數據"""
        return self.storage.load_global_data(
            'feedback',
            default={'feedbacks': [], 'counter': 0},
            legacy_filename='feedback.json'
        )
    
    def save_data(self, data):
        """保存反饋數據"""
        self.storage.save_global_data('feedback', data)
    
    def generate_feedback_id(self):
        """生成反饋 ID"""
        data = self.load_data()
        data['counter'] += 1
        counter = data['counter']
        self.save_data(data)
        return f"FB{counter:04d}"
    
    def save_feedback(self, feedback_data):
        """保存單個反饋"""
        data = self.load_data()
        data['feedbacks'].append(feedback_data)
        self.save_data(data)
    
    def get_feedback(self, feedback_id):
        """獲取特定反饋"""
        data = self.load_data()
        for feedback in data['feedbacks']:
            if feedback['id'] == feedback_id.upper():
                return feedback
        return None
    
    def update_feedback(self, feedback_id, updates):
        """更新反饋"""
        data = self.load_data()
        for feedback in data['feedbacks']:
            if feedback['id'] == feedback_id.upper():
                feedback.update(updates)
                self.save_data(data)
                return True
        return False
    
    async def notify_developers(self, feedback_data):
        """通知開發者新反饋"""
        embed = discord.Embed(
            title="📬 新反饋",
            description=f"**反饋編號:** `{feedback_data['id']}`",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="標題", value=feedback_data['title'], inline=False)
        embed.add_field(name="內容", value=feedback_data['content'], inline=False)
        embed.add_field(name="提交者", value=f"<@{feedback_data['user_id']}> ({feedback_data['user_name']})", inline=True)
        embed.add_field(name="來源", value=feedback_data['guild_name'], inline=True)
        embed.set_footer(text=f"使用 /反饋 回復 {feedback_data['id']} 來回覆")
        
        # 發送給所有開發者
        for dev_id in self.dev_ids:
            try:
                dev_user = await self.bot.fetch_user(dev_id)
                await dev_user.send(embed=embed)
            except Exception as e:
                print(f"無法通知開發者 {dev_id}: {e}")
    
    feedback_group = app_commands.Group(name="反饋", description="反饋系統")
    
    @feedback_group.command(name="提交", description="提交反饋、建議或問題")
    async def submit(self, interaction: discord.Interaction):
        """提交反饋"""
        modal = FeedbackModal(self)
        await interaction.response.send_modal(modal)
    
    @feedback_group.command(name="回復", description="回覆用戶反饋（開發者專用）")
    @app_commands.describe(
        反饋編號="要回覆的反饋編號",
        回覆內容="回覆內容"
    )
    async def reply(self, interaction: discord.Interaction, 反饋編號: str, 回覆內容: str):
        """回覆反饋"""
        # 檢查是否為開發者
        if interaction.user.id not in self.dev_ids:
            await interaction.response.send_message(
                "❌ 只有機器人開發者才能回覆反饋！",
                ephemeral=True
            )
            return
        
        # 獲取反饋
        feedback = self.get_feedback(反饋編號)
        if not feedback:
            await interaction.response.send_message(
                f"❌ 找不到反饋編號 `{反饋編號}`",
                ephemeral=True
            )
            return
        
        # 添加回覆
        reply_data = {
            'developer_id': interaction.user.id,
            'developer_name': str(interaction.user),
            'content': 回覆內容,
            'replied_at': datetime.now().isoformat()
        }
        
        feedback['replies'].append(reply_data)
        feedback['status'] = 'replied'
        self.update_feedback(反饋編號, feedback)
        
        # 通知用戶
        try:
            user = await self.bot.fetch_user(feedback['user_id'])
            
            embed = discord.Embed(
                title="💬 你的反饋已收到回覆",
                description=f"**反饋編號:** `{feedback['id']}`",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="你的反饋", value=feedback['title'], inline=False)
            embed.add_field(name="開發者回覆", value=回覆內容, inline=False)
            embed.set_footer(text=f"回覆者: {interaction.user.name}")
            
            await user.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ 已回覆反饋 `{反饋編號}` 並通知用戶",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"✅ 已回覆反饋，但無法通知用戶：{e}",
                ephemeral=True
            )
    
    @feedback_group.command(name="查看", description="查看反饋詳情")
    @app_commands.describe(反饋編號="反饋編號")
    async def view(self, interaction: discord.Interaction, 反饋編號: str):
        """查看反饋詳情"""
        feedback = self.get_feedback(反饋編號)
        if not feedback:
            await interaction.response.send_message(
                f"❌ 找不到反饋編號 `{反饋編號}`",
                ephemeral=True
            )
            return
        
        # 檢查權限：只有提交者或開發者可以查看
        if interaction.user.id != feedback['user_id'] and interaction.user.id not in self.dev_ids:
            await interaction.response.send_message(
                "❌ 你沒有權限查看此反饋！",
                ephemeral=True
            )
            return
        
        # 狀態圖標
        status_icons = {
            'pending': '⏳ 待處理',
            'replied': '✅ 已回覆',
            'closed': '🔒 已關閉'
        }
        
        embed = discord.Embed(
            title=f"📋 反饋詳情 - {feedback['id']}",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(feedback['created_at'])
        )
        embed.add_field(name="標題", value=feedback['title'], inline=False)
        embed.add_field(name="內容", value=feedback['content'], inline=False)
        embed.add_field(name="狀態", value=status_icons.get(feedback['status'], '❓ 未知'), inline=True)
        embed.add_field(name="提交者", value=f"<@{feedback['user_id']}>", inline=True)
        embed.add_field(name="來源", value=feedback['guild_name'], inline=True)
        
        # 顯示回覆
        if feedback['replies']:
            replies_text = ""
            for i, reply in enumerate(feedback['replies'], 1):
                replied_time = datetime.fromisoformat(reply['replied_at'])
                replies_text += f"**回覆 {i}** ({replied_time.strftime('%Y-%m-%d %H:%M')})\n"
                replies_text += f"👤 {reply['developer_name']}\n"
                replies_text += f"{reply['content']}\n\n"
            embed.add_field(name="📬 回覆記錄", value=replies_text, inline=False)
        
        embed.set_footer(text=f"提交時間")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @feedback_group.command(name="列表", description="查看所有反饋（開發者專用）")
    @app_commands.describe(狀態="篩選狀態（可選）")
    @app_commands.choices(狀態=[
        app_commands.Choice(name="待處理", value="pending"),
        app_commands.Choice(name="已回覆", value="replied"),
        app_commands.Choice(name="已關閉", value="closed"),
        app_commands.Choice(name="全部", value="all")
    ])
    async def list_feedbacks(self, interaction: discord.Interaction, 狀態: str = "all"):
        """查看所有反饋"""
        # 檢查是否為開發者
        if interaction.user.id not in self.dev_ids:
            await interaction.response.send_message(
                "❌ 只有機器人開發者才能查看所有反饋！",
                ephemeral=True
            )
            return
        
        data = self.load_data()
        feedbacks = data['feedbacks']
        
        # 篩選
        if 狀態 != "all":
            feedbacks = [f for f in feedbacks if f['status'] == 狀態]
        
        if not feedbacks:
            await interaction.response.send_message(
                "📭 目前沒有符合條件的反饋",
                ephemeral=True
            )
            return
        
        # 按時間排序（最新的在前）
        feedbacks.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 狀態圖標
        status_icons = {
            'pending': '⏳',
            'replied': '✅',
            'closed': '🔒'
        }
        
        embed = discord.Embed(
            title="📋 反饋列表",
            description=f"共 {len(feedbacks)} 條反饋",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # 最多顯示 10 條
        for feedback in feedbacks[:10]:
            created = datetime.fromisoformat(feedback['created_at'])
            status_icon = status_icons.get(feedback['status'], '❓')
            
            field_value = f"{status_icon} {feedback['title']}\n"
            field_value += f"👤 {feedback['user_name']}\n"
            field_value += f"📅 {created.strftime('%Y-%m-%d %H:%M')}"
            
            embed.add_field(
                name=f"[{feedback['id']}]",
                value=field_value,
                inline=False
            )
        
        if len(feedbacks) > 10:
            embed.set_footer(text=f"還有 {len(feedbacks) - 10} 條反饋未顯示")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @feedback_group.command(name="關閉", description="關閉反饋（開發者專用）")
    @app_commands.describe(反饋編號="要關閉的反饋編號")
    async def close_feedback(self, interaction: discord.Interaction, 反饋編號: str):
        """關閉反饋"""
        # 檢查是否為開發者
        if interaction.user.id not in self.dev_ids:
            await interaction.response.send_message(
                "❌ 只有機器人開發者才能關閉反饋！",
                ephemeral=True
            )
            return
        
        feedback = self.get_feedback(反饋編號)
        if not feedback:
            await interaction.response.send_message(
                f"❌ 找不到反饋編號 `{反饋編號}`",
                ephemeral=True
            )
            return
        
        feedback['status'] = 'closed'
        self.update_feedback(反饋編號, feedback)
        
        await interaction.response.send_message(
            f"✅ 已關閉反饋 `{反饋編號}`",
            ephemeral=True
        )
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Feedback(bot))
