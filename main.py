import re

import instaloader
import telegram.error
from instaloader import Post
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from Functions.Coloring import red, magenta, yellow
from Functions.DatabaseCRUD import init, read, edit
from Functions.PersonFunctions import check_person
from Functions.Progresses import check_progress
from MyObjects import Setting, Person


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    print(magenta('Received Message: ') + update.message.text)

    try:
        person = check_person(user)
        edit(Person, id=person.id, first_name=user.first_name, last_name=user.last_name, username=user.username)

        if person.progress:
            # User have unfinished progress
            progress = person.progress

            text = check_progress(progress, person, update)
            await context.bot.send_message(chat_id=person.chat_id, text=text)
            if progress["name"] == 'INS_REG' and progress["value"] == "INS_PASS":
                await context.bot.deleteMessage(chat_id=person.chat_id, message_id=update.message.id)

        else:
            re_match = re.match(
                r"(?:https?://)?(?:www.)?instagram.com/?([a-zA-Z0-9._\-]+)?/(p+)?([rel]+)?([tv]+)?([storie]+)?/([a-zA-Z0-9\-_.]+)/?([0-9]+)?",
                update.message.text)

            if re_match:
                shortcode = re_match.group(6)
                print(yellow("Shortcode: ") + shortcode)

                if person.session:
                    loader = instaloader.Instaloader()
                    loader.load_session(username=person.insta_username, session_data=person.session)
                    post = Post.from_shortcode(loader.context, shortcode=shortcode)

                    text = post.caption

                    await context.bot.send_message(chat_id=person.chat_id, text=text)

                else:
                    text = "To use this bot you must first login with your instagram account.\n" \
                           "Please send me your instagram username."

                    # Ask user to register
                    await context.bot.send_message(chat_id=person.chat_id, text=text)

                    edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})
            else:
                text = "I didn't understand. Please just send me a link to instagram media."
                await context.bot.send_message(chat_id=person.chat_id, text=text)

    except Exception as e:
        print('main: ' + red(str(e)))


def main() -> None:
    init()

    setting: Setting = read(Setting, name='BOT_TOKEN')[0]
    if setting.value:
        token = setting.value
    else:
        token = input('Please paste your bot token here:\n')
        edit(Setting, id=setting.id, value=token)

    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process))

    try:
        application.run_polling()
    except telegram.error.TimedOut as e:
        print(f'main: {red(str(e))}')
    except telegram.error.InvalidToken as e:
        print(f'main: {red(str(e))}')
        edit(Setting, id=setting.id, value=None)


if __name__ == "__main__":
    main()
