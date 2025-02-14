from typing import Dict, Any, Optional
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from blockchain.token import CynixToken
import asyncio
import json


class CynixTelegramBot:
    def __init__(
            self,
            token: str,
            cynix_token: CynixToken,
            config: Dict[str, Any]
    ):
        self.bot = Application.builder().token(token).build()
        self.cynix_token = cynix_token
        self.config = config
        self.alpha_channel_id = config["alpha_channel_id"]
        self.premium_delay = 900  # 15 minutes in seconds

        # Register handlers
        self.bot.add_handler(CommandHandler("start", self._start_command))
        self.bot.add_handler(CommandHandler("verify", self._verify_command))
        self.bot.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._handle_message
            )
        )

    async def start(self):
        """Start the bot"""
        await self.bot.initialize()
        await self.bot.start()

    async def stop(self):
        """Stop the bot"""
        await self.bot.stop()

    async def send_alpha_alert(
            self,
            message: str,
            data: Optional[Dict[str, Any]] = None
    ):
        """Send alpha alert to all channels with appropriate delays"""
        try:
            # First send to premium users
            premium_message = self._format_alpha_message(message, data, True)
            await self.bot.bot.send_message(
                chat_id=self.alpha_channel_id,
                text=premium_message,
                parse_mode='Markdown'
            )

            # Wait for delay period
            await asyncio.sleep(self.premium_delay)

            # Then send to regular channel
            regular_message = self._format_alpha_message(message, data, False)
            await self.bot.bot.send_message(
                chat_id=self.config["regular_channel_id"],
                text=regular_message,
                parse_mode='Markdown'
            )

        except Exception as e:
            print(f"Error sending alpha alert: {str(e)}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
Welcome to Cynix Alpha Bot! 🚀

To access premium features:
1. Hold required amount of CYNIX tokens
2. Use /verify <wallet_address> to verify your holdings
3. Get early access to alpha signals!

For more information, visit our website.
"""
        await update.message.reply_text(welcome_message)

    async def _verify_command(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /verify command"""
        try:
            wallet_address = context.args[0]
            access_info = await self.cynix_token.check_access_level(wallet_address)

            if access_info.get("error"):
                await update.message.reply_text(
                    "Error verifying wallet. Please check the address and try again."
                )
                return

            if access_info["access_levels"]["alpha_access"]:
                invite_link = await self._generate_channel_invite(
                    update.effective_user.id
                )
                await update.message.reply_text(
                    f"✅ Verification successful! Here's your premium channel invite:\n{invite_link}"
                )
            else:
                required_amount = 1000  # Minimum for alpha access
                current_amount = access_info["total_tokens"]
                await update.message.reply_text(
                    f"❌ Insufficient CYNIX tokens. You need {required_amount} tokens for premium access.\nCurrent balance: {current_amount}"
                )

        except (IndexError, ValueError):
            await update.message.reply_text(
                "Please provide a valid wallet address:\n/verify <wallet_address>"
            )

    async def _handle_message(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle regular messages"""
        # Add custom message handling logic here
        pass

    async def _generate_channel_invite(self, user_id: int) -> str:
        """Generate temporary invite link for premium channel"""
        invite = await self.bot.bot.create_chat_invite_link(
            chat_id=self.alpha_channel_id,
            member_limit=1,
            expire_date=int(time.time()) + 3600  # 1 hour validity
        )
        return invite.invite_link

    def _format_alpha_message(
            self,
            message: str,
            data: Optional[Dict[str, Any]],
            is_premium: bool
    ) -> str:
        """Format alpha alert message"""
        header = "🔥 PREMIUM ALPHA" if is_premium else "🔔 ALPHA ALERT"

        formatted_message = f"{header}\n\n{message}"

        if data and is_premium:
            formatted_message += "\n\nDetailed Analysis:\n"
            formatted_message += json.dumps(data, indent=2)

        formatted_message += "\n\n#CynixAlpha"
        return formatted_message