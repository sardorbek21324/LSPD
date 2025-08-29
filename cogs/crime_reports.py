
import discord
from discord.ext import commands
from discord import app_commands
import config
import os

def read_counter() -> int:
    try:
        with open(config.COUNTER_FILE_PATH, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
def save_counter(count: int):
    with open(config.COUNTER_FILE_PATH, 'w') as f:
        f.write(str(count))

class CrimeReportModal(discord.ui.Modal, title="Заявление"):
    citizen_name = discord.ui.TextInput(label="Ваше Имя", required=True)
    phone_number = discord.ui.TextInput(label="Ваш Номер Телефона", required=True)
    statement = discord.ui.TextInput(label="Суть Заявления", style=discord.TextStyle.paragraph, max_length=2000, required=True)
    evidence = discord.ui.TextInput(label="Доказательства", style=discord.TextStyle.paragraph, max_length=2000, required=True)
    documents = discord.ui.TextInput(label="Ксерокопия Документов", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        forum_channel = interaction.guild.get_channel(config.CRIME_REPORT_FORUM_ID)
        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.response.send_message("Ошибка: Форум-канал для заявлений не найден.", ephemeral=True)
            return
        current_count = read_counter()
        new_count = current_count + 1
        save_counter(new_count)
        case_number = f"LSPD-{new_count:04d}"
        embed = discord.Embed(title=f"🆕 {case_number}", color=discord.Color.from_rgb(22, 160, 133))
        embed.add_field(name="Имя", value=self.citizen_name.value, inline=False)
        embed.add_field(name="Телефон", value=self.phone_number.value, inline=False)
        embed.add_field(name="Суть заявления", value=self.statement.value, inline=False)
        embed.add_field(name="Доказательства", value=self.evidence.value, inline=False)
        embed.add_field(name="Ксерокопия документов", value=self.documents.value, inline=False)
        embed.add_field(name="Номер заявления:", value=case_number, inline=False)
        role_mention = f"<@&{config.CRIME_REPORT_ROLE_ID}>"
        header_text = f"{role_mention} поступило новое обращение!"
        await forum_channel.create_thread(name=case_number, content=header_text, embed=embed, view=ReportActionView())
        await interaction.response.send_message(f"✅ Ваше заявление `{case_number}` подано в {forum_channel.mention}", ephemeral=True)

async def check_permissions(interaction: discord.Interaction) -> bool:
    user_roles_ids = [role.id for role in interaction.user.roles]
    if config.CRIME_REPORT_ROLE_ID not in user_roles_ids:
        await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)
        return False
    return True
class TakeReportButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Взять на рассмотрение", style=discord.ButtonStyle.success, custom_id="dynamic_take_button")
    async def callback(self, interaction: discord.Interaction):
        if not await check_permissions(interaction):
            return
        view = self.view
        thread = interaction.channel
        current_name = thread.name.lstrip("🆕✅🔍 ")
        await thread.edit(name=f"🔍 {current_name}")
        original_embed = interaction.message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.add_field(name="Статус", value=f"Взял на рассмотрение: {interaction.user.mention}", inline=False)
        view.clear_items()
        view.add_item(ReviewCompleteButton())
        await interaction.message.edit(embed=new_embed, view=view)
        await interaction.response.send_message("Вы взяли это заявление в работу.", ephemeral=True)
class ReviewCompleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Рассмотрено", style=discord.ButtonStyle.primary, custom_id="dynamic_review_button")
    async def callback(self, interaction: discord.Interaction):
        if not await check_permissions(interaction):
            return
        view = self.view
        thread = interaction.channel
        current_name = thread.name.lstrip("🆕✅🔍 ")
        await thread.edit(name=f"✅ {current_name}")
        original_embed = interaction.message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.add_field(name="Итог", value=f"Рассмотрел: {interaction.user.mention}", inline=False)
        self.disabled = True
        await interaction.message.edit(embed=new_embed, view=view)
        await interaction.response.send_message("Заявление отмечено как рассмотренное.", ephemeral=True)
class ReportActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TakeReportButton())
class ReportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Подать заявление", style=discord.ButtonStyle.primary, custom_id="crime_report_button")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CrimeReportModal())


class CrimeReportCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="создать-панель-заявлений", description="Создает панель для подачи заявлений о преступлениях.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_report_panel(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Заявление",
            description="Нажмите кнопку «Подать заявление», чтобы оформить обращение.",
            color=discord.Color.dark_blue()
        )
        embed.add_field(
            name="\u200b",
            value="✅ *Об уголовной ответственности по статье 16.8 за заведомо ложные показания предупрежден(а)*"
        )
        embed.set_image(url=config.LSPD_BANNER_URL)

        await interaction.channel.send(embed=embed, view=ReportPanelView())
        
        
        await interaction.followup.send("Панель заявлений успешно создана.")

    @setup_report_panel.error
    async def on_setup_report_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Произошла непредвиденная ошибка: {error}", ephemeral=True)
        else:
             if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)



async def setup(bot: commands.Bot):
    bot.add_view(ReportPanelView())
    bot.add_view(ReportActionView())
    await bot.add_cog(CrimeReportCog(bot))