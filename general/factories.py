import factory
from factory.django import DjangoModelFactory
from general import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.Faker('password')
    is_staff = True


class PostFactory(DjangoModelFactory):
    class Meta:
        model = models.Post

    author = factory.SubFactory(UserFactory)
    title = factory.Faker("word")
    body = factory.Faker("text")


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = models.Comment

    body = factory.Faker("text")
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)


class ReactionFactory(DjangoModelFactory):
    class Meta:
        model = models.Reaction

    value = models.Reaction.Values.SMILE
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)


class ChatFactory(DjangoModelFactory):
    class Meta:
        model = models.Chat

    user_1 = factory.SubFactory(UserFactory)
    user_2 = factory.SubFactory(UserFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = models.Messages

    content = factory.Faker("text")
    chat = factory.LazyAttribute(lambda obj: ChatFactory(user_1=obj.author))
    author = factory.SubFactory(UserFactory)