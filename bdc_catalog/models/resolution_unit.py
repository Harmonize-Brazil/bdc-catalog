#
# This file is part of BDC-Catalog.
# Copyright (C) 2022 INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
#

"""Model for table ``bdc.resolution_unit``."""

from sqlalchemy import Column, Integer, String, Text

from ..config import BDC_CATALOG_SCHEMA
from .base_sql import BaseModel


class ResolutionUnit(BaseModel):
    """Model for table ``bdc.resolution_unit``."""

    __tablename__ = 'resolution_unit'
    __table_args__ = dict(
        schema=BDC_CATALOG_SCHEMA
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False, unique=True)
    symbol = Column(String(3))
    description = Column(Text)
