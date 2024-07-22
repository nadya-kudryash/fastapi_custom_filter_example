import json
from typing import List, Type, Dict, Any

import pydantic
from fastapi import HTTPException
from fastapi_sa_orm_filter.main import FilterCore
from fastapi_sa_orm_filter.parsers import _OrderByQueryParser, _FilterQueryParser
from pydantic.v1.main import ModelMetaclass
from sqlalchemy import UnaryExpression, BinaryExpression, and_
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute
from starlette import status
from fastapi_sa_orm_filter.operators import Operators as ops

"""
Это дополнение для библиотеки с фильтрацией. 
Проблема в том, что, по логике библиотеки, order_by работает только с колонками БД через __table__.columns.keys(),
однако необходимо, чтобы сортировка работала и с полями, генерируемыми на уровне SQLALchemy
Также в выгрузке полей для фильтра по умолчанию участвуют только фактические колонки таблицы, column_property, 
все виды property, association_proxy и все, что на уровне ORM, в базовой библиотеке вызывает ошибку

"""


class CustomOrderByQueryParser(_OrderByQueryParser):
    def __init__(self, model: Type[DeclarativeMeta]):
        super().__init__(model=model)

    # метод переопреден в соответствии с логикой: проверяем запрашиваемое значение по атрибутам класса,
    # а не по колонкам в БД
    def _validate_order_by_fields(self, order_by_query_str: str) -> List[str]:
        """
        :return:
            [
                +field_name,
                -field_name
            ]
        """
        order_by_fields = order_by_query_str.split(",")

        for field in order_by_fields:
            field = field.strip('+').strip('-')
            if hasattr(self._model, field):
                continue
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect order_by field name {field} for model {self._model}",
            )
        return order_by_fields


class CustomFilterCore(FilterCore):
    def __init__(self, model: Type[DeclarativeMeta], allowed_filters: Dict[str, List[ops]]):
        super().__init__(model=model, allowed_filters=allowed_filters)

    def get_order_by_query_part(self, order_by_query_str: str) -> List[UnaryExpression]:
        order_by_parser = CustomOrderByQueryParser(self.model)
        return order_by_parser.get_order_by_query(order_by_query_str)

    def _get_filter_query(self, custom_filter: str) -> List[BinaryExpression]:
        filter_conditions = []
        if custom_filter == '':
            return filter_conditions
        query_parser = _CustomFilterQueryParser(custom_filter, self.model, self._allowed_filters)
        for and_expressions in query_parser.get_parsed_query():
            and_condition = []
            for expression in and_expressions:
                column, operator, value = expression
                serialized_dict = self._format_expression(column, operator, value)
                try:
                    value = serialized_dict[column.key]
                except KeyError:
                    if hasattr(self.model, column.key):
                        pass
                param = self._get_orm_for_field(column, operator, value)
                and_condition.append(param)
            filter_conditions.append(and_(*and_condition))
        return filter_conditions

    def _format_expression(
            self, column: InstrumentedAttribute, operator: str, value: str
    ) -> dict[str, Any]:
        """
        Serialize expression value from string to python type value,
        according to db model types

        :return: {'field_name': [value, value]}
        """
        value = value.split(",")
        try:
            if operator not in [ops.between, ops.in_]:
                value = value[0]
                serialized_dict = self._model_serializer["optional_model"](
                    **{column.key: value}
                ).model_dump(exclude_none=True)
                return serialized_dict
            serialized_dict = self._model_serializer["optional_list_model"](
                **{column.key: value}
            ).model_dump(exclude_none=True)
            return serialized_dict
        except pydantic.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=json.loads(e.json())
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect filter value '{value}'",
            )

    def _create_pydantic_serializer(self) -> Dict[str, ModelMetaclass]:
        """
        Create two pydantic models (optional and list field types)
        for value: str serialization

        :return: {
            'optional_model':
                class model.__name__(BaseModel):
                    field: Optional[type]
            'list_model':
                class model.__name__(BaseModel):
                    field: Optional[List[type]]
        }
        """
        pydantic_serializer = self.model.sqlalchemy_to_pydantic()
        optional_model = self._get_optional_pydantic_model(pydantic_serializer)
        optional_list_model = self._get_optional_pydantic_model(pydantic_serializer, is_list=True)
        return {"optional_model": optional_model, "optional_list_model": optional_list_model}


class _CustomFilterQueryParser(_FilterQueryParser):
    def __init__(self, query: str, model: Type[DeclarativeMeta], allowed_filters: Dict[str, List[ops]]):
        super().__init__(query=query, model=model, allowed_filters=allowed_filters)

    def get_parsed_query(self) -> List[List[Any]]:
        """
        :return:
            [
                [[column, operator, value], [column, operator, value]],
                [[column, operator, value]]
            ]
        """
        and_blocks = self._parse_by_conjunctions()
        parsed_query = []
        for and_block in and_blocks:
            parsed_and_blocks = []
            for expression in and_block:
                column, operator, value = self._parse_expression(expression)
                self._validate_query_params(column.key, operator)
                parsed_and_blocks.append([column, operator, value])
            parsed_query.append(parsed_and_blocks)
        return parsed_query