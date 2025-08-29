

import discord
from discord.ext import commands
from discord import app_commands
import config

class SetRankModal(discord.ui.Modal, title="Назначение ранга"):
    rank_input = discord.ui.TextInput(label="На какой ранг назначить?", placeholder="Например: 5", required=True)
    def __init__(self, original_message: discord.Message):
        super().__init__()
        self.original_message = original_message
    async def on_submit(self, interaction: discord.Interaction):
        original_embed = self.original_message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.title = f"✅ {original_embed.title} [ОДОБРЕНО]"
        new_embed.color = discord.Color.green()
        status_text = f"Принял: {interaction.user.mention}\nНазначен ранг: **{self.rank_input.value}**"
        new_embed.add_field(name="Статус", value=status_text, inline=False)
        await self.original_message.edit(embed=new_embed, view=None)
        await interaction.response.send_message("Заявка успешно одобрена, ранг назначен.", ephemeral=True)

class AdminAcceptButton(discord.ui.Button):
    def __init__(self, required_roles: list[int], app_type: str):
        super().__init__(label="Принять", style=discord.ButtonStyle.success)
        self.required_roles = required_roles
        self.app_type = app_type
    async def callback(self, interaction: discord.Interaction):
        user_roles_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in user_roles_ids for role_id in self.required_roles):
            await interaction.response.send_message("У вас нет прав для выполнения этого действия.", ephemeral=True)
            return
        if self.app_type in ["восстановление", "перевод"]:
            await interaction.response.send_modal(SetRankModal(original_message=interaction.message))
        else:
            original_message = interaction.message
            original_embed = original_message.embeds[0]
            new_embed = original_embed.copy()
            new_embed.title = f"✅ {original_embed.title} [ОДОБРЕНО]"
            new_embed.color = discord.Color.green()
            status_text = f"Принял: {interaction.user.mention}"
            new_embed.add_field(name="Статус", value=status_text, inline=False)
            await original_message.edit(embed=new_embed, view=None)
            await interaction.response.send_message("Заявка на вступление успешно одобрена.", ephemeral=True)

class AdminDeclineButton(discord.ui.Button):
    def __init__(self, required_roles: list[int]):
        super().__init__(label="Отклонить", style=discord.ButtonStyle.danger)
        self.required_roles = required_roles
    async def callback(self, interaction: discord.Interaction):
        user_roles_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in user_roles_ids for role_id in self.required_roles):
            await interaction.response.send_message("У вас нет прав для выполнения этого действия.", ephemeral=True)
            return
        original_message = interaction.message
        original_embed = original_message.embeds[0]
        new_embed = original_embed.copy()
        new_embed.title = f"❌ {original_embed.title} [ОТКЛОНЕНО]"
        new_embed.color = discord.Color.dark_red()
        status_text = f"Отклонил: {interaction.user.mention}"
        new_embed.add_field(name="Статус", value=status_text, inline=False)
        await original_message.edit(embed=new_embed, view=None)
        await interaction.response.send_message("Заявка успешно отклонена.", ephemeral=True)

async def send_application(interaction: discord.Interaction, channel_id: int, roles_ids: list[int], embed: discord.Embed, app_type: str):
    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("Ошибка: Канал для заявок не найден.", ephemeral=True, delete_after=10)
        return
    ping_message = " ".join([f"<@&{role_id}>" for role_id in roles_ids])
    header_text = f"{ping_message} новая заявка ({app_type})! {interaction.user.mention}"
    admin_view = discord.ui.View()
    admin_view.add_item(AdminAcceptButton(roles_ids, app_type=app_type))
    admin_view.add_item(AdminDeclineButton(roles_ids))
    await channel.send(content=header_text, embed=embed, view=admin_view)
    await interaction.response.send_message(f"✅ Ваша заявка на {app_type} успешно отправлена!", ephemeral=True)

class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Вступление", style=discord.ButtonStyle.success, custom_id="persistent_entry_button")
    async def entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EntryApplicationModal())
    @discord.ui.button(label="Восстановление", style=discord.ButtonStyle.danger, custom_id="persistent_reinstate_button")
    async def reinstate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReinstateApplicationModal())
    @discord.ui.button(label="Перевод", style=discord.ButtonStyle.primary, custom_id="persistent_transfer_button")
    async def transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TransferApplicationModal())

