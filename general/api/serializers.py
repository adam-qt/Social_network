import sys
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework.serializers import ModelSerializer, \
    SerializerMethodField, CurrentUserDefault, HiddenField, CharField, DateTimeField
from general.models import (User, Post, Comment, Reaction, Chat, Messages)

# User Serializers


class UserRegistrationSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('username',
                  'password',
                  'email',
                  'first_name',
                  'last_name')

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserListSerializer(ModelSerializer):
    is_friend = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_friend')

    def get_is_friend(self, obj) -> bool:
        current_user = self.context["request"].user
        return current_user in obj.friends.all()


class NestedPostSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = ["id",
                  "body",
                  "created_at",
                  "title"]


class NestedFriendsSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserRetrieveSerializer(ModelSerializer):
    is_friend = SerializerMethodField()
    friend_count = SerializerMethodField()
    posts = NestedPostSerializer(many=True)
    friends = NestedFriendsSerializer(many=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_friend',
            'friend_count',
            "posts",
            'friends'
        ]

    def get_is_friend(self, obj) -> bool:
        return obj in self.context['request'].user.friends.all()

    def get_friend_count(self, obj) -> int:
        return obj.friends.count()


# Post Serializers


class UserShortSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class PostListSerializer(ModelSerializer):
    author = UserShortSerializer()
    body = SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id',
                  'author',
                  'title',
                  'created_at',
                  'body')

    def get_body(self, obj) -> str:
        max_length = 60
        if len(obj.body) > max_length:
            return f'{obj.body[:57]}...'
        else:
            return obj.body


class NestedReactionsSerializer(ModelSerializer):
    author = UserShortSerializer()

    class Meta:
        model = Reaction
        fields = ('id', 'value', 'author')


class PostRetrieveSerializer(ModelSerializer):
    author = UserShortSerializer()
    my_reaction = SerializerMethodField()
    reactions = NestedReactionsSerializer(many=True)

    class Meta:
        model = Post
        fields = ('id',
                  'title',
                  'body',
                  'author',
                  'reactions',
                  'my_reaction')

    def get_my_reaction(self, obj):
        user = self.context['request'].user

        try:
            reaction = obj.reactions.get(author=user).value
        except Reaction.DoesNotExist:
            reaction = 'you have not react on this post'
        return reaction


class PostCreateUpdateSerializer(ModelSerializer):
    author = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Post
        fields = ('id',
                  'author',
                  'title',
                  'body')

# Comments Serializers


class CommentSerializer(ModelSerializer):
    author = HiddenField(
        default=CurrentUserDefault()
    )

    def get_fields(self):
        fields = super().get_fields()
        if self.context['request'].method == 'GET':
            fields['author'] = UserShortSerializer(read_only=True)
        return fields

    class Meta:
        model = Comment
        fields = ('id',
                  'body',
                  'created_at',
                  'post',
                  'author')

# Reaction Serializer


class ReactionSerializer(ModelSerializer):
    author = HiddenField(
        default=UserShortSerializer()
    )

    class Meta:
        model = Reaction
        fields = ('id',
                  'value',
                  'author',
                  'created_at',
                  'post')

    def create(self, validated_data):
        reaction = Reaction.objects.filter(author=validated_data['author'],
                                           post=validated_data['post']).last()
        if not reaction:
            Reaction.objects.create(**validated_data)
        if reaction.value == validated_data['value']:
            reaction.value = None
        else:
            reaction.value = validated_data['value']
        reaction.save()
        return reaction


class ChatSerializer(ModelSerializer):
    user_1 = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = Chat
        fields = ("user_1", "user_2")

    def create(self, validated_data):
        request_user = validated_data["user_1"]
        second_user = validated_data["user_2"]

        chat = Chat.objects.filter(
            Q(user_1=request_user, user_2=second_user)
            | Q(user_1=second_user, user_2=request_user)
        ).first()
        if not chat:
            chat = Chat.objects.create(
                user_1=request_user,
                user_2=second_user,
            )

        return chat


class MessageListSerializer(ModelSerializer):
    message_author = CharField()

    class Meta:
        model = Messages
        fields = ("id", "content", "message_author", "created_at")


class ChatListSerializer(ModelSerializer):
    companion_name = SerializerMethodField()
    last_message_content = SerializerMethodField()
    last_message_datetime = DateTimeField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "companion_name",
            "last_message_content",
            "last_message_datetime",
        )

    def get_last_message_content(self, obj) -> str:
        return obj.last_message_content

    def get_companion_name(self, obj) -> str:
        companion = obj.user_1 if obj.user_2 == self.context["request"].user else obj.user_2
        return f"{companion.first_name} {companion.last_name}"


class MessageSerializer(ModelSerializer):
    author = HiddenField(
        default=CurrentUserDefault(),
    )

    def validate(self, attrs):
        chat = attrs["chat"]
        author = attrs["author"]
        if chat.user_1 != author and chat.user_2 != author:
            raise ValidationError("Вы не являетесь участником этого чата.")
        return super().validate(attrs)

    class Meta:
        model = Messages
        fields = ("id", "author", "content", "chat", "created_at")


