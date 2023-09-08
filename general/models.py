from django.db import models
from django.db.models import functions, F
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    friends = models.ManyToManyField(
        to='self',
        symmetrical=True,
        blank=True
    )

    def __str__(self):
        return self.username


class Post(models.Model):
    title = models.CharField(max_length=64)
    author = models.ForeignKey(to=User,
                               related_name='posts',
                               on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    body = models.TextField()
    author = models.ForeignKey(to=User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    post = models.ForeignKey(to=Post,
                             on_delete=models.CASCADE,
                             related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author}-{self.post}'


class Reaction(models.Model):
    class Values(models.TextChoices):
        SMILE = 'smile', 'улыбка'
        THUMB_UP = 'thumb_up' , 'палец вверх'
        SAD = 'sad', 'грустный',
        HEART = 'heart', 'сердце'
        LAUGH = 'laugh', 'смех'

    value = models.CharField(max_length=8, choices=Values.choices, null=True)
    author = models.ForeignKey(to=User, related_name='reactions', on_delete=models.CASCADE)
    post = models.ForeignKey(to=Post, related_name='reactions', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                'author',
                'post',
                name='author_post_unique'
            ),
        ]

    def __str__(self):
        return self.value


class Chat(models.Model):
    user_1 = models.ForeignKey(to=User, related_name='chats_as_user1', on_delete=models.CASCADE)
    user_2 = models.ForeignKey(to=User, related_name='chats_as_user2', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                functions.Greatest(F('user_1'), F('user_2')),
                functions.Least(F('user_1'), F('user_2')),
                name="users_chat_unique",
            ),
        ]


class Messages(models.Model):
    content = models.TextField()
    chat = models.ForeignKey( to=Chat, related_name='messages', on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, related_name='messages', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
