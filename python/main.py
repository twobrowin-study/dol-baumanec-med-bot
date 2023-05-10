import sys

from ext.spreadsheetbot import SpreadSheetBot, Log, DEBUG

from settings import (
    BotToken,
    SheetsSecret,
    SheetsLink,
    SwitchUpdateTime,
    SettingsUpdateTime,
)

if len(sys.argv) > 1 and sys.argv[1] in ['debug', '--debug', '-D']:
    Log.setLevel(DEBUG)
    Log.debug("Starting in debug mode")

if __name__ == "__main__":
    bot = SpreadSheetBot(BotToken, SheetsSecret, SheetsLink, SwitchUpdateTime, SettingsUpdateTime)
    bot.run_polling()