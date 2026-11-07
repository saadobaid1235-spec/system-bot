import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

warnings_db = {}

async def setup_guild_roles(guild):
    mute_role = discord.utils.get(guild.roles, name="ميوت")
    if not mute_role:
        try:
            mute_role = await guild.create_role(name="ميوت", color=discord.Color.dark_grey(), reason="إعداد تلقائي لبوت السيستم")
            for channel in guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, add_reactions=False)
            print("✅ تم إنشاء رتبة 'ميوت' وضبط صلاحياتها تلقائياً.")
        except Exception as e:
            print(f"❌ خطأ في إنشاء رتبة ميوت: {e}")

    jail_role = discord.utils.get(guild.roles, name="مَسجون")
    if not jail_role:
        try:
            jail_role = await guild.create_role(name="مَسجون", color=discord.Color.red(), reason="إعداد تلقائي لبوت السيستم")
            for channel in guild.channels:
                await channel.set_permissions(jail_role, send_messages=False, connect=False, view_channel=False)
            print("✅ تم إنشاء رتبة 'مَسجون' وضبط صلاحياتها تلقائياً.")
        except Exception as e:
            print(f"❌ خطأ في إنشاء رتبة مسجون: {e}")

@bot.event
async def on_ready():
    print(f"تم تشغيل بوت السيستم بنجاح باسم {bot.user}")
    await bot.change_presence(activity=discord.Game(name="حماية وإدارة السيرفر 🛡️"))
    for guild in bot.guilds:
        await setup_guild_roles(guild)

