from Functions.DatabaseCRUD import read, add
from MyObjects import Person


def check_person(user):
    # Find user in database
    persons: list[Person] = read(Person, chat_id=user.id)
    if not persons:  # User is not already registered
        result = add(Person(chat_id=user.id,
                            first_name=user.first_name,
                            last_name=user.last_name if user.last_name else None,
                            admin=0,
                            username=user.username))

        if result:
            # New user added successfully
            persons = read(Person, chat_id=user.id)

            if persons:
                # Newly added user read successfully
                return persons[0]

            else:
                # Somthing is wrong to read new user
                raise AddUserException("Can't find newly registered user!")

        else:
            # Couldn't add new user!
            raise AddUserException("Couldn't add new user!")

    else:
        # User already exists on the database
        return persons[0]


class AddUserException(Exception):
    pass
