

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
        
        
        guild_id = getattr(config, "GUILD_ID", 0)
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print("Дерево команд успешно синхронизировано с сервером.")
        else:
            print("Ошибка: переменная окружения GUILD_ID не установлена.")

    
    async def on_ready(self):
        print("-" * 30)
        print(f'Бот {self.user} успешно запущен!')
        print(f'ID бота: {self.user.id}')
        print("-" * 30)
        

bot = LSPDClerkBot()


token = getattr(config, "BOT_TOKEN")
if token:
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("Ошибка: указан неверный токен бота.")
else:

    print("Ошибка: переменная окружения BOT_TOKEN не установлена.")
