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
from ..scorelib.set import *


class InvalidWhitelistContract(Exception):
    pass


class Whitelist(SetDB):

    _NAME = 'WHITELIST'

    def __init__(self, db: IconScoreDatabase):
        super().__init__(Whitelist._NAME, db, Address)

    def add(self, token: Address) -> None:
        if not token.is_contract:
            raise InvalidWhitelistContract(self._NAME, token)
        super().add(token)
