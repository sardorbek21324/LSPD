

import discord
from discord.ext import commands
import config
import os


class LSPDClerkBot(commands.Bot):
    def __init__(self):
        
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True         
        super().__init__(command_prefix="!", intents=intents)

    
    async def setup_hook(self):
        print("Загрузка модулей (cogs)...")
        
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"  > Модуль '{filename}' успешно загружен.")
                except Exception as e:
                    print(f"  > Ошибка при загрузке модуля '{filename}': {e}")
        
        
        guild = discord.Object(id=config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Дерево команд успешно синхронизировано с сервером.")

    
    async def on_ready(self):
        print("-" * 30)
        print(f'Бот {self.user} успешно запущен!')
        print(f'ID бота: {self.user.id}')
        print("-" * 30)
        

bot = LSPDClerkBot()


if not config.BOT_TOKEN:
    print("Ошибка: переменная окружения BOT_TOKEN не установлена.")
else:
    try:
        bot.run(config.BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("Ошибка: указан неверный токен бота.")