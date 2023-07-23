from instaloader import instaloader, BadCredentialsException, TwoFactorAuthRequiredException, ConnectionException
from telegram import Update

from Functions.DatabaseCRUD import edit
from MyObjects import Person


def check_progress(progress: dict, person: Person, update: Update) -> str:
    if progress["name"] == 'INS_REG':  # -------------------- User is in the middle of registering instagram account

        if progress["value"] == "INS_UNAME":  # -------------------- Received instagram username

            progress = {"name": "INS_REG", "value": "INS_PASS"}
            edit(Person, person.id, progress=progress, insta_username=update.message.text)
            return "Now send me your password."

        elif progress["value"] == "INS_PASS":  # -------------------- Received instagram password

            loader = instaloader.Instaloader()

            try:  # -------------------- Try to log in with the given credentials

                loader.login(person.insta_username, update.message.text)
                edit(Person, person.id, progress=None, session=loader.save_session())

                return "Login successful."

            except TwoFactorAuthRequiredException:  # -------------------- User have 2FA enabled

                progress = {"name": "INS_REG", "value": "INS_2FA", "pass": update.message.text}
                edit(Person, id=person.id, progress=progress)

                return "You have two-factor-authentication enabled for yor account.\n" \
                       "If you have an authenticator app, get the code from it and write it here.\n" \
                       "Otherwise a code would be sent to you by SMS."

            except BadCredentialsException and ConnectionException:  # -------------------- User and password doesn't match

                edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})
                return "Username and password doesn't match. Try again.\n\nSend me your Username again please."

            finally:
                loader.close()

        elif progress['value'] == "INS_2FA":  # -------------------- Received text must be 2FA code

            loader = instaloader.Instaloader()
            try:  # -------------------- Try to log in with the given credentials

                loader.login(person.insta_username, progress['pass'])
                edit(Person, person.id, progress=None, session=loader.save_session())

                return "Login successful."

            except TwoFactorAuthRequiredException:  # -------------------- User have 2FA enabled

                try:  # -------------------- Try to log in with given 2FA code

                    loader.two_factor_login(update.message.text)

                    edit(Person, id=person.id, progress=None, session=loader.save_session())
                    return "Login successful."

                except BadCredentialsException:  # -------------------- Wrong 2FA code
                    # Ask user for 2FA code again
                    return "Wrong two-factor-authentication code. Try again.\n\nGet a new one and send it here please."

            except BadCredentialsException:  # -------------------- User and password doesn't match
                edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"}, insta_username=None)
                return "Username and password doesn't match. Try again.\n\nSend me your Username again please."

            finally:
                loader.close()
