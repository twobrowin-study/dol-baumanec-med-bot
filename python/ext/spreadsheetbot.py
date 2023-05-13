from telegram import Bot
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
)

from spreadsheetbot.sheets import (
    I18n,
    LogSheet,
    Switch,
    Settings,
    Groups,
    Users,
    Registration,
    Report,
    Keyboard
)

from spreadsheetbot.basic import Log, INFO, DEBUG
from spreadsheetbot.basic.handlers import ErrorHandlerFun, ChatMemberHandlerFun

from ext.i18n import I18nAdapterClass
from ext.keyboard import KeyboardAdapterClass
from ext.users import UsersAdapterClass

from ext.doctors import Doctors
from ext.doctors_users import DoctorsUsers

UPDATE_GROUP_USER_REQUEST  = 0
UPDATE_GROUP_GROUP_REQUEST = 2
UPDATE_GROUP_CHAT_MEMBER   = 3

START_COMMAND  = 'start'
HELP_COMMAND   = 'help'
REPORT_COMMAND = 'report'

class SpreadSheetBot():
    def __init__(self, bot_token: str, sheets_secret: str, sheets_link: str, switch_update_time: int, setting_update_time: int):
        self.bot_token           = bot_token
        self.sheets_secret       = sheets_secret
        self.sheets_link         = sheets_link
        self.switch_update_time  = switch_update_time
        self.setting_update_time = setting_update_time

    async def post_init(self, app: Application) -> None:
        Switch.set_sleep_time(self.switch_update_time)
        Settings.set_sleep_time(self.setting_update_time)

        await I18n.async_init(self.sheets_secret, self.sheets_link)
        await LogSheet.async_init(self.sheets_secret, self.sheets_link)
        await Switch.async_init(self.sheets_secret, self.sheets_link)
        await Settings.async_init(self.sheets_secret, self.sheets_link)
        await Groups.async_init(self.sheets_secret, self.sheets_link)
        await Users.async_init(self.sheets_secret, self.sheets_link)
        await Registration.async_init(self.sheets_secret, self.sheets_link)
        await Report.async_init(self.sheets_secret, self.sheets_link)
        await Keyboard.async_init(self.sheets_secret, self.sheets_link)
        await Doctors.async_init(self.sheets_secret, self.sheets_link)
        await DoctorsUsers.async_init(self.sheets_secret, self.sheets_link)

        bot: Bot = app.bot
        await bot.set_my_commands([(HELP_COMMAND, Settings.help_command_description)])

        await LogSheet.write(None, "Started an application")

        Switch.update(app)
        Settings.update(app)
        Groups.update(app)
        Users.update(app)
        Registration.update(app)
        Report.update(app)
        Keyboard.update(app)
        Doctors.update(app)
        DoctorsUsers.update(app)

    async def post_shutdown(self, app: Application) -> None:
        await LogSheet.write(None, "Stopped an application")

    def run_polling(self):
        Log.info("Starting...")
        app = ApplicationBuilder() \
            .token(self.bot_token) \
            .concurrent_updates(True) \
            .post_init(self.post_init) \
            .post_shutdown(self.post_shutdown) \
            .build()

        app.add_error_handler(ErrorHandlerFun)

        ##
        # Chat member handlers
        ##
        app.add_handler(
            ChatMemberHandler(ChatMemberHandlerFun, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER, block=False),
            group=UPDATE_GROUP_CHAT_MEMBER
        )

        ##
        # Group handlers
        ##
        app.add_handler(
            CommandHandler(HELP_COMMAND, Groups.help_handler, filters=Groups.IsRegisteredFilter, block=False),
            group=UPDATE_GROUP_GROUP_REQUEST
        )

        app.add_handler(
            CommandHandler(REPORT_COMMAND, Groups.report_handler, filters=Groups.IsAdminFilter, block=False),
            group=UPDATE_GROUP_GROUP_REQUEST
        )

        ##
        # User handlers
        ##
        app.add_handler(
            MessageHandler(Users.IsRegistrationOverFilter, Users.registration_is_over_handler, block=False),
            group=UPDATE_GROUP_USER_REQUEST
        )

        app.add_handler(
            MessageHandler(Users.EditedMessageFilter, Users.edited_message_handler, block=False),
            group=UPDATE_GROUP_USER_REQUEST
        )

        app.add_handler(
            CommandHandler(START_COMMAND, Users.start_registration_handler, filters=Users.StartRegistrationFilter, block=False),
            group=UPDATE_GROUP_USER_REQUEST
        )

        app.add_handlers([
            CommandHandler(START_COMMAND, Users.restart_help_registration_handler, filters=Users.HasActiveRegistrationStateFilter, block=False),
            CommandHandler(HELP_COMMAND,  Users.restart_help_registration_handler, filters=Users.HasActiveRegistrationStateFilter, block=False),
            MessageHandler(Users.HasActiveRegistrationStateFilter, Users.proceed_registration_handler, block=False),
        ], group=UPDATE_GROUP_USER_REQUEST)
        
        app.add_handlers([
            CommandHandler(START_COMMAND, Users.restart_help_on_registration_complete_handler, filters=Users.HasNoRegistrationStateFilter, block=False),
            CommandHandler(HELP_COMMAND,  Users.restart_help_on_registration_complete_handler, filters=Users.HasNoRegistrationStateFilter, block=False),
        ], group=UPDATE_GROUP_USER_REQUEST)

        app.add_handler(MessageHandler(Users.KeyboardKeyInputFilter, Users.keyboard_key_handler, block=False), group=UPDATE_GROUP_USER_REQUEST)

        app.add_handlers([
            CallbackQueryHandler(Users.set_active_state_callback_handler, pattern=Users.CALLBACK_USER_ACTIVE_STATE_PATTERN, block=False),
            CallbackQueryHandler(Users.change_state_callback_handler,     pattern=Users.CALLBACK_USER_CHANGE_STATE_PATTERN, block=False),
            CommandHandler(START_COMMAND, Users.restart_help_change_state_handler, filters=Users.HasChangeRegistrationStateFilter, block=False),
            CommandHandler(HELP_COMMAND,  Users.restart_help_change_state_handler, filters=Users.HasChangeRegistrationStateFilter, block=False),
            MessageHandler(Users.HasChangeRegistrationStateFilter, Users.change_state_reply_handler, block=False),
        ], group=UPDATE_GROUP_USER_REQUEST)
        
        app.add_handlers([
            CallbackQueryHandler(Users.doctors_medcheck_handler,       pattern=Users.CALLBACK_MEDCHECK_PATTERN,      block=False),
            CallbackQueryHandler(Users.doctors_users_callback_handler, pattern=Users.CALLBACK_DOCTORS_USERS_PATTERN, block=False),
        ], group=UPDATE_GROUP_USER_REQUEST)
        app.add_handler(MessageHandler(Users.StrangeErrorFilter, Users.strange_error_handler, block=False), group=UPDATE_GROUP_USER_REQUEST)

        app.run_polling()
        Log.info("Done. Goodby!")