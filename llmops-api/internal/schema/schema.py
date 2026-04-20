


from wtforms import Field


class ListField(Field):
    """
    wtforms字段类，用于处理列表类型的数据
    """

    data:list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data  else []



class DictField(Field):
    """自定义字典"""

    data: list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and len(valuelist) > 0 and isinstance(valuelist[0], dict):
            self.data = valuelist[0]

    def _value(self):
        return self.data
