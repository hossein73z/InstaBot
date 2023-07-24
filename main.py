import re

import instaloader
from telegram.error import TimedOut, InvalidToken, BadRequest
from instaloader import Post, ConnectionException
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from Functions.Coloring import red, magenta, yellow
from Functions.DatabaseCRUD import init, read, edit
from Functions.PersonFunctions import check_person
from Functions.Progresses import check_progress
from MyObjects import Setting, Person


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    print(magenta('Received Message: ') + update.message.text)

    person = check_person(user)
    edit(Person, id=person.id, first_name=user.first_name, last_name=user.last_name, username=user.username)

    if person.progress:  # -------------------- User have unfinished progress

        progress = person.progress

        # Check user progress and get new message text from 'check_progress' function
        text = check_progress(progress, person, update)
        try:
            await context.bot.send_message(chat_id=person.chat_id, text=text)
        except Exception as e:
            print('main: ' + red(str(e)))

        # If the received message is password, Delete it for security reason
        if progress["name"] == 'INS_REG' and progress["value"] == "INS_PASS":
            try:
                await context.bot.deleteMessage(chat_id=person.chat_id, message_id=update.message.id)
            except Exception as e:
                print('main: ' + red(str(e)))

    else:  # -------------------- User have no unfinished progress
        re_match = re.match(
            r"(?:https?://)?(?:www.)?instagram.com/?([a-zA-Z0-9._\-]+)?/(p+)?([rel]+)?([tv]+)?([storie]+)?/([a-zA-Z0-9\-_.]+)/?([0-9]+)?",
            update.message.text)

        if re_match:  # -------------------- The received message is an instagram link

            # Group number 6 of regex match is usually the shortcode
            group6 = re_match.group(6)
            print(yellow("Shortcode: ") + group6)

            if person.session:  # -------------------- Check if user already logged in

                loader = instaloader.Instaloader()
                loader.load_session(username=person.insta_username, session_data=person.session)

                post = None
                try:
                    post = Post.from_shortcode(loader.context, shortcode=group6)
                except ConnectionException:
                    edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"}, session=None)
                    await context.bot.send_message(chat_id=person.chat_id,
                                                   text="There was somthing wrong with instagram server. "
                                                        "you need to login again.\n"
                                                        "please send your instagram username.")
                except Exception as e:
                    print('main: ' + red(str(e)))

                loader.close()

                slides = []
                try:
                    if post.typename == "GraphSidecar":
                        # -------------------- Received link was an album

                        # Create media group list
                        slides = [
                            InputMediaVideo(media=item.video_url)
                            if item.is_video
                            else InputMediaPhoto(media=item.display_url)
                            for item in post.get_sidecar_nodes()
                        ]

                        if slides:
                            await context.bot.send_media_group(chat_id=person.chat_id,
                                                               media=slides,
                                                               reply_to_message_id=update.message.id,
                                                               caption=post.caption
                                                               )

                    elif post.typename == "GraphVideo":
                        # -------------------- Received link was a video

                        # Create media group from video and its thumbnail
                        slides = [InputMediaPhoto(media=post.url), InputMediaVideo(media=post.video_url)]
                        await context.bot.send_media_group(chat_id=person.chat_id,
                                                           media=slides,
                                                           reply_to_message_id=update.message.id,
                                                           caption=post.caption
                                                           )

                    elif post.typename == "GraphImage":
                        # -------------------- Received link was a single photo
                        await context.bot.send_photo(chat_id=person.chat_id,
                                                     photo=post.url,
                                                     reply_to_message_id=update.message.id,
                                                     caption=post.caption
                                                     )

                    else:
                        # -------------------- Received link was an unknown post
                        print(post.typename)
                except BadRequest as e:
                    if "wrong type of the web page content" in e.message:
                        media_url = ""

                        failed_msgs: list[str] = re.findall(r"#\d+", e.message)
                        for failed_msg in failed_msgs:
                            media_item = slides.pop(int(failed_msg.replace("#", "")) - 1)
                            media_url = post.video_url if type(media_item) == InputMediaVideo else post.url

                        text = "There was a problem uploading media to telegram. " \
                               "use this link to download missing media:\n\n"
                        text += media_url

                        await context.bot.send_message(chat_id=person.chat_id,
                                                       text=text,
                                                       reply_to_message_id=update.message.id
                                                       )
                        await context.bot.send_media_group(chat_id=person.chat_id,
                                                           media=slides,
                                                           reply_to_message_id=update.message.id,
                                                           caption=post.caption
                                                           )

                except Exception as e:
                    print(f'main: {red(str(e))}')

            else:
                text = "To use this bot you must first login with your instagram account.\n" \
                       "Please send me your instagram username."

                # Ask user to register
                await context.bot.send_message(chat_id=person.chat_id, text=text)

                edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})

        else:  # -------------------- The received message is not an instagram link
            text = "I didn't understand. Please just send me a link to instagram media."
            await context.bot.send_message(chat_id=person.chat_id, text=text)


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
    except TimedOut as e:
        print(f'main: {red(str(e))}')
    except InvalidToken as e:
        print(f'main: {red(str(e))}')
        edit(Setting, id=setting.id, value=None)


if __name__ == "__main__":
    main()
