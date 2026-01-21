import os
import os
from app import app, db, User

# Start a thread for the server? No, we can verify by using the test client
# Flask has a built-in test client
import unittest
from io import BytesIO

class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_sharanu_app.db' # Use separate DB for tests
        self.app = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

    def test_signup_login_flow(self):
        # Signup
        response = self.app.post('/signup', data=dict(
            username='testuser',
            email='test@example.com',
            password='Password@123',
            confirm_password='Password@123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # self.assertIn(b'Dashboard', response.data) # Changed logic
        self.assertIn(b'Signup successful', response.data)

        # Logout - Not needed if we are not logged in, but let's check login flow
        # self.app.get('/logout', follow_redirects=True) 

        # Login
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='Password@123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Batch Mfg', response.data)
        self.assertIn(b'Anchemco India Private Limited', response.data)

    def test_data_entry(self):
        # Register and Login first
        self.app.post('/signup', data=dict(
            username='testuser',
            email='test@example.com',
            password='Password@123',
            confirm_password='Password@123'
        ), follow_redirects=True)

        # Must login now
        self.app.post('/login', data=dict(
            username='testuser',
            password='Password@123'
        ), follow_redirects=True)

        # Save Entry
        response = self.app.post('/save_entry', data=dict(
            authorised_person='John Doe',
            employee_id='EMP001',
            final_batch_number='BATCH100',
            batch_quantity='1000 Liters',
            urea_percentage='45.5',
            density='1.2',
            photo=(BytesIO(b'fakeimage'), 'test.jpg')
        ), follow_redirects=True, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Entry saved successfully!', response.data)

        # Check Dashboard listing
        response = self.app.get('/dashboard')
        # self.assertIn(b'Anchemco India Private Limited', response.data) # Removed as not displayed
        self.assertIn(b'BATCH100', response.data)
        self.assertIn(b'1000 Liters', response.data)
        self.assertIn(b'SF AdBlue', response.data)

        # Get the entry ID to delete (assuming it's ID 1 since we clear DB)
        # Verify Delete
        response = self.app.get('/delete_entry/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Entry deleted successfully', response.data)
        self.assertNotIn(b'BATCH100', response.data)


if __name__ == "__main__":
    unittest.main()
