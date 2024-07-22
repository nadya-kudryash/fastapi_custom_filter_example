from custom_fliter_util.CustomFilter import CustomFilterCore

"""
Привязка модели к роуту (для фильтрации)
"""

MAPPER_ROUTE_MODEL = {
    'signs': ClientTimetableSign,
    'client_subscriptions': ClientSubscription,
    'coaches': Coach,
    'lessons': Lesson,
    'subscriptions': SubscriptionType,
    'timetable': Timetable,
    'users': User
}


def get_model_by_route(route: str):
    """
    :param route: базовое название роута
    :return: получаем модель, исходя из роута
    """
    return next((v for k, v in MAPPER_ROUTE_MODEL.items() if k in route), None)


def decode_string(encoded_string):
    # Разбиваем строку по символу '='
    parts = encoded_string.split('=', 1)

    if len(parts) != 2:
        raise ValueError("Некорректный формат строки")

    key, encoded_value = parts

    # Декодируем значение
    decoded_value = urllib.parse.unquote(encoded_value)

    # Формируем нормальную строку
    normal_string = f"{key}={decoded_value}"

    return normal_string


async def get_filtered_entities(
        request: Request,
        db: AsyncSession = Depends(get_session),
        user: User = Depends(get_current_user)
) -> List:
    """
    Логика фильтрации данных

    """
    # получаем модель через привязку к пути роута
    _model = get_model_by_route(request.url.path)
    filter_query = request.url.query  # получаем "сырую" строку для фильтрации из параметров

    # логика для отдачи данных, если запрашиваются объекты без фильтров
    if len(filter_query) == 0:
        query = select(_model)

        # если роль пользователя НЕ админ
        if user.role_id != RoleTypeEntry.ADMIN.value:
            if hasattr(_model, 'user_id'):
                # добавляем к запросу его user_id, чтобы отдать сущности, привязанные только к конкретному пользователю
                query = query.where(_model.user_id == user.id)

            if hasattr(_model, 'removed') and not hasattr(_model, 'user_id'):
                # также добавляем к запросу только НЕ архивные/НЕ удаленные сущности
                query = query.where(_model.removed == False)

        entities = (await db.execute(query)).scalars().all()
        return entities

    filter_query = decode_string(filter_query)  # декодируем строку для дальнейшей работы

    # если пользователь админ, то отдаем разрешенные фильтры с флагом True
    if user.role_id == RoleTypeEntry.ADMIN.value:
        my_filter = CustomFilterCore(_model, _model.allowed_filters(is_admin=True))
        query = my_filter.get_query(filter_query)

    else:
        my_filter = CustomFilterCore(_model, _model.allowed_filters())
        query = my_filter.get_query(filter_query)
        if hasattr(_model, 'user_id'):
            # по умолчанию добавляем к фильтру user_id, равное user_id залогиненного пользователя,
            # чтобы получить сущности, относящиеся только к этому пользователю
            query = query.where(_model.user_id == user.id)
        if hasattr(_model, 'removed'):
            # по умолчанию добавляем фильтр removed = False, чтобы выводить только неудаленные записи
            query = query.where(_model.removed == False)

    entities = (await db.execute(query)).scalars().all()
    return entities