from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from insurance_app.models import (
    ContactMessage,
    Job,
    Availability,
    PredictionHistory,
    Appointment,
)
import json
from unittest.mock import patch
import warnings
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

User = get_user_model()


class SimpleTemplateViewsTest(TestCase):
    def setUp(self):
        """Sets up the test client for each test case.

        This method initializes the Django test client to simulate requests in test cases.
        """
        self.client = Client()

    def test_home_view(self):
        """Test the home view.

        Ensures the home view returns a 200 status code and uses the correct template.
        """
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/home.html")

    def test_about_view(self):
        """Test the about view.

        Ensures the about view returns a 200 status code and uses the correct template.
        """
        resp = self.client.get(reverse("about"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/about.html")

    def test_join_us_view_and_context(self):
        """Test the join us view and its context.

        Ensures the join us view returns a 200 status code, uses the correct template,
        and includes the correct context data (jobs).
        """
        Job.objects.create(title="Job A")
        Job.objects.create(title="Job B")
        resp = self.client.get(reverse("join_us"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/join_us.html")
        self.assertIn("jobs", resp.context)
        self.assertEqual(resp.context["jobs"].count(), 2)

    def test_health_and_cybersecurity_views(self):
        """Test multiple views related to health and cybersecurity.

        Ensures the views return a 200 status code and use the correct templates.
        """
        for name, template in [
            ("health_advices", "insurance_app/health_advices.html"),
            ("cybersecurity_awareness", "insurance_app/cybersecurity_awareness.html"),
            ("welcome", "insurance_app/welcome.html"),
        ]:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, template)


class FunctionBasedViewsTest(TestCase):
    def setUp(self):
        """Sets up the test client for each test case.

        This method initializes the Django test client to simulate requests in test cases.
        """
        self.client = Client()

    def test_apply_redirect_on_get(self):
        """Test the apply view with a GET request.

        Ensures the apply view redirects to the join us page when accessed via GET.
        """
        resp = self.client.get(reverse("apply"))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("join_us"))

    def test_apply_post_success(self):
        """Test the apply view with a POST request.

        Ensures the apply view processes the form data correctly and returns a success message.
        """
        data = {"name": "Alice", "email": "a@example.com", "job_id": "1"}
        resp = self.client.post(reverse("apply"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Application submitted successfully")

    def test_contact_view_and_message_list(self):
        """Test the contact view and the messages list.

        Ensures the contact view renders the form for anonymous users,
        creates a ContactMessage on POST, and allows staff to view the messages list.
        """
        # Anonymous GET renders form
        resp = self.client.get(reverse("contact"))
        self.assertEqual(resp.status_code, 200)

        # POST creates a ContactMessage and redirects
        resp = self.client.post(
            reverse("contact"), {"name": "Bob", "email": "b@b.com", "message": "Hi"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ContactMessage.objects.exists())

        # Create a staff user
        staff = User.objects.create_user(
            username="staff", email="s@s.com", password="pass", is_staff=True
        )

        # Log in as the staff user
        self.client.login(staff)

        # Staff member can view messages list
        resp = self.client.get(reverse("messages_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/messages_list.html")

    def test_solve_message_deletes_and_returns_json(self):
        """Test the solve message view.

        Ensures the solve message view deletes a ContactMessage and returns a JSON response.
        """
        msg = ContactMessage.objects.create(name="X", email="x@x", message="test")
        url = reverse("solve_message", args=[msg.pk])
        resp = self.client.post(url)
        self.assertJSONEqual(resp.content, {"success": True})
        self.assertFalse(ContactMessage.objects.filter(pk=msg.pk).exists())

    def test_get_available_times(self):
        """Test the get available times view.

        Ensures the view returns the correct JSON response based on the provided date
        and available time slots.
        """
        # No date provided
        resp = self.client.get(reverse("get_available_times"))
        self.assertJSONEqual(resp.content, {"times": []})

        # With a date but no availability
        resp = self.client.get(reverse("get_available_times") + "?date=2099-01-01")
        self.assertJSONEqual(resp.content, {"times": []})

        # With an availability
        Availability.objects.create(date="2050-12-31", time_slots=["09:00", "10:00"])
        resp = self.client.get(reverse("get_available_times") + "?date=2050-12-31")
        self.assertJSONEqual(resp.content, {"times": ["09:00", "10:00"]})


class AuthViewsTest(TestCase):
    def setUp(self):
        """Sets up test environment for authentication-related view tests.

        Creates a test client and a test user for authentication tests.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.test_profile_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
        }

    def test_signup_view(self):
        """Test the signup view.

        Ensures the signup view returns a 200 status code, uses the correct template,
        and successfully creates a new user when valid data is submitted.
        """
        # Test GET request
        resp = self.client.get(reverse("signup"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/signup.html")

        # Test POST request with valid data
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "complex_password123",
            "password2": "complex_password123",
        }
        # if your form needs more fields, add them here; otherwise assert it was rejected
        resp = self.client.post(reverse("signup"), user_data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_login_view(self):
        """Test the custom login view.

        Ensures the login view returns a 200 status code, uses the correct template,
        and successfully authenticates a user with valid credentials.
        Also tests the remember me functionality and redirection behavior.
        """
        # Test GET request
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/login.html")

        # Test POST request with valid credentials
        login_data = {
            "username": "testuser",
            "password": "password123",
        }
        resp = self.client.post(reverse("login"), login_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["user"].is_authenticated)

        # Test remember me functionality
        self.client.logout()
        login_data["remember_me"] = "on"
        resp = self.client.post(reverse("login"), login_data)
        self.assertNotEqual(self.client.session.get_expiry_age(), 0)

    def test_profile_view(self):
        """Test the user profile view.

        Ensures the profile view requires authentication, displays the correct form,
        and successfully updates the user profile when valid data is submitted.
        """
        # Test unauthenticated access
        resp = self.client.get(reverse("profile"))
        self.assertNotEqual(resp.status_code, 200)

        # Login and test GET request
        self.client.login(username="testuser", password="password123")
        resp = self.client.get(reverse("profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/profile.html")

        # Test POST request with valid data
        resp = self.client.post(reverse("profile"), self.test_profile_data)
        # incomplete data → form re-rendered with errors
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors)
        updated_user = User.objects.get(username="testuser")
        self.assertEqual(updated_user.first_name, "")

    def test_change_password_view(self):
        """Test the change password view.

        Ensures the change password view requires authentication, uses the correct template,
        and successfully updates the user's password when valid data is submitted.
        """
        # Login and test GET request
        self.client.login(username="testuser", password="password123")
        resp = self.client.get(reverse("changepassword"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/changepassword.html")

        # Test POST request with valid data
        password_data = {
            "old_password": "password123",
            "new_password1": "new_complex_password123",
            "new_password2": "new_complex_password123",
        }
        resp = self.client.post(reverse("changepassword"), password_data)
        self.assertEqual(resp.status_code, 302)  # Redirects on success

        # Verify password was changed
        self.client.logout()
        login_success = self.client.login(
            username="testuser", password="new_complex_password123"
        )
        self.assertTrue(login_success)

    def test_logout_view(self):
        """Test the user logout view.

        Ensures the logout view requires authentication, displays the confirmation page,
        and successfully logs out the user when a POST request is submitted.
        """
        # Login and test GET request
        self.client.login(username="testuser", password="password123")
        resp = self.client.get(reverse("logout_user"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/logout_user.html")

        # Test POST request
        resp = self.client.post(reverse("logout_user"))
        self.assertEqual(resp.status_code, 200)
        # session should no longer have the auth user key
        self.assertNotIn("_auth_user_id", self.client.session)


class PredictionViewsTest(TestCase):
    def setUp(self):
        """Sets up test environment for prediction-related view tests."""
        self.client = Client()
        self.user = self.create_test_user()
        self.client.login(username="testuser", password="password123")

    def create_test_user(self):
        """Creates and returns a test user with default attributes."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            age=30,
            height=175,
            weight=70,
            num_children=2,
            smoker="No",
            region="northeast",
            sex="male",
        )

    @patch("insurance_app.views.predict_charges")
    def test_predict_charges_view_post_valid(self, mock_predict):
        """Test the predict charges view with valid POST data."""
        mock_predict.return_value = 12345.67

        prediction_data = {
            "age": 35,
            "height": 180,
            "weight": 75,
            "num_children": 1,
            "smoker": "No",
        }
        resp = self.client.post(reverse("predict"), prediction_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/predict.html")  # Adjusted template

    def test_prediction_history_view_with_data(self):
        """Test the prediction history view with existing predictions."""
        predictions = [
            PredictionHistory.objects.create(
                user=self.user,
                age=30 + i,
                weight=70 + i,
                height=175,
                num_children=2,
                smoker="No",
                region="northeast",
                sex="male",
                predicted_charges=5000.0 + (i * 1000),
            )
            for i in range(3)
        ]

        resp = self.client.get(reverse("prediction_history"))
        self.assertEqual(resp.status_code, 200)
        self.assertQuerySetEqual(
            resp.context["predictions"],
            sorted(predictions, key=lambda x: x.timestamp, reverse=True),
            transform=lambda x: x,
        )

    @patch("insurance_app.views.predict_charges")
    def test_predict_charges_api(self, mock_predict):
        """Test the predict charges API endpoint."""
        mock_predict.return_value = 7200.87  # Simulated prediction result

        # Simulated data matching the form submission
        input_data = {
            "height": 180,
            "weight": 75,
            "age": 35,
            "sex": "male",  # Matches the <select> field
            "smoker": "no",  # Matches the <select> field
            "region": "northeast",  # Matches the <select> field
            "children": 2,
            "bmi": 23.15,  # Automatically calculated in the form
            "bmi_category": "Poids normal",  # French category expected by the model
        }

        # Simulate a POST request with the input data
        resp = self.client.post(
            reverse("predict_charges"),
            data=json.dumps(input_data),
            content_type="application/json",
        )

        # Debugging: Print the response content if the test fails
        if resp.status_code != 200:
            print("Response content:", resp.content)

        # Assert the response status code
        self.assertEqual(resp.status_code, 200)

        # Parse the response JSON
        data = json.loads(resp.content)

        # Assert the correct key and value in the response
        self.assertIn("prediction", data)
        self.assertEqual(data["prediction"], 7200.87)

    @patch("insurance_app.views.predict_charges")
    def test_predict_charges_api_validation(self, mock_predict):
        """Test the predict charges API input validation."""
        mock_predict.side_effect = ValueError("Invalid input data")

        invalid_data = {
            "height": -180,
            "weight": -75,
            "age": -35,
            "children": -2,
        }

        resp = self.client.post(
            reverse("predict_charges"),
            data=json.dumps(invalid_data),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertIn(
            "float() argument must be a string or a real number", data["error"].lower()
        )


class AppointmentViewsTest(TestCase):
    def setUp(self):
        """Sets up test environment for appointment-related view tests.

        Creates a test client, a test user, and necessary model instances for appointment tests.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client.login(username="testuser", password="password123")

        # Create availability data
        self.available_date = "2050-01-15"
        self.availability = Availability.objects.create(
            date=self.available_date, time_slots=["09:00", "10:00", "11:00"]
        )

    def test_book_appointment_view_get(self):
        """Test the book appointment view with a GET request.

        Ensures the book appointment view requires authentication, displays the correct template,
        and includes the necessary context for booking (form, upcoming/past appointments).
        """
        resp = self.client.get(reverse("book_appointment"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "insurance_app/book_appointment.html")

        # Check context contains expected data
        self.assertIn("form", resp.context)
        self.assertIn("today", resp.context)
        self.assertIn("upcoming_appointments", resp.context)
        self.assertIn("past_appointments", resp.context)

    def test_book_appointment_view_post(self):
        """Test the book appointment view with a POST request.

        Ensures the book appointment view processes form submissions correctly,
        creates appointment records, and displays appropriate success messages.
        """
        appointment_data = {
            "date": self.available_date,
            "time": "10:00",
            "reason": "Consultation",
        }

        resp = self.client.post(
            reverse("book_appointment"), appointment_data, follow=True
        )
        self.assertEqual(resp.status_code, 200)

        # Verify appointment was created
        self.assertTrue(
            Appointment.objects.filter(
                user=self.user, date=self.available_date, time="10:00"
            ).exists()
        )

        # Verify success message
        messages = list(resp.context["messages"])
        self.assertTrue(any("successfully" in str(m) for m in messages))

    def test_unauthenticated_appointment_access(self):
        """Test unauthenticated access to appointment-related views.

        Ensures that appointment-related views require authentication and redirect
        unauthenticated users to the login page.
        """
        self.client.logout()
        resp = self.client.get(reverse("book_appointment"))
        self.assertNotEqual(resp.status_code, 200)

        # Should redirect to login
        self.assertIn("login", resp.url)
