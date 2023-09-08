from rest_framework import status
from rest_framework.test import APITestCase
from general.factories import UserFactory

from general.models import Post, Reaction


class PostTestCase(APITestCase):

    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/posts/"

    def test_create_post(self):

        data = {
            "title": "my_title",
            "body": "test_body"
        }

        response = self.client.post(path=self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.last()

        self.assertEqual(post.author, self.user)
        self.assertEqual(post.title, data["title"])
        self.assertEqual(post.body, data["body"])
        self.assertIsNotNone(post.created_at)

