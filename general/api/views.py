from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin,\
    RetrieveModelMixin, DestroyModelMixin
from .serializers import UserRegistrationSerializer, UserListSerializer, UserRetrieveSerializer, \
    PostListSerializer, PostCreateUpdateSerializer, PostRetrieveSerializer, CommentSerializer, \
    ReactionSerializer, ChatSerializer, MessageListSerializer, ChatListSerializer, MessageSerializer
from general.models import User, Post, Reaction, Comment, Messages, Chat
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from general.permissions import IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Case, When, Value, F, CharField, OuterRef, Subquery, Q


class UserViewSet(
        GenericViewSet,
        CreateModelMixin,
        ListModelMixin,
        RetrieveModelMixin):

    def get_queryset(self):
        queryset = User.objects.all().prefetch_related('friends').order_by('-id')
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action in ['retrieve', 'me']:
            return UserRetrieveSerializer
        return UserListSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = (AllowAny,)
        else:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='myself')
    def me(self, request):
        """
        method shows data of current user

        :param request:
        :return:
        """
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='friends')
    def friends(self, request, pk=None):
        """
        Method shows list of friends

        :param request:
        :param pk:
        :return:
        """
        user = self.get_object()
        queryset = self.filter_queryset(
            self.get_queryset().filter(friends=user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add')
    def add_to_friend_list(self, request, pk=None):
        """
        method allows you to add user to your friends list using id

        """
        user = self.get_object()
        request.user.friends.add(user)
        return Response(f'{user.username}  added to your friends')

    @action(detail=True, methods=['post'], url_path='delete')
    def remove_from_friend_list(self, request, pk=None):
        """
        method allows you to delete friend out of your friends list using id
        """
        user = self.get_object()
        request.user.friends.remove(user)
        return Response(f'{user.username} was deleted from your friends list')


class PostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.all().prefetch_related('reactions').order_by('id')
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return PostCreateUpdateSerializer
        elif self.action == 'list':
            return PostListSerializer
        else:
            return PostRetrieveSerializer

    def get_permissions(self):
        if self.action in ['update', 'destroy', 'partial_update']:
            self.permission_classes = (IsOwnerOrReadOnly,)
        return super().get_permissions()

    # def perform_destroy(self, instance):
    #     if instance.author != self.request.user:
    #         raise PermissionError('this is not your post')
    #     instance.delete()
    #
    # def perform_update(self, serializer):
    #     instance = self.get_object()
    #     if instance.author != self.request.user:
    #         raise PermissionError('this is not your post')
    #     serializer.save()


class CommentsViewSet(
        GenericViewSet,
        CreateModelMixin,
        ListModelMixin,
        DestroyModelMixin):
    queryset = Comment.objects.all().order_by('-id')
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('post__id',)

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionError('this action not allowed')
        instance.delete()


class ReactionViewSet(GenericViewSet, CreateModelMixin):
    queryset = Reaction.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ReactionSerializer


class ChatViewSet(
    CreateModelMixin,
    GenericViewSet, ListModelMixin, DestroyModelMixin
):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ChatListSerializer
        if self.action == "messages":
            return MessageListSerializer
        return ChatSerializer

    def get_queryset(self):
        user = self.request.user

        last_message_subquery = Messages.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]
        last_message_content_subquery = Messages.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('content')[:1]

        qs = Chat.objects.filter(
            Q(user_1=user) | Q(user_2=user),
            messages__isnull=False,
        ).annotate(
            last_message_datetime=Subquery(last_message_subquery),
            last_message_content=Subquery(last_message_content_subquery),
        ).select_related(
            "user_1",
            "user_2",
        ).order_by("-last_message_datetime").distinct()
        return qs

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        messages = self.get_object().messages.filter(chat__id=pk).annotate(
            message_author=Case(
                When(author=self.request.user, then=Value("Вы")),
                default=F("author__first_name"),
                output_field=CharField(),
            )
        ).order_by("-created_at")
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class MessageViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    queryset = Messages.objects.all().order_by("-id")

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого сообщения.")
        instance.delete()