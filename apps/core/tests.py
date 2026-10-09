from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ScrapeJob, ScrapedRecord
from .services.scraping.extractors.generic import extract_page
from .services.scraping.validators import validate_url
from .services.scraping.exceptions import UnsafeURLError


class ScrapingExtractionTests(TestCase):
    def test_json_ld_product_is_extracted(self):
        html = '''<html lang="en"><head><title>Example</title><script type="application/ld+json">{"@type":"Product","name":"Widget","offers":{"price":"19.99","priceCurrency":"USD","availability":"InStock"}}</script></head><body><h1>Widget</h1><main><p>A useful product description with enough text.</p></main></body></html>'''
        result = extract_page(html, "https://example.com/product", "beautifulsoup")
        self.assertEqual(result["record_type"], "product")
        self.assertEqual(result["records"][0]["attributes"]["price"], "19.99")
        self.assertEqual(result["records"][0]["attributes"]["currency"], "USD")

    def test_generic_page_is_extracted(self):
        result = extract_page("<html><head><title>Hello</title></head><body><main><h1>Hello</h1><p>Useful content.</p></main></body></html>", "https://example.com", "beautifulsoup")
        self.assertEqual(result["record_type"], "page")
        self.assertTrue(result["content"])


class SSRFTests(TestCase):
    @patch("apps.core.services.scraping.validators.url.socket.getaddrinfo", return_value=[(2, 0, 6, "", ("127.0.0.1", 0))])
    def test_private_resolution_is_blocked(self, _mock):
        with self.assertRaises(UnsafeURLError):
            validate_url("http://example.com")

    def test_localhost_is_blocked(self):
        with self.assertRaises(UnsafeURLError):
            validate_url("http://localhost:8000")


class OwnershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="StrongPassword123")
        self.other = User.objects.create_user(username="other", password="StrongPassword123")
        self.job = ScrapeJob.objects.create(user=self.user, name="Owned", url="https://example.com")
        self.record = ScrapedRecord.objects.create(job=self.job, title="Private", content_hash="a" * 64)

    def test_other_user_cannot_open_job(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("job_detail", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_open_record(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("record_detail", args=[self.record.pk]))
        self.assertEqual(response.status_code, 200)