@bot.event
async def on_guild_join(guild):
    await setup_guild_roles(guild)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ يا {ctx.author.mention}، ما عندك رتبة إدارية تخليك تستخدم هالأمر 😂.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ يا غالي أمرك ناقص! تأكد من كتابة الأمر بالطريقة الصحيحة.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"خطأ غير متوقع: {error}")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛠️ مشاكل تقنية", style=discord.ButtonStyle.primary, custom_id="tech_ticket")
    async def tech_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "تقنية")

    @discord.ui.button(label="⚖️ مشاكل بين الأعضاء", style=discord.ButtonStyle.danger, custom_id="members_ticket")
    async def members_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket_channel(interaction, "نزاع-أعضاء")

    async def create_ticket_channel(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        member = interaction.user
        
        existing_channel = discord.utils.get(guild.text_channels, name=f"تذكرة-{ticket_type.lower()}-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"❌ لديك تذكرة مفتوحة بالفعل: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"تذكرة-{ticket_type}-{member.name}",
                overwrites=overwrites
            )
            
            embed = discord.Embed(
                title=f"🎫 تذكرة جديدة ({ticket_type})",
                description=f"مرحباً {member.mention}!\nيرجى شرح مشكلتك بالتفصيل وسيتم الرد عليك من قِبل الإدارة قريباً.\n\nلإغلاق التذكرة، اضغط على الزر أدناه.",
                color=discord.Color.green()
            )
            
            await ticket_channel.send(embed=embed, view=CloseTicketView())
            await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ حدث خطأ أثناء إنشاء التذكرة: {e}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 جاري إغلاق وحذف التذكرة خلال 3 ثوانٍ...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

@bot.command(name='setup_tickets')
@commands.has_permissions(administrator=True)
async def setup_tickets_msg(ctx):
    embed = discord.Embed(
        title="🎫 نظام تذاكر الدعم الفني",
        description="إذا تواجهك أي مشكلة أو تريد التواصل مع الإدارة، اضغط على الزر المناسب أدناه لفتح تذكرة خاصة لك:",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name='سجن', aliases=['j'])
@commands.has_permissions(administrator=True)
async def jail_member(ctx, member: discord.Member, *, reason="لا توجد سبب"):
    if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
        await ctx.send(f"❌ يا {ctx.author.mention}، العضو هذا رتبته أعلى منك أو مساوي لك، ما تقدر تسجنه! 🛑")
        return

    guild = ctx.guild
    jail_role = discord.utils.get(guild.roles, name="مَسجون")
    
    if not jail_role:
        await ctx.send("❌ حدث خطأ، رتبة مَسجون غير موجودة.")
        return

    try:
        await member.add_roles(jail_role, reason=reason)
        await ctx.send(f"🔒 تم سجن العضو {member.mention} بنجاح.\n📝 السبب: {reason}")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء محاولة السجن.")

@bot.command(name='فك_سجن', aliases=['uj'])
@commands.has_permissions(administrator=True)
async def unjail_member(ctx, member: discord.Member):
    guild = ctx.guild
    jail_role = discord.utils.get(guild.roles, name="مَسجون")
    
    if jail_role in member.roles:
        await member.remove_roles(jail_role)
        await ctx.send(f"🔓 تم فك السجن عن العضو {member.mention}.")
    else:
        await ctx.send("❌ هذا العضو ليس مسجوناً أصلاً.")

@bot.command(name='ميوت', aliases=['m'])
@commands.has_permissions(manage_roles=True)
async def mute_member(ctx, member: discord.Member):
    if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
        await ctx.send(f"❌ يا {ctx.author.mention}، العضو هذا رتبته أعلى منك أو مساوي لك، ما تقدر تعطيه ميوت! 🛑")
        return

    guild = ctx.guild
    mute_role = discord.utils.get(guild.roles, name="ميوت")
    
    if not mute_role:
        await ctx.send("❌ رتبة ميوت غير موجودة.")
        return

    await member.add_roles(mute_role)
    await ctx.send(f"🔇 تم إعطاء ميوت شات للعضو {member.mention}.")

@bot.command(name='فك_ميوت', aliases=['um'])
@commands.has_permissions(manage_roles=True)
async def unmute_member(ctx, member: discord.Member):
    guild = ctx.guild
    mute_role = discord.utils.get(guild.roles, name="ميوت")
    
    if mute_role in member.roles:
        await member.remove_roles(mute_role)
        await ctx.send(f"🔊 تم فك الميوت عن العضو {member.mention}.")
    else:
        await ctx.send("❌ العضو ليس عليه ميوت.")

@bot.command(name='مسح', aliases=['c'])
@commands.has_permissions(manage_messages=True)
async def clear_chat(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 تم مسح {amount} رسالة بنجاح.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name='قفل', aliases=['lock'])
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 **تم قفل الشات بنجاح.**")

@bot.command(name='فتح', aliases=['unlock'])
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 **تم فتح الشات.**")

@bot.command(name='تحذير', aliases=['warn'])
@commands.has_permissions(manage_messages=True)
async def warn_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
        await ctx.send(f"❌ يا {ctx.author.mention}، العضو هذا رتبته أعلى منك، ما تقدر تحذره! 🛑")
        return

    m_id = member.id
    if m_id not in warnings_db:
        warnings_db[m_id] = []
    
    warnings_db[m_id].append(reason)
    count = len(warnings_db[m_id])
    
    await ctx.send(f"⚠️ تم تحذير العضو {member.mention} (التحذير رقم {count}).\nالسبب: {reason}")
    
    if count >= 3:
        jail_role = discord.utils.get(ctx.guild.roles, name="مَسجون")
        if jail_role:
            await member.add_roles(jail_role)
            await ctx.send(f"🚨 العضو {member.mention} وصل إلى 3 تحذيرات وتم سجنه تلقائياً!")

@bot.command(name='اوامر_السيستم', aliases=['h'])
async def system_help(ctx):
    embed = discord.Embed(title="🛡️ لوحة أوامر بوت السيستم والإدارة", color=discord.Color.dark_blue())
    embed.add_field(name=".سجن @العضو [السبب]", value="لسجن العضو (اختصار: `.j`)", inline=False)
    embed.add_field(name=".فك_سجن @العضو", value="لفك السجن (اختصار: `.uj`)", inline=False)
    embed.add_field(name=".ميوت @العضو", value="إعطاء ميوت شات (اختصار: `.m`)", inline=False)
    embed.add_field(name=".فك_ميوت @العضو", value="فك الميوت (اختصار: `.um`)", inline=False)
    embed.add_field(name=".تحذير @العضو [السبب]", value="إعطاء تحذير (اختصار: `.warn`)", inline=False)
    embed.add_field(name=".مسح [العدد]", value="مسح الرسائل (اختصار: `.c`)", inline=False)
    embed.add_field(name=".قفل / .فتح", value="قفل وفتح الشات", inline=False)
    embed.add_field(name=".setup_tickets", value="إرسال لوحة أزرار التذاكر في الشات الحالي", inline=False)
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
