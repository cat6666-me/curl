import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

class Statistics(commands.Cog):
    """統計分析系統"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = defaultdict(list)  # 臨時緩存，用於活躍度分析
    
    def get_stats_file(self, guild_id: int):
        """獲取統計文件路徑"""
        guild_id_str = str(guild_id)
        data_dir = os.path.join('data', guild_id_str)
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'statistics.json')
    
    def load_stats(self, guild_id: int):
        """載入統計數據"""
        file_path = self.get_stats_file(guild_id)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'total_messages': 0,
            'daily_messages': {},
            'channel_stats': {},
            'user_stats': {},
            'hourly_activity': {str(i): 0 for i in range(24)},
            'last_updated': datetime.now().isoformat()
        }
    
    def save_stats(self, guild_id: int, data: dict):
        """儲存統計數據"""
        file_path = self.get_stats_file(guild_id)
        data['last_updated'] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """監聽消息事件，記錄統計"""
        # 忽略機器人訊息和私訊
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # 載入統計數據
        stats = self.load_stats(guild_id)
        
        # 獲取當前日期和小時
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        hour = str(now.hour)
        
        # 更新總訊息數
        stats['total_messages'] = stats.get('total_messages', 0) + 1
        
        # 更新每日訊息
        if 'daily_messages' not in stats:
            stats['daily_messages'] = {}
        stats['daily_messages'][today] = stats['daily_messages'].get(today, 0) + 1
        
        # 更新頻道統計
        if 'channel_stats' not in stats:
            stats['channel_stats'] = {}
        if channel_id not in stats['channel_stats']:
            stats['channel_stats'][channel_id] = {
                'name': message.channel.name,
                'messages': 0
            }
        stats['channel_stats'][channel_id]['messages'] += 1
        stats['channel_stats'][channel_id]['name'] = message.channel.name  # 更新頻道名稱
        
        # 更新用戶統計
        if 'user_stats' not in stats:
            stats['user_stats'] = {}
        if user_id not in stats['user_stats']:
            stats['user_stats'][user_id] = {
                'username': str(message.author),
                'messages': 0,
                'channels': {}
            }
        stats['user_stats'][user_id]['messages'] += 1
        stats['user_stats'][user_id]['username'] = str(message.author)  # 更新用戶名
        
        # 更新用戶在各頻道的統計
        if channel_id not in stats['user_stats'][user_id]['channels']:
            stats['user_stats'][user_id]['channels'][channel_id] = 0
        stats['user_stats'][user_id]['channels'][channel_id] += 1
        
        # 更新每小時活躍度
        if 'hourly_activity' not in stats:
            stats['hourly_activity'] = {str(i): 0 for i in range(24)}
        stats['hourly_activity'][hour] = stats['hourly_activity'].get(hour, 0) + 1
        
        # 儲存統計數據
        self.save_stats(guild_id, stats)
    
    # 創建統計指令群組
    stats_group = app_commands.Group(name="統計", description="統計分析系統")
    
    @stats_group.command(name="活躍度", description="查看伺服器活躍度統計")
    async def activity(self, interaction: discord.Interaction):
        """查看活躍度統計"""
        stats = self.load_stats(interaction.guild.id)
        
        # 計算最近7天的訊息數
        daily_msgs = stats.get('daily_messages', {})
        today = datetime.now()
        last_7_days = []
        
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            count = daily_msgs.get(date, 0)
            last_7_days.append((date, count))
        
        # 創建嵌入訊息
        embed = discord.Embed(
            title="📊 伺服器活躍度統計",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # 總訊息數
        total = stats.get('total_messages', 0)
        embed.add_field(
            name="總訊息數",
            value=f"**{total:,}** 條",
            inline=True
        )
        
        # 今日訊息數
        today_str = today.strftime('%Y-%m-%d')
        today_count = daily_msgs.get(today_str, 0)
        embed.add_field(
            name="今日訊息",
            value=f"**{today_count:,}** 條",
            inline=True
        )
        
        # 7日平均
        week_total = sum(count for _, count in last_7_days)
        week_avg = week_total / 7
        embed.add_field(
            name="7日平均",
            value=f"**{week_avg:.0f}** 條/日",
            inline=True
        )
        
        # 最近7天趨勢
        trend_text = ""
        for date, count in last_7_days:
            bar_length = int(count / max(c for _, c in last_7_days) * 20) if max(c for _, c in last_7_days) > 0 else 0
            bar = "█" * bar_length + "░" * (20 - bar_length)
            trend_text += f"`{date}` {bar} **{count}**\n"
        
        embed.add_field(
            name="📈 最近7天訊息趨勢",
            value=trend_text or "暫無數據",
            inline=False
        )
        
        # 活躍時段
        hourly = stats.get('hourly_activity', {})
        if hourly:
            max_hour = max(hourly.items(), key=lambda x: x[1])
            min_hour = min(hourly.items(), key=lambda x: x[1])
            
            embed.add_field(
                name="🌟 最活躍時段",
                value=f"**{max_hour[0]}:00 - {max_hour[0]}:59**\n({max_hour[1]:,} 條訊息)",
                inline=True
            )
            embed.add_field(
                name="🌙 最冷清時段",
                value=f"**{min_hour[0]}:00 - {min_hour[0]}:59**\n({min_hour[1]:,} 條訊息)",
                inline=True
            )
        
        embed.set_footer(text=f"統計數據更新於")
        
        await interaction.response.send_message(embed=embed)
    
    @stats_group.command(name="熱門頻道", description="查看最熱門的頻道")
    async def top_channels(self, interaction: discord.Interaction):
        """查看熱門頻道"""
        stats = self.load_stats(interaction.guild.id)
        channel_stats = stats.get('channel_stats', {})
        
        if not channel_stats:
            await interaction.response.send_message("❌ 還沒有頻道統計數據", ephemeral=True)
            return
        
        # 排序頻道
        sorted_channels = sorted(
            channel_stats.items(),
            key=lambda x: x[1]['messages'],
            reverse=True
        )[:10]  # 取前10名
        
        embed = discord.Embed(
            title="🔥 熱門頻道排行榜 (前10名)",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        leaderboard_text = ""
        
        total_messages = sum(data['messages'] for _, data in channel_stats.items())
        
        for i, (channel_id, data) in enumerate(sorted_channels):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            percentage = (data['messages'] / total_messages * 100) if total_messages > 0 else 0
            
            # 嘗試獲取頻道
            try:
                channel = interaction.guild.get_channel(int(channel_id))
                channel_mention = channel.mention if channel else f"#{data['name']}"
            except:
                channel_mention = f"#{data['name']}"
            
            bar_length = int(percentage / 5)  # 每5%一個方塊
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            leaderboard_text += f"{medal} {channel_mention}\n"
            leaderboard_text += f"`{bar}` **{data['messages']:,}** 條 ({percentage:.1f}%)\n\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text="統計數據更新於")
        
        await interaction.response.send_message(embed=embed)
    
    @stats_group.command(name="我的統計", description="查看你的個人統計")
    async def my_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """查看個人統計"""
        target = user or interaction.user
        stats = self.load_stats(interaction.guild.id)
        user_stats = stats.get('user_stats', {})
        
        user_id_str = str(target.id)
        
        if user_id_str not in user_stats:
            await interaction.response.send_message(f"❌ {target.mention} 還沒有統計數據", ephemeral=True)
            return
        
        user_data = user_stats[user_id_str]
        total_messages = user_data.get('messages', 0)
        
        # 計算排名
        all_users = [(uid, data['messages']) for uid, data in user_stats.items()]
        all_users.sort(key=lambda x: x[1], reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(all_users) if uid == user_id_str), 0)
        
        # 計算佔比
        server_total = stats.get('total_messages', 0)
        percentage = (total_messages / server_total * 100) if server_total > 0 else 0
        
        embed = discord.Embed(
            title=f"📊 {target.display_name} 的統計數據",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="總訊息數", value=f"**{total_messages:,}** 條", inline=True)
        embed.add_field(name="伺服器排名", value=f"**#{rank}** / {len(all_users)}", inline=True)
        embed.add_field(name="佔比", value=f"**{percentage:.2f}%**", inline=True)
        
        # 最常使用的頻道
        user_channels = user_data.get('channels', {})
        if user_channels:
            sorted_channels = sorted(user_channels.items(), key=lambda x: x[1], reverse=True)[:5]
            
            channels_text = ""
            for channel_id, count in sorted_channels:
                try:
                    channel = interaction.guild.get_channel(int(channel_id))
                    channel_mention = channel.mention if channel else "未知頻道"
                except:
                    channel_mention = "未知頻道"
                
                ch_percentage = (count / total_messages * 100) if total_messages > 0 else 0
                channels_text += f"{channel_mention}: **{count:,}** 條 ({ch_percentage:.1f}%)\n"
            
            embed.add_field(
                name="🔥 最常使用的頻道 (前5名)",
                value=channels_text,
                inline=False
            )
        
        embed.set_footer(text="統計數據更新於")
        
        await interaction.response.send_message(embed=embed)
    
    @stats_group.command(name="活躍排行", description="查看最活躍用戶排行榜")
    async def active_users(self, interaction: discord.Interaction):
        """活躍用戶排行榜"""
        stats = self.load_stats(interaction.guild.id)
        user_stats = stats.get('user_stats', {})
        
        if not user_stats:
            await interaction.response.send_message("❌ 還沒有用戶統計數據", ephemeral=True)
            return
        
        # 排序用戶
        sorted_users = sorted(
            user_stats.items(),
            key=lambda x: x[1]['messages'],
            reverse=True
        )[:10]  # 取前10名
        
        embed = discord.Embed(
            title="👥 活躍用戶排行榜 (前10名)",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        leaderboard_text = ""
        
        total_messages = stats.get('total_messages', 0)
        
        for i, (user_id, data) in enumerate(sorted_users):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            percentage = (data['messages'] / total_messages * 100) if total_messages > 0 else 0
            
            # 嘗試獲取用戶
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = data.get('username', '未知用戶')
            
            bar_length = int(percentage / 5)  # 每5%一個方塊
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            leaderboard_text += f"{medal} {username}\n"
            leaderboard_text += f"`{bar}` **{data['messages']:,}** 條 ({percentage:.1f}%)\n\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text="統計數據更新於")
        
        await interaction.response.send_message(embed=embed)
    
    @stats_group.command(name="時段分析", description="查看24小時活躍度分析")
    async def hourly_analysis(self, interaction: discord.Interaction):
        """24小時活躍度分析"""
        stats = self.load_stats(interaction.guild.id)
        hourly = stats.get('hourly_activity', {})
        
        if not hourly or sum(hourly.values()) == 0:
            await interaction.response.send_message("❌ 還沒有時段統計數據", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🕐 24小時活躍度分析",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        max_count = max(hourly.values()) if hourly.values() else 1
        
        # 分三個時段顯示（0-7, 8-15, 16-23）
        periods = [
            ("🌙 凌晨時段 (0-7時)", range(0, 8)),
            ("☀️ 白天時段 (8-15時)", range(8, 16)),
            ("🌆 晚間時段 (16-23時)", range(16, 24))
        ]
        
        for period_name, hours in periods:
            period_text = ""
            for hour in hours:
                hour_str = str(hour)
                count = hourly.get(hour_str, 0)
                bar_length = int(count / max_count * 15) if max_count > 0 else 0
                bar = "█" * bar_length + "░" * (15 - bar_length)
                period_text += f"`{hour:02d}:00` {bar} **{count:,}**\n"
            
            embed.add_field(name=period_name, value=period_text, inline=False)
        
        # 統計最忙和最閒的時段
        sorted_hours = sorted(hourly.items(), key=lambda x: int(x[1]), reverse=True)
        busiest = sorted_hours[0] if sorted_hours else ("0", 0)
        quietest = sorted_hours[-1] if sorted_hours else ("0", 0)
        
        summary = f"📈 最忙：**{busiest[0]}:00** ({busiest[1]:,} 條)\n"
        summary += f"📉 最閒：**{quietest[0]}:00** ({quietest[1]:,} 條)"
        
        embed.add_field(name="📊 統計摘要", value=summary, inline=False)
        embed.set_footer(text="統計數據更新於")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))
