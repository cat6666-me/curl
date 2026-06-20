import discord
from discord import app_commands
from discord.ext import commands
import random

class Fun(commands.Cog):
    """娛樂指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # 創建指令組
    fun_group = app_commands.Group(name="娛樂", description="娛樂功能指令")
    
    @fun_group.command(name="投擲骰子", description="投擲骰子")
    @app_commands.describe(sides="骰子面數（預設6）")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        """投擲骰子"""
        if sides < 2:
            await interaction.response.send_message("❌ 骰子至少要有2面！", ephemeral=True)
            return
        
        result = random.randint(1, sides)
        await interaction.response.send_message(f'🎲 你投擲了一個{sides}面骰子，結果是: **{result}**')
    
    @fun_group.command(name="擲硬幣", description="擲硬幣")
    async def coinflip(self, interaction: discord.Interaction):
        """擲硬幣"""
        result = random.choice(['正面 🪙', '反面 🪙'])
        await interaction.response.send_message(f'擲硬幣結果: **{result}**')
    
    @fun_group.command(name="魔法8球", description="魔法8球")
    @app_commands.describe(question="你的問題")
    async def eightball(self, interaction: discord.Interaction, question: str):
        """魔法8球回答你的問題"""
        responses = [
            "毫無疑問。",
            "確定無疑。",
            "絕對如此。",
            "你可以依賴它。",
            "正如我所見，是的。",
            "很可能。",
            "前景不錯。",
            "是的。",
            "跡象指向是。",
            "答案模糊，再試一次。",
            "稍後再問。",
            "最好現在不告訴你。",
            "現在無法預測。",
            "集中精神再問一次。",
            "別指望了。",
            "我的回答是不。",
            "我的消息來源說不。",
            "前景不太好。",
            "非常值得懷疑。"
        ]
        
        embed = discord.Embed(
            title="🎱 魔法8球",
            color=discord.Color.purple()
        )
        embed.add_field(name="問題", value=question, inline=False)
        embed.add_field(name="回答", value=random.choice(responses), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @fun_group.command(name="幫你選擇", description="幫你做選擇")
    @app_commands.describe(choices="選項，用逗號分隔")
    async def choose(self, interaction: discord.Interaction, choices: str):
        """從多個選項中隨機選擇一個"""
        options = [choice.strip() for choice in choices.split(',')]
        
        if len(options) < 2:
            await interaction.response.send_message("❌ 請至少提供2個選項，用逗號分隔", ephemeral=True)
            return
        
        chosen = random.choice(options)
        await interaction.response.send_message(f'🎯 我選擇: **{chosen}**')
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Fun(bot))
