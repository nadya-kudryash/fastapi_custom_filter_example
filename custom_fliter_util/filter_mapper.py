"""
Привязка колонок модели к разрешенным фильтрам с учетом роли пользователя:
основной ключ словаря - название таблицы
basic - список разрешенных для фильтра колонок (с учетом и генерируемых на уровне Python) для всех пользователей
admin - список разрешенных для фильтра колонок (с учетом и генерируемых на уровне Python), которые добавляются к базовым,
если пользователь - админ

Значения - это библиотечные операторы, которые применяются для фильтрации данных


Для наглядности они размещены именно таким образом, для реального проекта я бы написала функцию или целый класс, формирующий
допустимые операторы для каждой колонки, исходя из ее типа (например, все колонки с типом integer имеют разрешенные фильтры
равно, не равно, меньше, больше и тд.
"""

FILTER_MAPPER = {
    'ClientTimetableSign': {
        'basic': {
            'visited': [ops.eq],
            'timetable_id': [ops.eq, ops.not_eq, ops.in_],
            'timetable_date': [ops.eq, ops.in_, ops.between, ops.gte, ops.lte, ops.gt, ops.lt],
            'client_sub_id': [ops.eq, ops.not_eq, ops.in_],
            'id': [ops.eq, ops.not_eq, ops.in_],
            'removed': [ops.eq],
        },
        'admin': {
            'user_id': [ops.eq, ops.not_eq, ops.in_],
        },
    },

    'ClientSubscription': {
        'basic': {
            'sub_id': [ops.eq, ops.not_eq, ops.in_],
            'id': [ops.eq, ops.not_eq, ops.in_],
            'removed': [ops.eq],
            'paid_date': [ops.eq, ops.in_, ops.between, ops.gte, ops.lte, ops.gt, ops.lt],
            'end_date': [ops.eq, ops.in_, ops.between, ops.gte, ops.lte, ops.gt, ops.lt],
            'yet_to_visit': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
            'visited_or_missed': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
        },
        'admin': {
            'user_id': [ops.eq, ops.not_eq, ops.in_],
        }
    },

    'Coach': {
        'basic': {
            'id': [ops.eq, ops.in_, ops.not_eq],
            'name': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'surname': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
        },
        'admin': {
            'removed': [ops.eq, ops.not_eq],
        }
    },

    'Lesson': {
        'basic': {
            'id': [ops.eq, ops.in_, ops.not_eq],
            'name': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'description': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'max_quantity_students': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
        },
        'admin': {
            'removed': [ops.eq, ops.not_eq],
        }
    },

    'SubscriptionType': {
        'basic': {
            'id': [ops.eq, ops.in_, ops.not_eq],
            'name': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'description': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'quantity_lessons': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
            'period_days': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
            'price': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
        },
        'admin': {
            'removed': [ops.eq, ops.not_eq],
        }
    },

    'Timetable': {
        'basic': {
            'id': [ops.eq, ops.in_, ops.not_eq],
            'coach_id': [ops.eq, ops.in_, ops.not_eq],
            'lesson_id': [ops.eq, ops.in_, ops.not_eq],
            'date': [ops.eq, ops.in_, ops.between, ops.gte, ops.lte, ops.gt, ops.lt],
            'quantity_people_signed': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
            'removed': [ops.eq, ops.not_eq],
        },
        'admin': {}
    },

    'User': {
        'basic': {},
        'admin': {
            'id': [ops.eq, ops.in_, ops.not_eq],
            'name': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'surname': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'patronymic': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'email': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'role_id': [ops.eq, ops.in_, ops.between, ops.gt, ops.lt, ops.gte, ops.lte],
            'login': [ops.like, ops.startswith, ops.contains, ops.eq, ops.not_eq],
            'registration_date': [ops.eq, ops.in_, ops.between, ops.gte, ops.lte, ops.gt, ops.lt],
        }
    }
}