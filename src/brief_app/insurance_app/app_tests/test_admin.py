from django.test import TestCase
from django.contrib.admin.sites import site
from insurance_app.models import Job, ContactMessage, Availability, Appointment
from insurance_app.admin import (
    JobAdmin,
    ContactMessageAdmin,
    AvailabilityAdmin,
    AppointmentAdmin,
)
from insurance_app.admin import AvailabilityAdminForm


class AdminSiteTest(TestCase):
    def test_job_admin_registered(self):
        # Ensure the Job model is registered with the correct admin class
        self.assertIn(Job, site._registry)
        self.assertIsInstance(site._registry[Job], JobAdmin)

    def test_contact_message_admin_registered(self):
        # Ensure the ContactMessage model is registered with the correct admin class
        self.assertIn(ContactMessage, site._registry)
        self.assertIsInstance(site._registry[ContactMessage], ContactMessageAdmin)

    def test_availability_admin_registered(self):
        # Ensure the Availability model is registered with the correct admin class
        self.assertIn(Availability, site._registry)
        self.assertIsInstance(site._registry[Availability], AvailabilityAdmin)

    def test_appointment_admin_registered(self):
        # Ensure the Appointment model is registered with the correct admin class
        self.assertIn(Appointment, site._registry)
        self.assertIsInstance(site._registry[Appointment], AppointmentAdmin)

    def test_display_times_method(self):
        # Test the display_times method in AvailabilityAdmin
        availability = Availability.objects.create(
            date="2025-05-13", time_slots=["09:00", "10:00"]
        )
        admin_instance = AvailabilityAdmin(Availability, site)
        self.assertEqual(admin_instance.display_times(availability), "09:00, 10:00")


class TestAvailabilityAdminFormCleanTimeSlots(TestCase):

    def test_clean_time_slots_happy_path_multiple(self):
        # Arrange
        form = AvailabilityAdminForm(
            data={"date": "2025-05-13", "time_slots": ["09:00", "10:00", "11:00"]}
        )
        self.assertTrue(form.is_valid())

        # Act
        result = form.clean_time_slots()

        # Assert
        self.assertEqual(result, ["09:00", "10:00", "11:00"])

    def test_clean_time_slots_happy_path_empty_list(self):
        self.extracted_from_test_clean_time_slots_error_missing_time_slots()

    def test_clean_time_slots_happy_path_single(self):
        # Arrange
        form = AvailabilityAdminForm(
            data={"date": "2025-05-13", "time_slots": ["15:00"]}
        )
        self.assertTrue(form.is_valid())

        # Act
        result = form.clean_time_slots()

        # Assert
        self.assertEqual(result, ["15:00"])

    def test_clean_time_slots_error_missing_time_slots(self):
        self.extracted_from_test_clean_time_slots_error_missing_time_slots()

    def extracted_from_test_clean_time_slots_error_missing_time_slots(self):
        form = AvailabilityAdminForm(data={"date": "2025-05-13"})
        self.assertFalse(form.is_valid())
        with self.assertRaises(KeyError):
            form.clean_time_slots()

    def test_clean_time_slots_edge_case_none_value(self):
        # Arrange
        # Simulate a form with cleaned_data['time_slots'] = None
        form = AvailabilityAdminForm(data={"date": "2025-05-13", "time_slots": None})
        # Bypass is_valid to directly set cleaned_data
        form.cleaned_data = {"time_slots": None}

        # Act
        result = form.clean_time_slots()

        # Assert
        self.assertIsNone(result)
