import instaloader
from instaloader import Post, TwoFactorAuthRequiredException, BadCredentialsException


def main():
    temp_uname = "hossein_zalaghi"
    temp_upass = "-uQb996U_(a]"

    # Initialize of instaloader
    loader = instaloader.Instaloader()
    loader.load_session(temp_uname, {'sessionid': '964453641%3Ad0eP9nkqX8v9RA%3A15%3AAYc74SnKugYferZithgXjRbtjOdV8DwyKQuPlaT_GQ', 'mid': 'ZLq2JAAEAAGuKyLEVPUS8ZApoX0u', 'ig_pr': '1', 'ig_vw': '1920', 'ig_cb': '1', 'csrftoken': 'R9C84aZNxcNAIfF4gbag2ObeijDpw4mk', 's_network': '', 'ds_user_id': '964453641', 'ig_did': '2AFC1DAC-178A-4638-84BC-C74F5287BDF5', 'ig_nrcb': '1', 'rur': '"CLN\\054964453641\\0541721493953:01f7b2f7164024149e10f19d218b42c2f1adc0eb452b8311ba271804741dba29d4159ecf"'})
    # try:
    #     loader.login(temp_uname, temp_upass)
    # except TwoFactorAuthRequiredException as tfa_error:
    #     print(tfa_error)
    #     tfa_code = int(input("Enter your two-factor-auth: "))
    #     try:
    #         loader.two_factor_login(tfa_code)
    #         print(loader.save_session())
    #     except BadCredentialsException as e:
    #         print(e)

    post = Post.from_shortcode(loader.context, 'Cu9hmcth0ZI')
    print(post.caption)


if __name__ == '__main__':
    main()
