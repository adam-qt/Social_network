from rest_framework import status
from rest_framework.test import APITestCase
from general.factories import UserFactory, PostFactory, MessageFactory, ChatFactory
from django.contrib.auth.hashers import check_password
from general.models import User


class UserTestCase(APITestCase):

    def setUp(self):

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/users/'

    def test_user_list(self):
        UserFactory.create_batch(20)
        response = self.client.get(path=self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 21)

    def test_user_structure_response(self):
        response = self.client.get(path=self.url, format='json')
        expected_data = {
            'id': self.user.pk,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_friend': False
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertDictEqual(response.data["results"][0], expected_data)

    def test_is_friend(self):
        user_2 = UserFactory()
        UserFactory()
        self.user.friends.add(user_2)
        self.user.save()

        with self.assertNumQueries(3):
            response = self.client.get(path=self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue(response.data["results"][1]['is_friend'])
        self.assertFalse(response.data["results"][2]["is_friend"])

    def test_correct_registration(self):
        """
        [post]
        /api/users/
        """
        self.client.logout()

        data = {
            'username': 'Aishe',
            'password': 'Hidaet1217Qt_',
            'email': 'jij@gmail.com',
            'first_name': 'h43423',
            'last_name': 'dfsdfsd'
        }

        response = self.client.post(path=self.url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.last()

        self.assertTrue(
            check_password(
                data["password"],
                created_user.password))
        data.pop('password')

        created_user_data = {
            'username': created_user.username,
            'email': created_user.email,
            'first_name': created_user.first_name,
            'last_name': created_user.last_name
        }

        self.assertDictEqual(created_user_data, data)

    def test_to_try_create_existing_username(self):
        """
        [post]
        /api/users/
        """
        self.client.logout()

        user = {
            'username': self.user.username,
            'email': 'random@gmail.com',
            'first_name': 'Elbrus',
            'last_name': 'Johnson',
            'password': '1234'
        }
        response = self.client.post(path=self.url, data=user, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), 1)

    def test_user_add_friend(self):
        """
        [post]
        /api/users/{pk}/add
        """
        friend = UserFactory()
        url = f"{self.url}{friend.pk}/add/"

        response = self.client.post(path=url, format='json')

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(friend in self.user.friends.all())

    def test_delete_user_from_friend_list(self):
        """
        [post]
        '/api/users/{pk}/delete'
        """
        friend = UserFactory()
        self.user.friends.add(friend)
        self.user.save()
        url = f"{self.url}{friend.pk}/delete/"

        self.assertTrue(friend in self.user.friends.all())

        response = self.client.post(path=url, format='json')

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(friend in self.user.friends.all())

    def test_retrieve_user(self):
        """
        [get]
        /api/users/{pk}
        """
        user = UserFactory()

        url = f"{self.url}{user.pk}/"

        friend_1 = UserFactory()
        friend_2 = UserFactory()
        not_friend_1 = UserFactory()
        not_friend_2 = UserFactory()

        post_1 = PostFactory(author=user)
        post_2 = PostFactory(author=user)

        user.friends.add(friend_1, friend_2)
        response = self.client.get(path=url, format='json')

        expected_data = {"id": user.pk,
                         "username": user.username,
                         "email": user.email,
                         "first_name": user.first_name,
                         "last_name": user.last_name,
                         "is_friend": False,
                         "friend_count": 2,
                         "posts": [{"id": post_1.pk,
                                    "body": post_1.body,
                                    "created_at": post_1.created_at.strftime("%Y-%b-%dT%H:%M:%S"),
                                    "title": post_1.title},
                                   {"id": post_2.pk,
                                    "body": post_2.body,
                                    "created_at": post_2.created_at.strftime("%Y-%b-%dT%H:%M:%S"),
                                    "title": post_2.title}],
                         "friends": [{"id": friend_1.pk,
                                      "username": friend_1.username},
                                     {"id": friend_2.pk,
                                      "username": friend_2.username}]}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected_data)

    def test_friends_list(self):
        """
        [get]
        api/users/{pk}/friends
        """

        user = UserFactory()
        url = f"{self.url}{user.pk}/friends/"
        friend_1 = UserFactory()
        friend_2 = UserFactory()
        UserFactory()
        UserFactory()
        friend_2.friends.add(user)
        user.friends.add(friend_1)

        self.user.friends.add(friend_1)
        user.save()
        friend_2.save()
        self.assertTrue(user in friend_1.friends.all())
        self.assertTrue(friend_2 in user.friends.all())

        response = self.client.get(path=url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        expected_data = {"results": [
            {
                "id": friend_2.pk,
                "username": friend_2.username,
                "first_name": friend_2.first_name,
                "last_name": friend_2.last_name,
                "is_friend": friend_2 in self.user.friends.all()},
            {
                "id": friend_1.pk,
                "username": friend_1.username,
                "first_name": friend_1.first_name,
                "last_name": friend_1.last_name,
                "is_friend": friend_1 in self.user.friends.all()
            }
        ]}

        self.assertDictEqual(expected_data,
                             {"results": response.data["results"]})

    def test_myself(self):
        """
        [get]
        /api/users/myself/
        """

        url = f"{self.url}myself/"
        user = UserFactory()
        self.client.force_authenticate(user=user)

        friend_1 = UserFactory()
        friend_2 = UserFactory()
        not_friend_1 = UserFactory()
        not_friend_2 = UserFactory()

        post_1 = PostFactory(author=user)
        post_2 = PostFactory(author=user)

        user.friends.add(friend_1, friend_2)
        response = self.client.get(path=url, format='json')

        expected_data = {"id": user.pk,
                         "username": user.username,
                         "email": user.email,
                         "first_name": user.first_name,
                         "last_name": user.last_name,
                         "is_friend": False,
                         "friend_count": 2,
                         "posts": [{"id": post_1.pk,
                                    "body": post_1.body,
                                    "created_at": post_1.created_at.strftime("%Y-%b-%dT%H:%M:%S"),
                                    "title": post_1.title},
                                   {"id": post_2.pk,
                                    "body": post_2.body,
                                    "created_at": post_2.created_at.strftime("%Y-%b-%dT%H:%M:%S"),
                                    "title": post_2.title}],
                         "friends": [{"id": friend_1.pk,
                                      "username": friend_1.username},
                                     {"id": friend_2.pk,
                                      "username": friend_2.username}]}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected_data)
