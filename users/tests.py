from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
import io
from PIL import Image

User = get_user_model()

def generate_test_image():
    file = io.BytesIO()
    image = Image.new('RGBA', size=(100, 100), color=(255, 0, 0))
    image.save(file, 'png')
    file.seek(0)
    return SimpleUploadedFile('test_avatar.png', file.read(), content_type='image/png')

class UserAvatarTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='pedro_test',
            email='pedro@example.com',
            password='Password123!'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'pedro_test')
        self.assertIsNone(response.data['avatar'])

    def test_upload_avatar_multipart(self):
        avatar_file = generate_test_image()
        response = self.client.patch(
            '/api/users/me/',
            {'avatar': avatar_file, 'bio': 'Bio atualizada com foto'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['avatar'])
        self.assertIn('/media/avatars/test_avatar', response.data['avatar'])
        self.assertEqual(response.data['bio'], 'Bio atualizada com foto')

        # Atualiza instância e retesta GET
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

        get_response = self.client.get('/api/users/me/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(get_response.data['avatar'])
        self.assertTrue(
            get_response.data['avatar'].startswith('http://') or
            get_response.data['avatar'].startswith('https://') or
            get_response.data['avatar'].startswith('/media/')
        )

