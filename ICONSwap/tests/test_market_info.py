# -*- coding: utf-8 -*-

# Copyright 2020 ICONation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
from ICONSwap.tests.iconswap_utils import *

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class TestICONSwap(ICONSwapTests):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))
    IRC2_PROJECT = os.path.abspath(os.path.join(DIR_PATH, './irc2'))

    def setUp(self):
        super().setUp()

        self.icon_service = None
        # if you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        # self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

        # install SCORE
        self._score_address = self._deploy_score(self.SCORE_PROJECT)['scoreAddress']
        self._operator = self._test1
        self._user = self._wallet_array[0]
        self._attacker = self._wallet_array[1]

        for wallet in self._wallet_array:
            icx_transfer_call(
                super(), self._test1, wallet.get_address(), 100 * 10**18, self.icon_service)

        self._operator_icx_balance = get_icx_balance(super(), address=self._operator.get_address(), icon_service=self.icon_service)
        self._user_icx_balance = get_icx_balance(super(), address=self._user.get_address(), icon_service=self.icon_service)
        self._irc2_address = self._deploy_irc2(self.IRC2_PROJECT)['scoreAddress']
        self._irc2_address_2 = self._deploy_irc2(self.IRC2_PROJECT)['scoreAddress']

        irc2_transfer(super(), from_=self._operator, token=self._irc2_address, to_=self._user.get_address(), value=0x1000000, icon_service=self.icon_service)
        irc2_transfer(super(), from_=self._operator, token=self._irc2_address_2, to_=self._user.get_address(), value=0x1000000, icon_service=self.icon_service)
        self._operator_irc2_balance = get_irc2_balance(super(), address=self._operator.get_address(), token=self._irc2_address, icon_service=self.icon_service)
        self._user_irc2_balance = get_irc2_balance(super(), address=self._user.get_address(), token=self._irc2_address, icon_service=self.icon_service)

    def _create_market(self):
        # SELL ICX - 2 ICX = 3 IRC2 (1 ICX = 1.5 IRC2)
        swap_id_200icx_300irc2 = self._create_icx_irc2_swap(200, 300)[0]
        # SELL ICX - 1 ICX = 2 IRC2 (1 ICX = 2 IRC2)
        swap_id_10icx_20irc2 = self._create_icx_irc2_swap(10, 20)[0]
        # SELL ICX - 1 ICX = 2 IRC2 (1 ICX = 2 IRC2)
        swap_id_100icx_200irc2 = self._create_icx_irc2_swap(100, 200)[0]
        # BUY ICX  - 10 IRC2 = 20 ICX (1 ICX = 0.5 IRC2)
        swap_id_10irc2_20icx = self._create_irc2_icx_swap(10, 20)[0]
        # BUY ICX  - 20 IRC2 = 30 ICX (1 ICX = 0.6667 IRC2)
        swap_id_20irc2_30icx = self._create_irc2_icx_swap(20, 30)[0]

        return (swap_id_200icx_300irc2,
                swap_id_10icx_20irc2,
                swap_id_100icx_200irc2,
                swap_id_10irc2_20icx,
                swap_id_20irc2_30icx)

    # ===============================================================
    def test_market_info_ok(self):
        self._create_market()

        market_info = self._get_market_info(0)

        # print(market_info)
        self.assertEqual(market_info['pairs'][0]['swaps_pending_count'], 5)
        self.assertEqual(market_info['pairs'][0]['last_price'], 0)

    def test_get_market_sellers_pending_swaps_ok(self):
        self._create_market()
        market_info = self._get_market_info(0)

        market_sellers = icx_call(
            super(),
            from_=self._operator.get_address(),
            to_=self._score_address,
            method="get_market_sellers_pending_swaps",
            params={"pair": market_info['pairs'][0]['name'], "offset": 0},
            icon_service=self.icon_service
        )

        # print("SELLERS =======================")
        # print(json.dumps(market_sellers, indent=4))
        self.assertEqual(market_sellers[0]['maker']['amount'], 200)
        self.assertEqual(market_sellers[0]['taker']['amount'], 300)
        self.assertEqual(market_sellers[1]['maker']['amount'], 10)
        self.assertEqual(market_sellers[1]['taker']['amount'], 20)
        self.assertEqual(market_sellers[2]['maker']['amount'], 100)
        self.assertEqual(market_sellers[2]['taker']['amount'], 200)

    def test_get_market_buyers_pending_swaps_ok(self):
        self._create_market()
        market_info = self._get_market_info(0)

        market_buyers = icx_call(
            super(),
            from_=self._operator.get_address(),
            to_=self._score_address,
            method="get_market_buyers_pending_swaps",
            params={"pair": market_info['pairs'][0]['name'], "offset": 0},
            icon_service=self.icon_service
        )

        # print("BUYERS =======================")
        # print(json.dumps(market_buyers, indent=4))
        self.assertEqual(market_buyers[0]['maker']['amount'], 20)
        self.assertEqual(market_buyers[0]['taker']['amount'], 30)
        self.assertEqual(market_buyers[1]['maker']['amount'], 10)
        self.assertEqual(market_buyers[1]['taker']['amount'], 20)

    def test_get_market_filled_swaps_ok(self):
        (swap_id_200icx_300irc2,
            swap_id_10icx_20irc2,
            swap_id_100icx_200irc2,
            swap_id_10irc2_20icx,
            swap_id_20irc2_30icx) = self._create_market()
        market_info = self._get_market_info(0)

        self._fill_irc2_order_success(self._user, self._irc2_address, swap_id_10icx_20irc2, 20)
        self._fill_irc2_order_success(self._user, self._irc2_address, swap_id_100icx_200irc2, 200)

        filled_swaps = icx_call(
            super(),
            from_=self._operator.get_address(),
            to_=self._score_address,
            method="get_market_filled_swaps",
            params={"pair": market_info['pairs'][0]['name'], "offset": 0},
            icon_service=self.icon_service
        )

        # print(json.dumps(filled_swaps, indent=4))
        self.assertEqual(filled_swaps[0]['maker']['amount'], 100)
        self.assertEqual(filled_swaps[0]['taker']['amount'], 200)
        self.assertEqual(filled_swaps[1]['maker']['amount'], 10)
        self.assertEqual(filled_swaps[1]['taker']['amount'], 20)
