import re
import traceback

import instaloader
import telegram.error
from instaloader import TwoFactorAuthRequiredException, Post, BadCredentialsException
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from Functions.Coloring import red, magenta, yellow
from Functions.DatabaseCRUD import init, read, edit, add
from Functions.PersonFunctions import check_person
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

            if progress["name"] == 'INS_REG':
                # User is in the middle of registering instagram account

                if progress["value"] == "INS_UNAME":
                    # Received text must be user's instagram username
                    progress = {"name": "INS_REG", "value": "INS_PASS"}
                    edit(Person, person.id, progress=progress, insta_username=update.message.text)

                    text = "Now send me your password."
                    await context.bot.send_message(chat_id=person.chat_id, text=text)  # Ask for user password

                elif progress["value"] == "INS_PASS":
                    # Received text must be user password

                    loader = instaloader.Instaloader()
                    try:
                        # Try to log in with the given credentials

                        loader.login(person.insta_username, update.message.text)
                        text = "Login successful."
                        await context.bot.send_message(chat_id=person.chat_id, text=text)
                        edit(Person, person.id, progress=None, session=loader.save_session())

                    except TwoFactorAuthRequiredException:
                        # User have 2FA enabled

                        text = "You have two-factor-authentication enabled for yor account.\n" \
                               "If you have an authenticator app, get the code from it and write it here.\n" \
                               "Otherwise a code would be sent to you by SMS."

                        # Ask user for 2FA code
                        await context.bot.send_message(chat_id=person.chat_id, text=text)

                        progress = {"name": "INS_REG", "value": "INS_2FA", "pass": update.message.text}
                        edit(Person, id=person.id, progress=progress)

                    except BadCredentialsException:
                        # User and password doesn't match

                        edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})

                        text = "Username and password doesn't match. Try again.\n\n" \
                               "Send me your Username again please."
                        await context.bot.send_message(chat_id=person.chat_id, text=text)

                    finally:
                        loader.close()
                        await context.bot.deleteMessage(chat_id=person.chat_id, message_id=update.message.id)

                elif progress['value'] == "INS_2FA":
                    # Received text must be 2FA code

                    loader = instaloader.Instaloader()
                    try:
                        # Try to log in with the given credentials

                        loader.login(person.insta_username, progress['pass'])
                        text = "Login successful."
                        await context.bot.send_message(chat_id=person.chat_id, text=text)
                        edit(Person, person.id, progress=None, session=loader.save_session())

                    except TwoFactorAuthRequiredException:
                        try:
                            # Try to log in with given 2FA code

                            loader.two_factor_login(update.message.text)

                            # Log in successful
                            await context.bot.send_message(chat_id=person.chat_id, text="Login successful.")
                            edit(Person, id=person.id, progress=None, session=loader.save_session())

                        except BadCredentialsException:
                            # Wrong 2FA code

                            text = "Wrong two-factor-authentication code. Try again.\n\n" \
                                   "Get a new one and send it here please."

                            # Ask user for 2FA code again
                            await context.bot.send_message(chat_id=person.chat_id, text=text)

                    except BadCredentialsException:
                        # User and password doesn't match

                        text = "Username and password doesn't match. Try again.\n\n" \
                               "Send me your Username again please."
                        await context.bot.send_message(chat_id=person.chat_id, text=text)
                        edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"}, insta_username=None)

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
