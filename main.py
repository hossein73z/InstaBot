import json
import logging
import re

import instaloader
import telegram.error
from instaloader import TwoFactorAuthRequiredException, BadCredentialsException, Post
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from Functions.Coloring import red, magenta, bright
from Functions.DatabaseCRUD import init, read, edit, add
from MyObjects import Setting, Person


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    print(magenta('Received Message: ') + update.message.text)
    try:
        # Find user in database
        persons: list[Person] = read(Person, chat_id=user.id)
        if not persons:  # User is not already registered
            result = add(Person(chat_id=user.id,
                                first_name=user.first_name,
                                last_name=user.last_name if user.last_name else None,
                                admin=0,
                                username=user.username))

            if result:  # New user added successfully
                persons = read(Person, chat_id=user.id)

                if persons:  # Newly added user read successfully
                    await context.bot.send_message(chat_id=persons[0].chat_id, text='Wellcome to the Bot')

                else:  # Somthing is wrong to read new user
                    await context.bot.send_message(chat_id=user.id, text="Can't find the registered user!")

            else:  # Couldn't add new user!
                await context.bot.send_message(chat_id=user.id, text="Couldn't add new user!")
        else:  # User already exists on the database
            person = persons[0]
            person.first_name = user.first_name
            person.last_name = user.last_name
            person.username = user.username
            edit(Person, id=person.id,
                 first_name=person.first_name,
                 last_name=person.last_name,
                 username=person.username)

            if person.progress:
                progress = person.progress

                if progress["name"] == 'INS_REG':

                    if progress["value"] == "INS_UNAME":
                        edit(Person, person.id,
                             progress={"name": "INS_REG", "value": "INS_PASS"},
                             insta_username=update.message.text)
                        text = "Now send me your password."

                        await context.bot.send_message(chat_id=person.chat_id, text=text)

                    elif progress["value"] == "INS_PASS":
                        await context.bot.deleteMessage(chat_id=person.chat_id, message_id=update.message.id)
                        loader = instaloader.Instaloader()

                        try:
                            loader.login(person.insta_username, update.message.text)
                            text = "Login successful."
                            await context.bot.send_message(chat_id=person.chat_id, text=text)
                            edit(Person, person.id, progress=None, session=loader.save_session())

                        except TwoFactorAuthRequiredException as tfa_error:
                            print('main: ' + red(str(tfa_error)))

                            text = "You have two-factor-authentication enabled for yor account.\n" \
                                   "If you have an authenticator app, get the code from it and write it here.\n" \
                                   "Otherwise a code would be sent to you by SMS."

                            await context.bot.send_message(chat_id=person.chat_id, text=text)

                            edit(Person, id=person.id,
                                 progress={"name": "INS_REG", "value": "INS_TFA", "pass": update.message.text})

                    elif progress['value'] == "INS_TFA":
                        loader = instaloader.Instaloader()

                        try:
                            loader.login(person.insta_username, progress['pass'])
                        except TwoFactorAuthRequiredException as tfa_error:
                            print('main: ' + red(str(tfa_error)))

                            loader.two_factor_login(update.message.text)

                            text = "Login successful."
                            await context.bot.send_message(chat_id=person.chat_id, text=text)

                            edit(Person, id=person.id, progress=None, session=loader.save_session())

            else:
                re_match = re.match(
                    r"(?:https?:\/\/)?(?:www.)?instagram.com\/?([a-zA-Z0-9\.\_\-]+)?\/([p]+)?([reel]+)?([tv]+)?([stories]+)?\/([a-zA-Z0-9\-\_\.]+)\/?([0-9]+)?",
                    update.message.text)
                shortcode = re_match.group(6)

                if shortcode:
                    if person.session:
                        loader = instaloader.Instaloader()
                        loader.load_session(username=person.insta_username, session_data=person.session)
                        post = Post.from_shortcode(loader.context, shortcode=shortcode)

                        text = post.caption

                        await context.bot.send_message(chat_id=person.chat_id, text=text)

                    else:
                        text = "To use this bot you must first login with your instagram account.\n" \
                               "Please send me your instagram username."

                        await context.bot.send_message(chat_id=person.chat_id, text=text)

                        edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})

            # # Initialization of instaloader
            # loader = instaloader.Instaloader()
            #
            # try:
            #
            #     loader.login(temp_uname, temp_pass)
            #
            # except TwoFactorAuthRequiredException as tfa_error:
            #     print(tfa_error)
            #     tfa_code = int(input("Enter your two-factor-auth: "))
            #     try:
            #         loader.two_factor_login(tfa_code)
            #         edit(Person, id=person.id, session=loader.save_session())
            #         print(loader.save_session())
            #     except BadCredentialsException as e:
            #         print(e)
            #
            # post = Post.from_shortcode(loader.context, shortcode)
            #
            # await context.bot.send_message(chat_id=person.chat_id, text=post.caption)

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
