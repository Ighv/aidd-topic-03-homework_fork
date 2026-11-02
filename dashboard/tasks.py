from config.celery import app
from config.settings import logger
from dashboard.models import Share
from dashboard.services.alerts import check_price_alerts
from dashboard.services.market_data import get_last_data


@app.task
def update_last_price():
    shares = Share.objects.all()

    for share in shares:
        try:
            result = get_last_data(share)
            if not result:
                continue
            last_price = result[0]

            try:
                if share.last_price is not None and last_price is not None:
                    if float(share.last_price) > float(last_price):
                        is_trend_high = False
                    else:
                        is_trend_high = True
                else:
                    is_trend_high = True
            except Exception as e:
                logger.error(e)
                is_trend_high = True

            try:
                Share.objects.filter(id=share.id).update(
                    last_price=last_price, is_trend_high=is_trend_high
                )
            except Exception as e:
                logger.error(e)
        except Exception as e:
            logger.error(e)


@app.task
def check_alerts():
    return check_price_alerts()
