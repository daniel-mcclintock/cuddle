# cuddle.py
An awkward Hug for your PeeWee class

## Wha?
 - A decorator for quick and dirty [Hug API](https://hugapi.github.io/hug/) CRUD.
 - It gives you basic CRUD for your [PeeWee](http://docs.peewee-orm.com) classes.

## Huh?
 - Put cuddle.py somewhere
 - Create some PeeWee classes

```python
# models.py
import peewee

from cuddle import Cuddle

DATABASE = peewee.SqliteDatabase('friends.db')

@Cuddle
class OldFriend(peewee.Model):
    name = peewee.CharField()

    class Meta:
        database = DATABASE

@Cuddle
class Frenemy(peewee.Model):
    name = peewee.CharField()

    class Meta:
        database = DATABASE
```

 - Use the newly Cuddled classes

```bash
hug -f models.py
```

 - Extend an existing Hug API

```python
# main.py
import hug

import models

@hug.extend_api("/api")
def extended():
    return [models]
```

```bash
hug -f main.py
```

## Ooh!
It gives you the following Routes:
 - GET `/{model_name}/{primary_key}`: by primary key
 - DELETE `/{model_name}/{primary_key}`: by primary key
 - PUT `/{model_name}/{primary_key}`: by primary key
 - POST `/{model_name}`: create new instance, JSON Body containing model fields
 - GET `/{model_name}/query`: query by model fields, basic pagination

## Nah?
Did I mention this was for quick and dirty CRUD, it doesn't do much
