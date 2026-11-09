# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test cases for the campaign settings write tools."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from google.ads.googleads.client import GoogleAdsClient
from google.auth.credentials import AnonymousCredentials

from ads_mcp.config import ToolsConfig
from ads_mcp.coordinator import initialize_and_mount_tools
from ads_mcp.tools import campaign_settings as cs

CID = "1234567890"


def _resp(*resource_names: str) -> MagicMock:
    resp = MagicMock()
    resp.results = [SimpleNamespace(resource_name=rn) for rn in resource_names]
    return resp


def _schedule_row(criterion_id, day, sh, eh, modifier=0.0):
    return SimpleNamespace(
        campaign_criterion=SimpleNamespace(
            criterion_id=criterion_id,
            bid_modifier=modifier,
            ad_schedule=SimpleNamespace(
                day_of_week=SimpleNamespace(name=day),
                start_hour=sh,
                start_minute=SimpleNamespace(name="ZERO"),
                end_hour=eh,
                end_minute=SimpleNamespace(name="ZERO"),
            ),
        )
    )


class TestCampaignSettings(unittest.TestCase):
    """Propose/confirm behaviour and request construction for each tool."""

    @classmethod
    def setUpClass(cls):
        cls.real_ga_client = GoogleAdsClient(
            credentials=AnonymousCredentials(),
            developer_token="fake-token",
            use_proto_plus=True,
        )

    def setUp(self):
        self.services: dict[str, MagicMock] = {}
        self.schedule_rows: list = []
        self.mock_client = MagicMock()

        def search(customer_id, query):
            if "campaign_criterion.type = 'AD_SCHEDULE'" in query:
                return list(self.schedule_rows)
            return []

        def get_service(name, **kwargs):
            if name not in self.services:
                svc = MagicMock()
                if name == "GoogleAdsService":
                    svc.search.side_effect = search
                self.services[name] = svc
            return self.services[name]

        self.mock_client.get_service.side_effect = get_service
        self.mock_client.get_type.side_effect = self.real_ga_client.get_type
        patcher = patch(
            "ads_mcp.utils.get_googleads_client", return_value=self.mock_client
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _propose_then_commit(self, fn, **kwargs):
        proposal = json.loads(fn(**kwargs))
        self.assertEqual(proposal["status"], "PROPOSED")
        result = fn(**kwargs, validate_only=False, checksum=proposal["checksum"])
        return proposal, result

    # ---- bidding --------------------------------------------------------

    def test_maximize_conversions_with_target_cpa(self):
        svc = self.mock_client.get_service("CampaignService")
        svc.mutate_campaigns.return_value = _resp(f"customers/{CID}/campaigns/5")
        proposal, result = self._propose_then_commit(
            cs.update_campaign_bidding,
            customer_id=CID,
            campaign_id="5",
            strategy="MAXIMIZE_CONVERSIONS",
            target_cpa=120,
        )
        fields = {i["field_readable"]: i["value_readable"] for i in proposal["change_items"]}
        self.assertEqual(fields["Target CPA"], "120.00")
        op = svc.mutate_campaigns.call_args.kwargs["request"].operations[0]
        self.assertEqual(op.update.maximize_conversions.target_cpa_micros, 120_000_000)
        self.assertEqual(
            list(op.update_mask.paths), ["maximize_conversions.target_cpa_micros"]
        )
        self.assertIn("Successfully updated 1", result)

    def test_remove_target_cpa(self):
        svc = self.mock_client.get_service("CampaignService")
        svc.mutate_campaigns.return_value = _resp(f"customers/{CID}/campaigns/5")
        proposal, _ = self._propose_then_commit(
            cs.update_campaign_bidding,
            customer_id=CID,
            campaign_id="5",
            strategy="MAXIMIZE_CONVERSIONS",
        )
        fields = {i["field_readable"]: i["value_readable"] for i in proposal["change_items"]}
        self.assertEqual(fields["Target CPA"], "none")
        op = svc.mutate_campaigns.call_args.kwargs["request"].operations[0]
        self.assertEqual(op.update.maximize_conversions.target_cpa_micros, 0)

    def test_maximize_conversion_value_with_roas(self):
        svc = self.mock_client.get_service("CampaignService")
        svc.mutate_campaigns.return_value = _resp(f"customers/{CID}/campaigns/5")
        self._propose_then_commit(
            cs.update_campaign_bidding,
            customer_id=CID,
            campaign_id="5",
            strategy="MAXIMIZE_CONVERSION_VALUE",
            target_roas=3.5,
        )
        op = svc.mutate_campaigns.call_args.kwargs["request"].operations[0]
        self.assertAlmostEqual(op.update.maximize_conversion_value.target_roas, 3.5)

    def test_bidding_rejects_mismatched_target(self):
        with self.assertRaises(ToolError):
            cs.update_campaign_bidding(
                customer_id=CID, campaign_id="5",
                strategy="MAXIMIZE_CONVERSIONS", target_roas=2,
            )
        with self.assertRaises(ToolError):
            cs.update_campaign_bidding(
                customer_id=CID, campaign_id="5",
                strategy="MAXIMIZE_CONVERSION_VALUE", target_cpa=50,
            )
        with self.assertRaises(ToolError):
            cs.update_campaign_bidding(
                customer_id=CID, campaign_id="5", strategy="MANUAL_CPC",
            )

    # ---- location targeting --------------------------------------------

    def test_location_targeting_presence(self):
        svc = self.mock_client.get_service("CampaignService")
        svc.mutate_campaigns.return_value = _resp(f"customers/{CID}/campaigns/5")
        self._propose_then_commit(
            cs.update_campaign_location_targeting,
            customer_id=CID,
            campaign_id="5",
            targeting_type="PRESENCE",
        )
        op = svc.mutate_campaigns.call_args.kwargs["request"].operations[0]
        self.assertEqual(
            op.update.geo_target_type_setting.positive_geo_target_type.name, "PRESENCE"
        )
        self.assertEqual(
            list(op.update_mask.paths),
            ["geo_target_type_setting.positive_geo_target_type"],
        )

    # ---- ad schedule ----------------------------------------------------

    def test_set_ad_schedule_replaces_existing(self):
        self.schedule_rows = [_schedule_row(111, "MONDAY", 0, 24)]
        svc = self.mock_client.get_service("CampaignCriterionService")
        windows = [
            {"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 20},
            {"day_of_week": "FRIDAY", "start_hour": 8, "start_minute": 30,
             "end_hour": 14, "bid_modifier": 0.8},
        ]
        proposal, result = self._propose_then_commit(
            cs.set_campaign_ad_schedule, customer_id=CID, campaign_id="5", windows=windows
        )
        ops = [i["operation"] for i in proposal["change_items"]]
        self.assertEqual(ops, ["REMOVE", "CREATE", "CREATE"])
        self.assertIn("FRIDAY 08:30-14:00 (bid x0.8)",
                      [i["value_readable"] for i in proposal["change_items"]])

        request = svc.mutate_campaign_criteria.call_args.kwargs["request"]
        self.assertFalse(request.validate_only)
        self.assertEqual(request.operations[0].remove,
                         f"customers/{CID}/campaignCriteria/5~111")
        created = request.operations[2].create
        self.assertEqual(created.ad_schedule.day_of_week.name, "FRIDAY")
        self.assertEqual(created.ad_schedule.start_minute.name, "THIRTY")
        self.assertEqual(created.ad_schedule.end_hour, 14)
        self.assertAlmostEqual(created.bid_modifier, 0.8)
        self.assertIn("removed 1 window(s), added 2", result)

    def test_schedule_change_between_propose_and_commit_is_rejected(self):
        svc = self.mock_client.get_service("CampaignCriterionService")
        windows = [{"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 20}]
        proposal = json.loads(
            cs.set_campaign_ad_schedule(customer_id=CID, campaign_id="5", windows=windows)
        )
        # Someone adds a window in the UI before the user confirms.
        self.schedule_rows = [_schedule_row(222, "MONDAY", 9, 17)]
        with self.assertRaises(ToolError):
            cs.set_campaign_ad_schedule(
                customer_id=CID, campaign_id="5", windows=windows,
                validate_only=False, checksum=proposal["checksum"],
            )
        self.assertEqual(svc.mutate_campaign_criteria.call_count, 1)

    def test_schedule_validation(self):
        bad = [
            [{"day_of_week": "SUNDAY", "start_hour": 20, "end_hour": 8}],
            [{"day_of_week": "SUNDAY", "start_hour": 8, "start_minute": 10, "end_hour": 9}],
            [{"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 24, "end_minute": 15}],
            [{"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 12},
             {"day_of_week": "SUNDAY", "start_hour": 11, "end_hour": 14}],
            [{"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 12, "bid_modifier": 20}],
        ]
        for windows in bad:
            with self.assertRaises(ToolError, msg=str(windows)):
                cs.set_campaign_ad_schedule(customer_id=CID, campaign_id="5", windows=windows)

    def test_empty_schedule_without_existing_is_rejected(self):
        with self.assertRaises(ToolError):
            cs.set_campaign_ad_schedule(customer_id=CID, campaign_id="5", windows=[])


class TestSettingsMounting(unittest.IsolatedAsyncioTestCase):
    """The new tools mount under the existing management namespace."""

    @patch("ads_mcp.config.ToolsConfig.load")
    async def test_tools_are_mounted(self, mock_load):
        mock_load.return_value = ToolsConfig({"namespaces": {"management": True}})
        parent = FastMCP("Test Parent")
        initialize_and_mount_tools(parent)
        names = {t.name for t in await parent.list_tools()}
        for expected in (
            "management_update_campaign_bidding",
            "management_update_campaign_location_targeting",
            "management_set_campaign_ad_schedule",
            "management_update_conversion_action",
        ):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
