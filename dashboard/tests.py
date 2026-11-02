from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from dashboard.models import PriceAlert, Share, Watchlist
from dashboard.services.alerts import check_price_alerts


class DashboardTests(APITestCase):
    def setUp(self) -> None:
        self.apple_share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
            last_price=100.50,
            is_trend_high=True,
        )

        self.second_company = {
            "figi": "BBG000B9XRY5",
            "isin": "US0378331004",
            "name": "Company_test",
            "ticker": "TESTTEST",
            "currency": "usd",
            "uid": "a9eb4238-eba9-488c-b102-b6140fd08e39",
            "last_price": 1.50,
            "is_trend_high": False,
        }

    def test_share_list_html(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_list(self):
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        apple_share = response.json().get("results")[0]
        self.assertEqual(apple_share["id"], self.apple_share.id)
        self.assertEqual(apple_share["figi"], self.apple_share.figi)
        self.assertEqual(apple_share["isin"], self.apple_share.isin)
        self.assertEqual(apple_share["name"], self.apple_share.name)
        self.assertEqual(apple_share["ticker"], self.apple_share.ticker)
        self.assertEqual(apple_share["currency"], self.apple_share.currency)

    def test_share_detail(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.get(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_detail_invalid(self):
        response = self.client.get("/api/v1/shares/2/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_share_update(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "id": share_detail["id"],
                "figi": self.apple_share.figi,
                "isin": self.apple_share.isin,
                "name": f"{self.apple_share.name}_test",
                "ticker": self.apple_share.ticker,
                "currency": self.apple_share.currency,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["figi"], self.apple_share.figi)
        self.assertEqual(body["name"], f"{self.apple_share.name}_test")

    def test_share_update_invalid(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "figi": self.apple_share.figi,
                "name": f"{self.apple_share.name}_test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_share_create(self):
        response = self.client.post(
            "/api/v1/shares/", self.second_company, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["figi"], self.second_company["figi"])
        self.assertEqual(body["name"], self.second_company["name"])
        self.assertEqual(body["ticker"], self.second_company["ticker"])

        response = self.client.get("/api/v1/shares/")
        self.assertEqual(len(response.data["results"]), 2)

    def test_share_create_invalid(self):
        response = self.client.post(
            "/api/v1/shares/", {"figi": "BBG000B9XRY5"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_share_delete(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.delete(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_share_delete_invalid(self):
        response = self.client.delete("/api/v1/shares/3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MonitoringTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
        )
        self.share = Share.objects.create(
            figi="BBG000B9XRY6",
            isin="US0378331006",
            name="Test company",
            ticker="TEST",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e40",
            last_price=160.0,
        )

    def test_watchlist_duplicate_web(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:watchlist_add")

        first = self.client.post(url, {"share": self.share.pk})
        second = self.client.post(url, {"share": self.share.pk})

        self.assertEqual(first.status_code, status.HTTP_302_FOUND)
        self.assertEqual(second.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            Watchlist.objects.filter(user=self.user, share=self.share).count(),
            1,
        )

    def test_watchlist_duplicate_api(self):
        self.client.force_login(self.user)
        url = "/api/v1/watchlist/"

        first = self.client.post(url, {"share_id": self.share.pk}, format="json")
        second = self.client.post(url, {"share_id": self.share.pk}, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Watchlist.objects.filter(user=self.user, share=self.share).count(),
            1,
        )

    def test_alert_triggers_only_once(self):
        alert = PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            target_price=150.0,
            condition=PriceAlert.ABOVE,
        )

        check_price_alerts()
        alert.refresh_from_db()
        self.assertTrue(alert.triggered)
        first_triggered_at = alert.triggered_at

        check_price_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.triggered_at, first_triggered_at)

    def test_alert_api_isolation(self):
        alert = PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            target_price=150.0,
            condition=PriceAlert.ABOVE,
        )
        self.client.force_login(self.other_user)

        response = self.client.get("/api/v1/alerts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        response = self.client.delete(f"/api/v1/alerts/{alert.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_monitoring_pages_render(self):
        self.client.force_login(self.user)
        Watchlist.objects.create(user=self.user, share=self.share)
        PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            target_price=150.0,
            condition=PriceAlert.ABOVE,
        )

        for url_name in ("dashboard:watchlist", "dashboard:alerts"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_triggered_alert_banner(self):
        PriceAlert.objects.create(
            user=self.user,
            share=self.share,
            target_price=150.0,
            condition=PriceAlert.ABOVE,
            triggered=True,
            triggered_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, "Сработавших уведомлений")

    def test_login_required_redirects_to_user_login(self):
        response = self.client.get(reverse("dashboard:watchlist"))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/user/login/", response.url)

        login_page = self.client.get(response.url)
        self.assertEqual(login_page.status_code, status.HTTP_200_OK)

    def test_alert_target_price_validation_web(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard:alert_add"),
            {
                "share": self.share.pk,
                "target_price": "0",
                "condition": PriceAlert.ABOVE,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PriceAlert.objects.count(), 0)

    def test_alert_target_price_validation_api(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/v1/alerts/",
            {
                "share_id": self.share.pk,
                "target_price": 0,
                "condition": PriceAlert.ABOVE,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
