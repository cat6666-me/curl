import os
import discord
from discord import app_commands
from discord.ext import commands

import wavelink
from datetime import timedelta


def format_duration(duration_ms: int) -> str:
    if duration_ms is None or duration_ms <= 0:
        return "未知"
    seconds = int(duration_ms / 1000)
    if seconds < 60:
        return f"0:{seconds:02d}"
    return str(timedelta(seconds=seconds))


class Music(commands.Cog):
    """Lavalink 音樂播放系統"""

    music_group = app_commands.Group(name="音樂", description="音樂播放系統")

    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.node_ready = False
        self.node_params = {
            'host': os.getenv('LAVALINK_HOST', '127.0.0.1'),
            'port': int(os.getenv('LAVALINK_PORT', 2333)),
            'password': os.getenv('LAVALINK_PASSWORD', 'youshallnotpass'),
            'secure': os.getenv('LAVALINK_SECURE', 'false').lower() in ('1', 'true', 'yes')
        }

    async def cog_load(self):
        if not hasattr(self.bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(self.bot)

        self.bot.loop.create_task(self.start_lavalink_node())

    async def start_lavalink_node(self):
        await self.bot.wait_until_ready()
        if self.node_ready:
            return

        try:
            await wavelink.NodePool.create_node(bot=self.bot, **self.node_params)
            self.node_ready = True
            print(f"✅ Lavalink 節點已連線：{self.node_params['host']}:{self.node_params['port']}")
        except Exception as exc:
            print(f"❌ Lavalink 節點連線失敗：{exc}")

    def get_node(self):
        if not self.node_ready:
            return None
        try:
            return wavelink.NodePool.get_node()
        except Exception:
            return None

    async def search_track(self, query: str):
        if not self.node_ready:
            return None

        try:
            query = query.strip()
            track = await wavelink.YouTubeTrack.search(query, return_first=True)
            return track
        except Exception:
            return None

    async def ensure_player(self, voice_channel: discord.VoiceChannel):
        player = self.bot.wavelink.get_player(voice_channel.guild.id)
        if player is None or not player.is_connected():
            player = await voice_channel.connect(cls=wavelink.Player)
        return player

    async def enqueue_track(self, guild_id: int, track):
        self.queue.setdefault(guild_id, []).append(track)

    def get_queue(self, guild_id: int):
        return self.queue.get(guild_id, [])

    def pop_queue(self, guild_id: int):
        queue = self.queue.get(guild_id, [])
        if not queue:
            return None
        return queue.pop(0)

    async def send_error(self, interaction: discord.Interaction, message: str):
        await interaction.followup.send(message, ephemeral=True)

    @music_group.command(name="播放", description="播放音樂或加入播放隊列")
    @app_commands.describe(query="歌曲名稱、YouTube 連結或搜尋關鍵字")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        voice_state = interaction.user.voice
        if voice_state is None or voice_state.channel is None:
            return await self.send_error(interaction, "❌ 你必須先加入語音頻道才能播放音樂。")

        if not self.node_ready:
            return await self.send_error(interaction, "❌ Lavalink 節點尚未連線，請稍後再試。")

        if interaction.guild is None:
            return await self.send_error(interaction, "❌ 此指令只能在伺服器中使用。")

        track = await self.search_track(query)
        if track is None:
            return await self.send_error(interaction, "❌ 找不到符合的音樂，請確認關鍵字或連結是否正確。")

        player = await self.ensure_player(voice_state.channel)
        guild_id = interaction.guild.id

        if player.is_playing() or player.is_paused():
            await self.enqueue_track(guild_id, track)
            await interaction.followup.send(
                f"✅ 已將 **{track.title}** 加入隊列，排隊位置：`{len(self.get_queue(guild_id))}`。"
            )
            return

        await player.play(track)

        embed = discord.Embed(
            title="🎵 開始播放音樂",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )
        embed.add_field(name="作者", value=track.author or '未知', inline=True)
        embed.add_field(name="時長", value=format_duration(track.duration), inline=True)
        embed.set_footer(text="/音樂 暫停 / 繼續 / 跳過 / 停止")
        await interaction.followup.send(embed=embed)

    @music_group.command(name="暫停", description="暫停目前播放的音樂")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected():
            return await self.send_error(interaction, "❌ 目前沒有連接的音樂播放器。")

        if not player.is_playing():
            return await self.send_error(interaction, "❌ 目前沒有音樂可以暫停。")

        await player.pause()
        await interaction.followup.send("⏸️ 已暫停音樂。")

    @music_group.command(name="繼續", description="繼續播放已暫停的音樂")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected():
            return await self.send_error(interaction, "❌ 目前沒有連接的音樂播放器。")

        if not player.is_paused():
            return await self.send_error(interaction, "❌ 目前沒有已暫停的音樂。")

        await player.resume()
        await interaction.followup.send("▶️ 已繼續播放音樂。")

    @music_group.command(name="跳過", description="跳過目前播放的音樂")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected():
            return await self.send_error(interaction, "❌ 目前沒有連接的音樂播放器。")

        next_track = self.pop_queue(interaction.guild.id)
        if next_track is not None:
            await player.play(next_track)
            await interaction.followup.send(f"⏭️ 已跳過，現在播放：**{next_track.title}**。")
            return

        await player.stop()
        await interaction.followup.send("⏭️ 已跳過當前歌曲，隊列已清空。")

    @music_group.command(name="停止", description="停止播放並清空音樂隊列")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected():
            return await self.send_error(interaction, "❌ 目前沒有連接的音樂播放器。")

        self.queue[interaction.guild.id] = []
        await player.stop()
        await interaction.followup.send("⏹️ 已停止音樂並清空隊列。")

    @music_group.command(name="音量", description="設定音樂播放器音量")
    @app_commands.describe(level="音量等級（1-200）")
    async def volume(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer(thinking=True)
        if level < 1 or level > 200:
            return await self.send_error(interaction, "❌ 音量必須介於 1 到 200 之間。")

        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected():
            return await self.send_error(interaction, "❌ 目前沒有連接的音樂播放器。")

        await player.set_volume(level)
        await interaction.followup.send(f"🔊 已將音量設定為：`{level}%`。")

    @music_group.command(name="現在播放", description="顯示目前正在播放的曲目")
    async def now_playing(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        player = self.bot.wavelink.get_player(interaction.guild.id)
        if player is None or not player.is_connected() or not player.current:
            return await self.send_error(interaction, "❌ 目前沒有正在播放的音樂。")

        current = player.current
        queue = self.get_queue(interaction.guild.id)

        embed = discord.Embed(
            title="🎧 目前播放",
            description=f"[{current.title}]({current.uri})",
            color=discord.Color.blurple()
        )
        embed.add_field(name="作者", value=current.author or '未知', inline=True)
        embed.add_field(name="時長", value=format_duration(current.duration), inline=True)
        embed.add_field(name="隊列長度", value=f"{len(queue)} 首", inline=False)
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track, reason):
        next_track = self.pop_queue(player.guild_id)
        if next_track is None:
            return
        await player.play(next_track)


async def setup(bot):
    await bot.add_cog(Music(bot))
