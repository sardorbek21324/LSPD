# cogs/special_equipment.py

import discord
from discord.ext import commands
from discord import app_commands
import config

# =================================================================
# МОДАЛЬНЫЕ ОКНА
# =================================================================

# --- Модальное окно 1: ЗАПРОС ---
class RequestModal(discord.ui.Modal, title="Заявка на спец.вооружение"):
    rank = discord.ui.TextInput(label="Ваш Ранг", placeholder="Например: 9", required=True)
    department = discord.ui.TextInput(label="Ваш Отдел", placeholder="K9, PD и т.д.", required=True)
    item = discord.ui.TextInput(label="Вид Спец. Вооружения", placeholder="Например: Дефибриллятор", required=True)
    payment_agreement = discord.ui.TextInput(label="Согласны Оплатить В Случае Утери?", placeholder="Да/Нет", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(config.SPEC_GEAR_REQUEST_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("Ошибка: Канал для запросов не найден.", ephemeral=True)

        embed = discord.Embed(title="Запрос спец. вооружения", color=discord.Color.green())
        embed.add_field(name="Ваш ранг", value=self.rank.value, inline=False)
        embed.add_field(name="Ваш отдел", value=self.department.value, inline=False)
        embed.add_field(name="Вид вооружения", value=self.item.value, inline=False)
        embed.add_field(name="Готовы оплатить утерю?", value=self.payment_agreement.value, inline=False)
        
        staff_role_mention = f"<@&{config.SPEC_GEAR_STAFF_ROLE_ID}>"
        
        ### ИЗМЕНЕНИЕ: Заменяем кастомный тег на прямое упоминание пользователя. ###
        header_text = f"{staff_role_mention} — новый запрос спец. вооружения!\nЗапрос оставил: {interaction.user.mention}"

        await channel.send(content=header_text, embed=embed, view=RequestActionView())
        await interaction.response.send_message("✅ Ваш запрос на вооружение успешно отправлен.", ephemeral=True)


# --- Модальное окно 2: ОТЧЕТ ---
class ReportModal(discord.ui.Modal, title="Отчет по спец. вооружению"):
    name_static = discord.ui.TextInput(label="Ваше Имя | Статик", placeholder="Sayo Paradise | 12345", required=True)
    item_taken = discord.ui.TextInput(label="Какое Спец. Вооружение Взяли?", placeholder="Например: Дрон", required=True)
    action = discord.ui.TextInput(label="Взял/Сдал", placeholder="Взял / Сдал", required=True)
    item_number = discord.ui.TextInput(label="Номер Вооружения", placeholder="SHPD-123456", required=True)
    request_link = discord.ui.TextInput(label="Ссылка На Одобренный Запрос", placeholder="Ссылка...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(config.SPEC_GEAR_REPORT_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("Ошибка: Канал для отчетов не найден.", ephemeral=True)

        embed = discord.Embed(title="Отчет по спец. вооружению", color=0xffc300) # Желтый цвет
        embed.add_field(name="Ваше имя | Статик", value=self.name_static.value, inline=False)
        embed.add_field(name="Какое вооружение взяли?", value=self.item_taken.value, inline=False)
        embed.add_field(name="Взял/сдал", value=self.action.value, inline=False)
        embed.add_field(name="Номер вооружения", value=self.item_number.value, inline=False)
        embed.add_field(name="Ссылка на одобренный запрос", value=self.request_link.value, inline=False)

        ### ИЗМЕНЕНИЕ: Заменяем кастомный тег на прямое упоминание пользователя. ###
        header_text = f"Отчет от {interaction.user.mention}"

        await channel.send(content=header_text, embed=embed)
        await interaction.response.send_message("✅ Ваш отчет успешно отправлен.", ephemeral=True)


# --- Модальное окно 3: УТЕРЯ ---
class LossModal(discord.ui.Modal, title="Утеря спец. вооружения"):
    full_info = discord.ui.TextInput(label="Отдел | Имя Фамилия | Статик | Ранг", placeholder="PD | Sayo Paradise | 12345 | 10", required=True)
    item_lost = discord.ui.TextInput(label="Что Было Утеряно?", placeholder="Дефибриллятор", required=True)
    how_lost = discord.ui.TextInput(label="Как Потеряли?", style=discord.TextStyle.paragraph, placeholder="Опишите обстоятельства...", required=True)
    proof = discord.ui.TextInput(label="Доказательства", style=discord.TextStyle.paragraph, placeholder="Ссылки на скриншоты/видео", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(config.SPEC_GEAR_LOSS_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("Ошибка: Канал для отчетов об утере не найден.", ephemeral=True)

        embed = discord.Embed(title="Отчёт об утере", description="Информация о потерянном спец. вооружении", color=0xe67e22) # Оранжевый цвет
        embed.add_field(name="Отдел | Имя Фамилия | Статик | Ранг", value=self.full_info.value, inline=False)
        embed.add_field(name="Что утеряно?", value=self.item_lost.value, inline=False)
        embed.add_field(name="Как потеряли?", value=self.how_lost.value, inline=False)
        embed.add_field(name="Доказательства", value=self.proof.value, inline=False)

        staff_role_mention = f"<@&{config.SPEC_GEAR_STAFF_ROLE_ID}>"
        
        ### ИЗМЕНЕНИЕ: Заменяем кастомный тег на прямое упоминание пользователя. ###
        header_text = f"{staff_role_mention} — новый отчет об утере!\nОтчет оставил: {interaction.user.mention}"

        await channel.send(content=header_text, embed=embed)
        await interaction.response.send_message("✅ Ваш отчет об утере успешно отправлен.", ephemeral=True)

# =================================================================
# КНОПКИ ОДОБРЕНИЯ ДЛЯ ЗАПРОСОВ (без изменений)
# =================================================================
class RequestActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_staff_perms(self, interaction: discord.Interaction) -> bool:
        user_roles_ids = [role.id for role in interaction.user.roles]
        if config.SPEC_GEAR_STAFF_ROLE_ID not in user_roles_ids:
            await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="accept_gear_request")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_staff_perms(interaction): return
        
        original_embed = interaction.message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.add_field(name="Статус", value=f"Принято: {interaction.user.mention}", inline=False)

        for item in self.children: item.disabled = True
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.send_message("Запрос одобрен.", ephemeral=True)
    
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="decline_gear_request")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_staff_perms(interaction): return

        original_embed = interaction.message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.color = discord.Color.red()
        new_embed.add_field(name="Статус", value=f"Отклонено: {interaction.user.mention}", inline=False)

        for item in self.children: item.disabled = True
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.send_message("Запрос отклонен.", ephemeral=True)


# =================================================================
# ГЛАВНАЯ ПАНЕЛЬ (без изменений)
# =================================================================
class SpecialEquipmentPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Запрос", style=discord.ButtonStyle.primary, custom_id="gear_request")
    async def request_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RequestModal())

    @discord.ui.button(label="Отчет", style=discord.ButtonStyle.success, custom_id="gear_report")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal())

    @discord.ui.button(label="Утеря", style=discord.ButtonStyle.danger, custom_id="gear_loss")
    async def loss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LossModal())

# =================================================================
# КОГ С КОМАНДОЙ (без изменений)
# =================================================================
class SpecialEquipmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="создать-панель-вооружения", description="Создает панель для запроса/отчета по спец. вооружению.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_spec_gear_panel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="Заявления на спец. вооружение",
            description="Выберите действие, нажав на одну из кнопок ниже.",
            color=discord.Color.dark_blue()
        )
        await interaction.channel.send(embed=embed, view=SpecialEquipmentPanelView())
        await interaction.followup.send("Панель успешно создана.")

    @setup_spec_gear_panel.error
    async def on_spec_gear_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Произошла непредвиденная ошибка: {error}", ephemeral=True)
        else:
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)


async def setup(bot: commands.Bot):
    bot.add_view(SpecialEquipmentPanelView())
    bot.add_view(RequestActionView())
    await bot.add_cog(SpecialEquipmentCog(bot))
