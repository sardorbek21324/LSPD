

import discord
from discord.ext import commands
from discord import app_commands
import config
import re


class PromotionModal(discord.ui.Modal, title="Отчет о повышении"):
    name_static = discord.ui.TextInput(label="Ваше Имя И Статик", placeholder="Sayo Paradise | 12345", required=True)
    rank_from = discord.ui.TextInput(label="С Какого Ранга Повышаетесь", placeholder="Например: 2", required=True)
    rank_to = discord.ui.TextInput(label="На Какой Ранг Повышаетесь", placeholder="Например: 3", required=True)
    work_done = discord.ui.TextInput(label="Проделанная Работа + Планшет", style=discord.TextStyle.paragraph, placeholder="Описание работы + скрин планшета", required=True)
    score = discord.ui.TextInput(label="Общее Количество Баллов", placeholder="Например: 25", required=True)
    def __init__(self, target_channel_id: int, reviewer_role_id: int):
        super().__init__(); self.target_channel_id = target_channel_id; self.reviewer_role_id = reviewer_role_id
    async def on_submit(self, interaction: discord.Interaction):
        target_channel = interaction.guild.get_channel(self.target_channel_id)
        if not target_channel: return await interaction.response.send_message("Ошибка: Канал для отчетов не найден.", ephemeral=True)
        embed = discord.Embed(title="Отчет о повышении", color=discord.Color.dark_green())
        clean_name = interaction.user.global_name or interaction.user.name
        embed.set_author(name=f"{clean_name} | {self.name_static.value}", icon_url=interaction.user.avatar)
        embed.add_field(name="1. Ваше имя и статик", value=self.name_static.value, inline=False)
        embed.add_field(name="2. С какого ранга", value=self.rank_from.value, inline=False)
        embed.add_field(name="3. На какой ранг", value=self.rank_to.value, inline=False)
        embed.add_field(name="4. Проделанная работа + планшет", value=self.work_done.value, inline=False)
        embed.add_field(name="5. Общее количество баллов", value=self.score.value, inline=False)
        embed.add_field(name="Статус", value="*На рассмотрении...*", inline=False)
        embed.set_footer(text=f"ID автора отчета: {interaction.user.id}")
        header = f"<@&{self.reviewer_role_id}> — новый отчёт о повышении!\nОтчет от {interaction.user.mention}"
        view = PromotionActionView(reviewer_role_id=self.reviewer_role_id)
        await target_channel.send(content=header, embed=embed, view=view)
        await interaction.response.send_message("✅ Ваш отчет на повышение успешно отправлен.", ephemeral=True)


class PromotionActionView(discord.ui.View):
    def __init__(self, reviewer_role_id: int):
        super().__init__(timeout=None)
        self.children[0].custom_id = f"promo_accept:{reviewer_role_id}"
        self.children[1].custom_id = f"promo_decline:{reviewer_role_id}"

    async def handle_action(self, interaction: discord.Interaction, button: discord.ui.Button, is_accepted: bool):
        reviewer_role_id = int(button.custom_id.split(":")[1])
        user_roles_ids = [role.id for role in interaction.user.roles]
        if reviewer_role_id not in user_roles_ids:
            return await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True)

        await interaction.response.defer()
        original_embed = interaction.message.embeds[0]
        new_embed = original_embed.copy()
        for item in self.children: item.disabled = True
        
        if is_accepted:
            new_embed.color = discord.Color.green()
            new_embed.set_field_at(5, name="Статус", value=f"Принято: {interaction.user.mention}", inline=False)
            
            
            log_channel = interaction.guild.get_channel(config.PROMOTION_LOG_CHANNEL_ID)
            if log_channel:
                applicant_id = int(re.search(r'\d+', original_embed.footer.text).group(0))
                applicant_mention = f"<@{applicant_id}>"
                rank_to = original_embed.fields[2].value
                log_role_mention = f"<@&{config.PROMOTION_LOG_ROLE_ID}>"
                
                
                log_message = (
                    f"{log_role_mention}\n"
                    f"{interaction.user.mention} **одобрил отчет** {applicant_mention} на **{rank_to} ранг.**\n"
                    f"{interaction.message.jump_url}\n" 
                    f"После отправки КА оставьте реакцию ✅"
                )
                await log_channel.send(log_message)
        else:
            new_embed.color = discord.Color.red()
            new_embed.set_field_at(5, name="Статус", value=f"Отклонено: {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=new_embed, view=self)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, button, is_accepted=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, button, is_accepted=False)


class PromotionPanelView(discord.ui.View):
    def __init__(self, target_channel_id: int, reviewer_role_id: int):
        super().__init__(timeout=None)
        self.children[0].custom_id = f"promo_panel_button:{target_channel_id}:{reviewer_role_id}"
    @discord.ui.button(label="Подать отчет", style=discord.ButtonStyle.success)
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        _, target_channel_id, reviewer_role_id = button.custom_id.split(":")
        modal = PromotionModal(target_channel_id=int(target_channel_id), reviewer_role_id=int(reviewer_role_id))
        await interaction.response.send_modal(modal)


class PromotionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @app_commands.command(name="создать-панель-повышений", description="Создает панель для подачи отчетов на повышение.")
    @app_commands.describe(target_channel="Канал, куда будут отправляться отчеты.", reviewer_role="Роль, которая сможет одобрять отчеты.")
    @app_commands.checks.has_any_role(*config.ADMIN_ROLES_IDS)
    async def setup_promotion_panel(self, interaction: discord.Interaction, target_channel: discord.TextChannel, reviewer_role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="Отчёт о повышении", description="Нажмите кнопку, чтобы подать отчёт о повышении.", color=discord.Color.dark_blue())
        view = PromotionPanelView(target_channel_id=target_channel.id, reviewer_role_id=reviewer_role.id)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.followup.send(f"Панель повышений успешно создана. Отчеты будут уходить в {target_channel.mention} и проверяться ролью {reviewer_role.mention}.")
    @setup_promotion_panel.error
    async def on_promotion_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if not interaction.response.is_done():
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message("У вас нет необходимой роли для использования этой команды.", ephemeral=True)
        else:
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.followup.send("У вас нет необходимой роли для использования этой команды.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.add_view(PromotionPanelView(0, 0))
    bot.add_view(PromotionActionView(0))
    await bot.add_cog(PromotionsCog(bot))