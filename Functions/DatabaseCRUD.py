from Functions.Coloring import yellow, red, magenta
from MyObjects import Base, engine, factory, Setting


def init():
    # Generate database schema
    Base.metadata.create_all(engine)

    # Add default values
    session = factory()
    objects = [Setting(id=0, name='BOT_TOKEN')]

    for item in objects:
        try:
            session.merge(item)
            session.commit()
        except Exception as e:
            print(f"init: {red(str(e))}")

    session.close()


def add(my_object: Base):
    session = factory()

    try:
        session.add(my_object)
        return True
    except Exception as e:
        print(f"add: {yellow(str(my_object))}: {red(str(e))}")
        return False
    finally:
        session.commit()
        session.close()


def read(my_class: Base, **kwargs):
    session = factory()

    try:
        query = session.query(my_class)
        for key in kwargs:
            val = kwargs[key]
            if type(val) == set:
                query = query.filter(getattr(my_class, key).in_(val))
            else:
                query = query.filter(getattr(my_class, key) == val)

        result: list[my_class] = []
        for item in query.all():
            result.append(item)
        return result if result else None

    except Exception as e:
        print(f"read:  {yellow(str(my_class))}, {magenta(kwargs)}: {red(str(e))}")
        return None
    finally:
        session.close()


def edit(my_class: Base, id, **kwargs):
    session = factory()

    try:
        rec = session.query(my_class).filter(my_class.id == id)
        rec.update(kwargs)
        session.commit()

    except Exception as e:
        print(f"edit:  {yellow(str(my_class))}, {magenta(kwargs)}: {red(str(e))}")
    finally:
        session.close()
