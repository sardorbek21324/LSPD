# cogs/transfers.py (версия с финальным дизайном)

import discord
from discord.ext import commands
from discord import app_commands
import config
import re

# =================================================================
# ШАГ 3: МОДАЛЬНОЕ ОКНО ДЛЯ ВВОДА РАНГА
# =================================================================
class RankModal(discord.ui.Modal, title="Ввод ранга"):
    rank_input = discord.ui.TextInput(label="Введите ваш текущий ранг", placeholder="10", required=True)
    def __init__(self, current_dept: str, new_dept: str):
        super().__init__(); self.current_dept = current_dept; self.new_dept = new_dept
    async def on_submit(self, interaction: discord.Interaction):
        view = ConfirmView(current_dept=self.current_dept, new_dept=self.new_dept, rank=self.rank_input.value)
        await interaction.response.send_message(
            f"Старый отдел: **{self.current_dept}**\nНовый отдел: **{self.new_dept}**\nРанг: **{self.rank_input.value}**\n\nПодтвердить / Отмена?",
            view=view, ephemeral=True
        )

# =================================================================
# ШАГ 2: ВЫБОР ОТДЕЛОВ
# =================================================================
class DepartmentSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180); self.current_dept = None; self.new_dept = None
        self.add_item(DepartmentSelect(placeholder="Выберите ваш ТЕКУЩИЙ отдел", custom_id="select_current_dept"))
    async def proceed_to_rank_input(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(RankButton(current_dept=self.current_dept, new_dept=self.new_dept))
        await interaction.response.edit_message(content=f"Текущий отдел: **{self.current_dept}**\nНовый отдел: **{self.new_dept}**\n\nВведите ваш текущий ранг:", view=self)
class DepartmentSelect(discord.ui.Select):
    def __init__(self, placeholder: str, custom_id: str):
        options = [discord.SelectOption(label=dept) for dept in config.DEPARTMENTS]
        super().__init__(placeholder=placeholder, options=options, custom_id=custom_id)
    async def callback(self, interaction: discord.Interaction):
        view: DepartmentSelectView = self.view; selected_value = self.values[0]
        if self.custom_id == "select_current_dept":
            view.current_dept = selected_value; self.disabled = True
            view.add_item(DepartmentSelect(placeholder="Выберите НОВЫЙ отдел", custom_id="select_new_dept"))
            await interaction.response.edit_message(view=view)
        elif self.custom_id == "select_new_dept":
            if selected_value == view.current_dept:
                return await interaction.response.send_message("Вы не можете выбрать один и тот же отдел.", ephemeral=True, delete_after=5)
            view.new_dept = selected_value; self.disabled = True; await view.proceed_to_rank_input(interaction)
class RankButton(discord.ui.Button):
    def __init__(self, current_dept: str, new_dept: str):
        super().__init__(label="Ввести ранг", style=discord.ButtonStyle.primary)
        self.current_dept = current_dept; self.new_dept = new_dept
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RankModal(current_dept=self.current_dept, new_dept=self.new_dept)); await interaction.delete_original_response()

