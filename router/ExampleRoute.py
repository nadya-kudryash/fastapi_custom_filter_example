from dependency.filter_dependency import get_filtered_entities


@router.get('', summary='Получить все абонементы', response_model=List[ClientSubscriptionSchema])
async def get_client_subscriptions(
        subscriptions: List[ClientSubscription] = Depends(get_filtered_entities),
):
    """
    Если текущий пользователь не админ, то к фильтрам будет автоматически добавляться user_id
    """

    return subscriptions
