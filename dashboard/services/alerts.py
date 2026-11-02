from django.utils import timezone

from config.settings import logger
from dashboard.models import PriceAlert


def check_price_alerts():
    """Проверить активные уведомления и отметить сработавшие.

    Возвращает количество уведомлений, сработавших в этом запуске.
    Повторно уже сработавшие уведомления не проверяются, поэтому
    дублирования одного и того же события не происходит.
    """
    alerts = PriceAlert.objects.filter(
        is_active=True,
        triggered=False,
    ).select_related('share', 'user')

    triggered_count = 0
    for alert in alerts:
        try:
            price = alert.share.last_price
            if price is None:
                continue

            if alert.condition == PriceAlert.ABOVE:
                hit = float(price) >= float(alert.target_price)
            else:
                hit = float(price) <= float(alert.target_price)

            if hit:
                alert.triggered = True
                alert.triggered_at = timezone.now()
                alert.save(update_fields=['triggered', 'triggered_at'])
                triggered_count += 1
                logger.info(
                    'Alert triggered: user=%s share=%s price=%s',
                    alert.user_id,
                    alert.share.ticker,
                    price,
                )
        except Exception as error:
            logger.error(error)

    return triggered_count
