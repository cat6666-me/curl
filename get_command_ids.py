"""
Discord Bot 命令 ID 查询工具
用于获取所有斜杠命令的 ID，方便在消息中使用 </command:id> 格式
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# 加载环境变量
load_dotenv()

# 创建 Bot 实例
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"\n{'='*60}")
    print(f"Bot 已登录: {bot.user.name} (ID: {bot.user.id})")
    print(f"{'='*60}\n")
    
    try:
        # 获取全局命令
        print("📋 获取全局命令...")
        global_commands = await bot.tree.fetch_commands()
        
        if global_commands:
            print(f"\n✅ 找到 {len(global_commands)} 个全局命令:\n")
            print(f"{'命令名称':<30} {'命令 ID':<20} {'Discord 格式'}")
            print("-" * 80)
            
            for cmd in sorted(global_commands, key=lambda x: x.name):
                discord_format = f"</{cmd.name}:{cmd.id}>"
                print(f"{cmd.name:<30} {cmd.id:<20} {discord_format}")
        else:
            print("\n⚠️  没有找到全局命令")
        
        # 获取所有服务器的命令
        print(f"\n{'='*60}")
        print(f"📋 检查服务器专属命令...")
        print(f"{'='*60}\n")
        
        found_guild_commands = False
        for guild in bot.guilds:
            guild_commands = await bot.tree.fetch_commands(guild=guild)
            if guild_commands:
                found_guild_commands = True
                print(f"\n🏰 服务器: {guild.name} (ID: {guild.id})")
                print(f"找到 {len(guild_commands)} 个服务器专属命令:\n")
                print(f"{'命令名称':<30} {'命令 ID':<20} {'Discord 格式'}")
                print("-" * 80)
                
                for cmd in sorted(guild_commands, key=lambda x: x.name):
                    discord_format = f"</{cmd.name}:{cmd.id}>"
                    print(f"{cmd.name:<30} {cmd.id:<20} {discord_format}")
        
        if not found_guild_commands:
            print("⚠️  没有找到服务器专属命令")
        
        # 生成复制友好的格式
        print(f"\n{'='*60}")
        print("📝 复制友好格式 (可直接在 Discord 中使用):")
        print(f"{'='*60}\n")
        
        all_commands = global_commands
        for guild in bot.guilds:
            guild_commands = await bot.tree.fetch_commands(guild=guild)
            all_commands.extend(guild_commands)
        
        # 去重（根据命令名称）
        unique_commands = {}
        for cmd in all_commands:
            if cmd.name not in unique_commands:
                unique_commands[cmd.name] = cmd
        
        for cmd_name in sorted(unique_commands.keys()):
            cmd = unique_commands[cmd_name]
            print(f"</{cmd.name}:{cmd.id}>")
        
        print(f"\n{'='*60}")
        print("✅ 查询完成！")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭 bot
        await bot.close()


async def main():
    """主函数"""
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ 错误: 未找到 DISCORD_TOKEN 环境变量")
        print("请确保 .env 文件中包含 DISCORD_TOKEN")
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Discord Bot 命令 ID 查询工具")
    print("="*60 + "\n")
    
    # 运行 bot
    asyncio.run(main())
