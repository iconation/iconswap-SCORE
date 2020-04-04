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

from iconservice import *
from .swap import *
from ..scorelib.linked_list import *
from ..scorelib.set import *


class _MarketSidePendingSwapDB(LinkedListDB):
    """ _MarketSidePendingSwapDB is a linked list of swaps
        sorted by their ascending maker/price price
     """
    _NAME = '_MARKET_SIDE_PENDING_SWAP_DB'

    def __init__(self, var_key: str, db: IconScoreDatabase):
        name = var_key + _MarketSidePendingSwapDB._NAME
        super().__init__(name, db, int)
        self._name = name
        self._db = db

    def add(self, new_swap_id: int) -> None:
        """ Iterate through swap list and insert it according to the price """
        new_swap_price = Swap(new_swap_id, self._db).get_price()

        # Find positionning in the list for the current item
        for swap_node_id, cur_swap_id in self:
            cur_swap_price = Swap(cur_swap_id, self._db).get_price()
            if new_swap_price < cur_swap_price:
                self.prepend_before(new_swap_id, swap_node_id)
                break
        else:
            self.append(new_swap_id)


class _MarketBuyersPendingSwapDB(_MarketSidePendingSwapDB):
    _NAME = 'BUYERS'

    def __init__(self, var_key: str, db: IconScoreDatabase):
        name = var_key + _MarketBuyersPendingSwapDB._NAME
        super().__init__(name, db)
        self._name = name


class _MarketSellersPendingSwapDB(_MarketSidePendingSwapDB):
    _NAME = 'SELLERS'

    def __init__(self, var_key: str, db: IconScoreDatabase):
        name = var_key + _MarketSellersPendingSwapDB._NAME
        super().__init__(name, db)
        self._name = name


class MarketPendingSwapDB:
    """ MarketPendingSwapDB is two linked lists of swaps (buyers and sellers)
        sorted by their price
     """
    _NAME = 'MARKET_PENDING_SWAP_DB'

    def __init__(self, pair: tuple, db: IconScoreDatabase):
        self._name = MarketPairsDB.get_pair_name(pair) + '_' + MarketPendingSwapDB._NAME
        self._buyers = _MarketBuyersPendingSwapDB(self._name, db)
        self._sellers = _MarketSellersPendingSwapDB(self._name, db)
        self._pair = pair
        self._db = db

    def buyers(self) -> _MarketBuyersPendingSwapDB:
        return self._buyers

    def sellers(self) -> _MarketSellersPendingSwapDB:
        return self._sellers

    def add(self, new_swap_id: int) -> None:
        swap = Swap(new_swap_id, self._db)
        maker, taker = swap.get_orders()
        pair = (maker.contract(), taker.contract())
        if MarketPairsDB.is_buyer(pair, maker):
            self._buyers.add(new_swap_id)
        else:
            self._sellers.add(new_swap_id)

    def remove(self, swap_id: int) -> None:
        swap = Swap(swap_id, self._db)
        maker, taker = swap.get_orders()
        pair = (maker.contract(), taker.contract())
        if MarketPairsDB.is_buyer(pair, maker):
            self._buyers.remove(swap_id)
        else:
            self._sellers.remove(swap_id)


class MarketFilledSwapDB(LinkedListDB):
    _NAME = 'MARKET_FILLED_SWAP_DB'

    def __init__(self, pair: tuple, db: IconScoreDatabase):
        name = MarketPairsDB.get_pair_name(pair) + '_' + MarketFilledSwapDB._NAME
        super().__init__(name, db, int)
        self._name = name


class MarketPairsDB(SetDB):
    _NAME = 'MARKET_PAIRS_DB'

    @staticmethod
    def is_buyer(pair: tuple, order: Order) -> bool:
        contracts_alpha = sorted([str(pair[0]), str(pair[1])])
        return order.contract() == Address.from_string(contracts_alpha[1])

    @staticmethod
    def get_pair_name(pair: tuple) -> str:
        contracts_alpha = sorted([str(pair[0]), str(pair[1])])
        return contracts_alpha[0] + '/' + contracts_alpha[1]

    def __init__(self, db: IconScoreDatabase):
        name = MarketPairsDB._NAME
        super().__init__(name, db, str)
        self._name = name

    def add(self, pair: tuple) -> None:
        super().add(MarketPairsDB.get_pair_name(pair))

    def __contains__(self, pair: tuple) -> bool:
        return super().__contains__(MarketPairsDB.get_pair_name(pair))
