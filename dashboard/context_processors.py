from dashboard.models import PriceAlert


def alert_notifications(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'triggered_alerts_count': PriceAlert.objects.filter(
            user=request.user,
            triggered=True,
        ).count(),
    }