# =================================================================
# ШАГ 4: ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ
# =================================================================
class ConfirmView(discord.ui.View):
    def __init__(self, current_dept: str, new_dept: str, rank: str):
        super().__init__(timeout=180); self.current_dept = current_dept; self.new_dept = new_dept; self.rank = rank
    @discord.ui.button(label="Подтвердить", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        channel = interaction.guild.get_channel(config.TRANSFER_REQUEST_CHANNEL_ID)
        if not channel: return await interaction.followup.send("Ошибка: Канал для переводов не найден.", ephemeral=True)
        current_dept_data = config.DEPARTMENT_DATA.get(self.current_dept); new_dept_data = config.DEPARTMENT_DATA.get(self.new_dept)
        if not current_dept_data or not new_dept_data: return await interaction.followup.send("Ошибка: Не удалось найти данные для отделов в конфиге.", ephemeral=True)
        current_dept_leader_role_id = current_dept_data['leadership_role']; new_dept_leader_role_id = new_dept_data['leadership_role']
        header = (f"Заявление на перевод от {interaction.user.mention} !\n<@&{current_dept_leader_role_id}>\n<@&{new_dept_leader_role_id}>\nРассмотрите, пожалуйста, перевод!")
        
        ### ИСПРАВЛЕННЫЙ ДИЗАЙН ЭМБЕДА ###
        embed = discord.Embed(title="Новая заявка на перевод", color=discord.Color.dark_purple())
        # Используем global_name или name, чтобы избежать бага с никнеймом
        clean_name = interaction.user.global_name or interaction.user.name
        embed.set_author(name=f"{self.current_dept} | {clean_name}", icon_url=interaction.user.avatar)
        embed.add_field(name="1) Имя пользователя", value=interaction.user.mention, inline=False)
        embed.add_field(name="2) Текущий ранг", value=self.rank, inline=False)
        embed.add_field(name="3) Текущий отдел", value=self.current_dept, inline=False)
        embed.add_field(name="4) Новый отдел", value=self.new_dept, inline=False)
        # Формируем поле "Одобрения" с тегами ролей
        approval_text = (f"<@&{current_dept_leader_role_id}>: —\n"
                         f"<@&{new_dept_leader_role_id}>: —")
        embed.add_field(name="Одобрения", value=approval_text, inline=False)
        embed.add_field(name="Статус", value="*Ожидается рассмотрение...*", inline=False)

        await channel.send(content=header, embed=embed, view=TransferActionView())
        await interaction.edit_original_response(content="✅ Ваш перевод успешно отправлен на рассмотрение!", view=None)
    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Перевод отменен.", view=None)

# =================================================================
# ШАГ 5: СИСТЕМА ОДОБРЕНИЯ
# =================================================================
class TransferActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.approvers = set()
    def get_dept_data_from_embed(self, embed: discord.Embed):
        old_dept_name = embed.fields[2].value; new_dept_name = embed.fields[3].value
        return config.DEPARTMENT_DATA.get(old_dept_name), config.DEPARTMENT_DATA.get(new_dept_name)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="universal_transfer_accept_v2")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        old_dept_data, new_dept_data = self.get_dept_data_from_embed(interaction.message.embeds[0])
        if not old_dept_data or not new_dept_data: return await interaction.response.send_message("Ошибка: Не удалось найти данные отделов.", ephemeral=True)
        user_roles_ids = [role.id for role in interaction.user.roles]
        is_old_dept_leader = old_dept_data['leadership_role'] in user_roles_ids
        is_new_dept_leader = new_dept_data['leadership_role'] in user_roles_ids
        if not is_old_dept_leader and not is_new_dept_leader: return await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)
        if interaction.user.id in self.approvers: return await interaction.response.send_message("Вы уже одобрили этот перевод.", ephemeral=True)

        await interaction.response.defer()
        self.approvers.add(interaction.user.id)
        new_embed = interaction.message.embeds[0].copy()
        
        ### ИСПРАВЛЕННАЯ ЛОГИКА ОБНОВЛЕНИЯ ПОЛЯ "ОДОБРЕНИЯ" ###
        approval_lines = new_embed.fields[4].value.split('\n')
        if is_old_dept_leader:
            approval_lines[0] = f"<@&{old_dept_data['leadership_role']}>: {interaction.user.mention}"
        if is_new_dept_leader:
            approval_lines[1] = f"<@&{new_dept_data['leadership_role']}>: {interaction.user.mention}"
        new_embed.set_field_at(4, name="Одобрения", value="\n".join(approval_lines), inline=False)
        
        # Проверяем, одобрены ли обе стороны (проверяем, что в строках больше нет "—")
        if "—" not in approval_lines[0] and "—" not in approval_lines[1]:
            new_embed.set_field_at(5, name="Статус", value="Перевод одобрен! Ожидается выдача ролей.", inline=False)
            new_embed.color = discord.Color.gold()
            self.clear_items()
            self.add_item(IssueRolesButton())
        
        await interaction.message.edit(embed=new_embed, view=self)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="universal_transfer_decline_v2")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        old_dept_data, new_dept_data = self.get_dept_data_from_embed(interaction.message.embeds[0])
        if not old_dept_data or not new_dept_data: return await interaction.response.send_message("Ошибка: Не удалось найти данные отделов.", ephemeral=True)
        user_roles_ids = [role.id for role in interaction.user.roles]
        if old_dept_data['leadership_role'] not in user_roles_ids and new_dept_data['leadership_role'] not in user_roles_ids:
            return await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)
        await interaction.response.defer()
        new_embed = interaction.message.embeds[0].copy()
        new_embed.color = discord.Color.red()
        new_embed.set_field_at(5, name="Статус", value=f"Перевод отклонен {interaction.user.mention}.", inline=False)
        for item in self.children: item.disabled = True
        await interaction.message.edit(embed=new_embed, view=self)

class IssueRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Выдать роли", style=discord.ButtonStyle.success, custom_id="final_issue_roles_button_v2")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        original_embed = interaction.message.embeds[0]
        applicant_id = int(re.search(r'\d+', original_embed.fields[0].value).group(0))
        old_dept_name = original_embed.fields[2].value; new_dept_name = original_embed.fields[3].value
        old_dept_data = config.DEPARTMENT_DATA.get(old_dept_name); new_dept_data = config.DEPARTMENT_DATA.get(new_dept_name)
        if not new_dept_data or not old_dept_data: return await interaction.followup.send("Ошибка: Нет данных для отделов.", ephemeral=True)
        new_dept_leader_role_id = new_dept_data['leadership_role']; user_roles_ids = [role.id for role in interaction.user.roles]
        if new_dept_leader_role_id not in user_roles_ids: return await interaction.followup.send("Только руководство нового отдела может выдать роли.", ephemeral=True)
        member = await interaction.guild.fetch_member(applicant_id)
        if not member: return await interaction.followup.send("Не удалось найти сотрудника на сервере.", ephemeral=True)
        old_role = interaction.guild.get_role(old_dept_data['member_role']); new_role = interaction.guild.get_role(new_dept_data['member_role'])
        if not old_role or not new_role: return await interaction.followup.send("Ошибка: Не удалось найти одну из ролей отделов (member_role).", ephemeral=True)
        
        new_nickname = None
        current_nick = member.nick or member.global_name or member.name
        parts = re.split(r'\s*[|/\\]\s*', current_nick)
        if len(parts) > 1:
            name_and_id = " | ".join(parts[1:])
            new_nickname = f"{new_dept_name} | {name_and_id}"
        else:
            new_nickname = f"{new_dept_name} | {current_nick}"

        try:
            await member.remove_roles(old_role, reason=f"Перевод в отдел {new_dept_name}")
            await member.add_roles(new_role, reason=f"Перевод в отдел {new_dept_name}")
            if new_nickname: await member.edit(nick=new_nickname)
        except discord.Forbidden:
            return await interaction.followup.send("Ошибка: У бота недостаточно прав для управления ролями и/или никнеймами.", ephemeral=True)

        new_embed = original_embed.copy()
        new_embed.set_field_at(5, name="Статус", value=f"Перевод завершен. Роли и ник обновлены {interaction.user.mention}.", inline=False)
        self.disabled = True
        await interaction.message.edit(embed=new_embed, view=self.view)

# =================================================================
# ШАГ 1: ГЛАВНАЯ ПАНЕЛЬ
# =================================================================
class TransferPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Подать заявление", style=discord.ButtonStyle.success, custom_id="start_transfer_button_v2")
    async def start_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Пожалуйста, выберите ваш текущий отдел:", view=DepartmentSelectView(), ephemeral=True)

# =================================================================
# КОГ С КОМАНДОЙ
# =================================================================
class TransfersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @app_commands.command(name="создать-панель-переводов", description="Создает панель для заявок на перевод.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_transfer_panel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="Заявление на перевод", description="Нажмите кнопку, чтобы подать заявку на перевод.", color=discord.Color.dark_purple())
        await interaction.channel.send(embed=embed, view=TransferPanelView())
        await interaction.followup.send("Панель переводов успешно создана.")
    @setup_transfer_panel.error
    async def on_transfer_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
        else:
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.add_view(TransferPanelView())
    bot.add_view(TransferActionView())
    await bot.add_cog(TransfersCog(bot))