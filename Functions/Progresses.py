from instaloader import instaloader, BadCredentialsException, TwoFactorAuthRequiredException
from telegram import Update

from Functions.DatabaseCRUD import edit
from MyObjects import Person


def check_progress(progress: dict, person: Person, update: Update) -> str:
    if progress["name"] == 'INS_REG':
        # User is in the middle of registering instagram account

        if progress["value"] == "INS_UNAME":
            # Received text must be user's instagram username
            progress = {"name": "INS_REG", "value": "INS_PASS"}
            edit(Person, person.id, progress=progress, insta_username=update.message.text)

            text = "Now send me your password."
            return text

        elif progress["value"] == "INS_PASS":
            # Received text must be user password

            loader = instaloader.Instaloader()
            try:
                # Try to log in with the given credentials

                loader.login(person.insta_username, update.message.text)
                text = "Login successful."
                edit(Person, person.id, progress=None, session=loader.save_session())

                return text

            except TwoFactorAuthRequiredException:
                # User have 2FA enabled

                text = "You have two-factor-authentication enabled for yor account.\n" \
                       "If you have an authenticator app, get the code from it and write it here.\n" \
                       "Otherwise a code would be sent to you by SMS."

                # Ask user for 2FA code
                progress = {"name": "INS_REG", "value": "INS_2FA", "pass": update.message.text}
                edit(Person, id=person.id, progress=progress)

                return text

            except BadCredentialsException:
                # User and password doesn't match

                edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"})

                text = "Username and password doesn't match. Try again.\n\n" \
                       "Send me your Username again please."
                return text

            finally:
                loader.close()

        elif progress['value'] == "INS_2FA":
            # Received text must be 2FA code

            loader = instaloader.Instaloader()
            try:
                # Try to log in with the given credentials

                loader.login(person.insta_username, progress['pass'])
                text = "Login successful."
                edit(Person, person.id, progress=None, session=loader.save_session())

                return text

            except TwoFactorAuthRequiredException:
                try:
                    # Try to log in with given 2FA code

                    loader.two_factor_login(update.message.text)

                    # Log in successful
                    edit(Person, id=person.id, progress=None, session=loader.save_session())

                    return "Login successful."

                except BadCredentialsException:
                    # Wrong 2FA code

                    text = "Wrong two-factor-authentication code. Try again.\n\n" \
                           "Get a new one and send it here please."

                    # Ask user for 2FA code again
                    return text

            except BadCredentialsException:
                # User and password doesn't match

                text = "Username and password doesn't match. Try again.\n\n" \
                       "Send me your Username again please."
                edit(Person, person.id, progress={"name": "INS_REG", "value": "INS_UNAME"}, insta_username=None)

                return text
