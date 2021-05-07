import contextlib
import re
import traceback
from typing import Iterable

from aiohttp import ClientSession
from discord import (
    AllowedMentions,
    AsyncWebhookAdapter,
    Color,
    Embed,
    Forbidden,
    Intents,
    Message,
    NotFound,
    TextChannel,
    Webhook,
    utils,
)
from discord.ext import commands
from discord.http import HTTPClient

from config import Config
from utils.error_logging import error_to_embed


class Bot(commands.Bot):
    http: HTTPClient

    def __init__(
        self,
        *,
        command_prefix: str,
        description: str,
        config: Config,
        load_extensions=True,
        loadjsk=True,
    ):
        allowed_mentions = AllowedMentions(
            users=True, replied_user=True, roles=False, everyone=False
        )
        super().__init__(
            command_prefix=self.get_custom_prefix,
            intents=Intents.all(),
            allowed_mentions=allowed_mentions,
            description=description,
            strip_after_prefix=True,
        )
        self.config = config
        self.prefix = command_prefix

        if load_extensions:
            self.load_extensions(
                (
                    "cogs.core",
                    "cogs.help_command",
                )
            )
        if loadjsk:
            self.load_extension("jishaku")

    # Properties
    @property
    def session(self) -> ClientSession:
        return self.http._HTTPClient__session  # type: ignore

    @property
    def log_webhook(self) -> Webhook:
        return Webhook.from_url(
            self.config.log_webhook, adapter=AsyncWebhookAdapter(self.session)
        )

    # Util methods
    def load_extensions(self, extentions: Iterable[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def get_custom_prefix(self, _, message: Message) -> str:
        prefix: str = self.prefix
        bot_id = self.user.id
        prefixes = [prefix, f"<@{bot_id}> ", f"<@!{bot_id}> "]

        comp = re.compile(
            "^(" + "|".join(re.escape(p) for p in prefixes) + ").*", flags=re.I
        )
        match = comp.match(message.content)
        if match is not None:
            return match.group(1)
        return prefix

    def run(self) -> None:
        return super().run(self.config.bot_token, bot=True, reconnect=True)

    # Listeners
    async def on_ready(self):
        print("Ready!")

    async def on_message(self, msg: Message):
        if msg.author.bot:
            return
        user_id = self.user.id
        if msg.content in (f"<@{user_id}>", f"<@!{user_id}>"):
            return await msg.reply(
                "My prefix here is `{}`".format(await self.get_custom_prefix(None, msg))
            )
        await self.process_commands(msg)

    # Error listeners
    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        embeds = error_to_embed()
        context_embed = Embed(
            title="Context", description=f"**Event**: {event_method}", color=Color.red()
        )
        await self.log_webhook.send(embeds=[*embeds, context_embed])

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if not isinstance(error, commands.CommandInvokeError):
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            return await ctx.send(
                embed=Embed(title=title, description=str(error), color=Color.red())
            )

        # If we've reached here, the error wasn't expected
        # Report to logs
        embed = Embed(
            title="Error",
            description="An unknown error has occurred and my developer has been notified of it.",
            color=Color.red(),
        )
        with contextlib.suppress(NotFound, Forbidden):
            await ctx.send(embed=embed)

        traceback_embeds = error_to_embed(error)

        # Add message content
        info_embed = Embed(
            title="Message content",
            description="```\n" + utils.escape_markdown(ctx.message.content) + "\n```",
            color=Color.red(),
        )
        # Guild information
        value = (
            (
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Joined**: {0.me.joined_at}\n"
                "**Member count**: {0.member_count}\n"
                "**Permission integer**: {0.me.guild_permissions.value}"
            ).format(ctx.guild)
            if ctx.guild
            else "None"
        )

        info_embed.add_field(name="Guild", value=value)
        # Channel information
        if isinstance(ctx.channel, TextChannel):
            value = (
                "**Type**: TextChannel\n"
                "**Name**: {0.name}\n"
                "**ID**: {0.id}\n"
                "**Created**: {0.created_at}\n"
                "**Permission integer**: {1}\n"
            ).format(ctx.channel, ctx.channel.permissions_for(ctx.guild.me).value)
        else:
            value = (
                "**Type**: DM\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
            ).format(ctx.channel)

        info_embed.add_field(name="Channel", value=value)

        # User info
        value = (
            "**Name**: {0}\n" "**ID**: {0.id}\n" "**Created**: {0.created_at}\n"
        ).format(ctx.author)

        info_embed.add_field(name="User", value=value)

        await self.log_webhook.send(embeds=[*traceback_embeds, info_embed])
