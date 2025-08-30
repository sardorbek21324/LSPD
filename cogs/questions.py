# cogs/questions.py

# ... (весь код до QuestionCog остается без изменений) ...
import discord
from discord.ext import commands
from discord import app_commands
import config

class QuestionModal(discord.ui.Modal, title="Задайте свой вопрос"):
    question_text = discord.ui.TextInput(label="Ваш вопрос", style=discord.TextStyle.paragraph, placeholder="Вопросы могут касаться законодательства штата, внутреннего устава, правил проекта.", required=True, max_length=1500)
    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(config.QUESTIONS_CHANNEL_ID)
        if not channel or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Ошибка: Текстовый канал для вопросов не найден или настроен неверно.", ephemeral=True)
            return
        user_tag = f"{interaction.user.display_name} | {interaction.user.id}"
        thread_title = f"Вопрос от {user_tag}"
        staff_role_mention = f"<@&{config.QUESTIONS_STAFF_ROLE_ID}>"
        header_text = f"{staff_role_mention} | {interaction.user.mention} задал вопрос:"
        embed = discord.Embed(description=f"```\n{self.question_text.value}\n```", color=discord.Color.blurple())
        embed.set_footer(text=f"ID автора вопроса: {interaction.user.id}")
        start_message = await channel.send(content=header_text, embed=embed, view=QuestionActionView())
        thread = await start_message.create_thread(name=thread_title)
        await interaction.response.send_message(f"✅ Ваш вопрос отправлен! Обсуждение здесь: {thread.mention}", ephemeral=True)

class QuestionActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Вопрос решён", style=discord.ButtonStyle.success, custom_id="resolve_question_button")
    async def resolve_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_roles_ids = [role.id for role in interaction.user.roles]
        if config.QUESTIONS_STAFF_ROLE_ID not in user_roles_ids:
            await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)
            return
        original_embed = interaction.message.embeds[0]
        try:
            footer_text = original_embed.footer.text
            original_author_id = int(footer_text.split(': ')[1])
            if interaction.user.id == original_author_id:
                await interaction.response.send_message("Вы не можете закрыть собственный вопрос.", ephemeral=True)
                return
        except (IndexError, ValueError, AttributeError):
            pass
        thread = interaction.channel
        if isinstance(thread, discord.Thread):
            current_name = thread.name
            if not current_name.startswith("✅"):
                await thread.edit(name=f"✅ {current_name}")
        new_embed = original_embed.copy()
        new_embed.add_field(name="Статус", value=f"Вопрос решил: {interaction.user.mention}", inline=False)
        button.disabled = True
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.send_message("Вопрос отмечен как решённый.", ephemeral=True)

class QuestionPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Задать вопрос", style=discord.ButtonStyle.primary, custom_id="ask_question_button")
    async def ask_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuestionModal())

# =================================================================
# КОГ С КОМАНДОЙ ДЛЯ СОЗДАНИЯ ПАНЕЛИ
# =================================================================
class QuestionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="создать-панель-вопросов", description="Создает панель для системы 'Вопрос-Ответ'.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_question_panel(self, interaction: discord.Interaction):
        ### ИСПРАВЛЕНИЕ: Добавляем defer() ###
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="Задай свой вопрос!",
            description=(
                "Нажми «Задать вопрос», чтобы отправить вопрос в специальный канал.\n\n"
                "Вопросы могут касаться: законодательства штата, внутреннего устава, правил проекта."
            ),
            color=discord.Color.dark_blue()
        )
        
        await interaction.channel.send(embed=embed, view=QuestionPanelView())
        
        ### ИСПРАВЛЕНИЕ: Используем followup.send() ###
        await interaction.followup.send("Панель вопросов успешно создана.")

    @setup_question_panel.error
    async def on_setup_question_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Произошла непредвиденная ошибка: {error}", ephemeral=True)
        else:
             if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)


# Функция для регистрации кога и постоянных кнопок
async def setup(bot: commands.Bot):
    bot.add_view(QuestionPanelView())
    bot.add_view(QuestionActionView())
    await bot.add_cog(QuestionCog(bot))