class EntryApplicationModal(discord.ui.Modal, title="Форма для вступления"):
    name = discord.ui.TextInput(label="Имя Фамилия", placeholder="Sayo Paradise")
    static_id = discord.ui.TextInput(label="Номер Паспорта (Static ID)", placeholder="123456")
    documents = discord.ui.TextInput(label="Ксерокопия Документов (Imgur)", style=discord.TextStyle.paragraph)
    discord_login = discord.ui.TextInput(label="Логин Discord", placeholder="username")
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Новая заявка на вступление", color=0x3498db)
        embed.add_field(name="Имя Фамилия", value=self.name.value, inline=False)
        embed.add_field(name="Номер Паспорта (Static ID)", value=self.static_id.value, inline=False)
        embed.add_field(name="Логин Discord", value=self.discord_login.value, inline=False)
        embed.add_field(name="Ксерокопия Документов", value=self.documents.value, inline=False)
        embed.set_footer(text=f"ID пользователя: {interaction.user.id}")
        await send_application(interaction, config.ENTRY_CHANNEL_ID, config.ENTRY_ROLES_IDS, embed, "вступление")

class ReinstateApplicationModal(discord.ui.Modal, title="Форма для восстановления"):
    name = discord.ui.TextInput(label="Имя Фамилия", placeholder="Sayo Paradise")
    static_id = discord.ui.TextInput(label="Номер Паспорта (Static ID)", placeholder="123456")
    documents = discord.ui.TextInput(label="Ксерокопия Документов (Imgur)", style=discord.TextStyle.paragraph)
    last_rank = discord.ui.TextInput(label="Какой Ранг Занимали", placeholder="9")
    rank_proof = discord.ui.TextInput(label="Доказательства Нахождения На Ранге", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Новая заявка на восстановление", color=0xf1c40f)
        embed.add_field(name="Имя Фамилия", value=self.name.value, inline=False)
        embed.add_field(name="Номер Паспорта (Static ID)", value=self.static_id.value, inline=False)
        embed.add_field(name="Прежний ранг", value=self.last_rank.value, inline=False)
        embed.add_field(name="Ксерокопия документов", value=self.documents.value, inline=False)
        embed.add_field(name="Доказательства", value=self.rank_proof.value, inline=False)
        embed.set_footer(text=f"ID пользователя: {interaction.user.id}")
        await send_application(interaction, config.REINSTATE_CHANNEL_ID, config.REINSTATE_ROLES_IDS, embed, "восстановление")

class TransferApplicationModal(discord.ui.Modal, title="Форма для перевода"):
    name = discord.ui.TextInput(label="Имя Фамилия", placeholder="Sayo Paradise")
    static_id = discord.ui.TextInput(label="Номер Паспорта (Static ID)", placeholder="123456")
    documents = discord.ui.TextInput(label="Документы+Доказательство Ранга (Imgur)", style=discord.TextStyle.paragraph)
    from_where = discord.ui.TextInput(label="Откуда Перевод + Ранг?", placeholder="FIB | 10")
    approval = discord.ui.TextInput(label="Одобрение Перевода (Imgur)", placeholder="Ссылка на скриншот одобрения")
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Новая заявка на перевод", color=0x9b59b6)
        embed.add_field(name="Имя Фамилия", value=self.name.value, inline=False)
        embed.add_field(name="Номер Паспорта (Static ID)", value=self.static_id.value, inline=False)
        embed.add_field(name="Откуда перевод и ранг", value=self.from_where.value, inline=False)
        embed.add_field(name="Документы+Доказательство ранга", value=self.documents.value, inline=False)
        embed.add_field(name="Одобрение перевода", value=self.approval.value, inline=False)
        embed.set_footer(text=f"ID пользователя: {interaction.user.id}")
        await send_application(interaction, config.TRANSFER_CHANNEL_ID, config.TRANSFER_ROLES_IDS, embed, "перевод")

class ApplicationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="создать-панель-заявок", description="Создает панель для подачи заявок в LSPD.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_applications(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=True)

        if not config.LSPD_BANNER_URL or "example.png" in config.LSPD_BANNER_URL:
            await interaction.followup.send("Ошибка: Ссылка на баннер не указана в `config.py`.")
            return
            
        embed = discord.Embed(
            title="Добро пожаловать в LSPD!",
            description="Для подачи заявления выберите нужную кнопку ниже.",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=config.LSPD_BANNER_URL)
        
        #
        await interaction.channel.send(embed=embed, view=ApplicationView())
        
        
        await interaction.followup.send("Панель заявок успешно создана.")
    
    @setup_applications.error
    async def on_setup_applications_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Произошла непредвиденная ошибка: {error}", ephemeral=True)
        else: 
             if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)


async def setup(bot: commands.Bot):
    bot.add_view(ApplicationView())
    await bot.add_cog(ApplicationCog(bot))