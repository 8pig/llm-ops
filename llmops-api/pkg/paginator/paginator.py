import math
from dataclasses import dataclass
from typing import Any

from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms.validators import Optional, NumberRange

from pkg.sqlalchemy import SQLAlchemy


class PaginatorReq(FlaskForm):
    """ 分页基础类"""

    current_page = IntegerField("current_page",default=1, validators=[
        Optional(),
        NumberRange(min=1, max=1000, message="页码必须大于1小于1000")
    ])

    page_size = IntegerField("page_size",default=20, validators=[
        Optional(),
        NumberRange(min=1, max=50, message="页大小必须大于1小于50")
    ])


@dataclass
class Paginator:
    total_page: int = 0
    total_record: int = 0
    current_page: int = 1
    page_size: int = 20

    def __init__(self, db: SQLAlchemy,  req: PaginatorReq =  None):
        if req is not None:
            self.current_page = req.current_page.data
            self.page_size = req.page_size.data

        self.db = db

    def paginate(self, select) -> list[Any]:
        p =  self.db.paginate(select, self.current_page, self.page_size,error_out=True)
        self.total_record = p.total
        self.total_page = math.ceil(p.total/p.pages)
        return  p.items


@dataclass
class PageModel:
    list: list[Any]
    paginator: Paginator