from typing import Type, Container, Optional, Dict

from pydantic import ConfigDict, create_model
from sqlalchemy import Column, Boolean, text, UUID
from sqlalchemy.orm import declarative_mixin, declared_attr, InstrumentedAttribute

from database import Base

from custom_fliter_util.filter_mapper import FILTER_MAPPER


class BaseModel(Base):
    """
    Базовая модель, в которой в дальнейшем могли бы быть кастомные методы INSERT, UPDATE, SELECT...WHERE

    """
    __abstract__ = True

    @classmethod
    def allowed_filters(cls, is_admin: bool = False) -> Dict:
        """
        Метод, используемый для фильтрации данных

        :param is_admin: роль пользователя
        :return: словарь с разрешенными фильтрами для каждого поля в зависимости от роли пользователя
        """
        if is_admin:
            return {**FILTER_MAPPER[cls.__name__]['basic'], **FILTER_MAPPER[cls.__name__]['admin']}

        return FILTER_MAPPER[cls.__name__]['basic']

    @classmethod
    def sqlalchemy_to_pydantic(
            cls, *, config: Type = ConfigDict(from_attributes=True), exclude: Container[str] = []
    ):
        """
       метод, переопределяющий логику базового метода из pydantic, который проверяет не только физические колонки БД,
       но и поля, создаваемые на уровне SQLAlchemy
        """
        fields = {}
        for column in cls.__mapper__.all_orm_descriptors.values():
            if not isinstance(type(column), InstrumentedAttribute):
                # исключаем relationships из проверки
                # также здесь не учитывается association_proxy
                continue

            name = column.key
            if name in exclude:
                continue
            python_type: Optional[type] = None
            if not hasattr(column, 'type'):
                continue

            if hasattr(column.type, "impl"):
                if hasattr(column.type.impl, "python_type"):
                    python_type = column.type.impl.python_type
            elif hasattr(column.type, "python_type"):
                python_type = column.type.python_type
            assert python_type, f"Could not infer python_type for {column}"

            if not hasattr(column, 'nullable'):
                fields[name] = (Optional[python_type], None)
                continue

            if not column.nullable:
                fields[name] = (python_type, ...)
            else:
                fields[name] = (Optional[python_type], None)

        pydantic_model = create_model(cls.__name__, __config__=config, **fields)
        return pydantic_model


@declarative_mixin
class RemovedModel:
    """
    Базовый класс, добавляющий колонку removed в таблицу

    """
    def __repr__(self):
        return f"<{self.__class__.__name__}{self.__dict__}>"

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    removed = Column(Boolean,
                     nullable=False,
                     default=False,
                     server_default='false')


@declarative_mixin
class IdModel:
    """
        Базовый класс, добавляющий колонку id (UUID) в таблицу

    """
    def __repr__(self):
        return f"<{self.__class__.__name__}{self.__dict__}>"

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(
        UUID(as_uuid=True),
        name='id',
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
