from rest_framework import serializers

from dashboard.models import PriceAlert, Share, Watchlist

from .serializer import ShareSerializer


class WatchlistSerializer(serializers.ModelSerializer):
    share = ShareSerializer(read_only=True)
    share_id = serializers.PrimaryKeyRelatedField(
        source='share',
        queryset=Share.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Watchlist
        fields = ['id', 'share', 'share_id', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        share = attrs.get('share')
        if request and share:
            query = Watchlist.objects.filter(user=request.user, share=share)
            if self.instance is not None:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(
                    {'share_id': 'Эта акция уже есть в списке наблюдения.'}
                )
        return attrs


class PriceAlertSerializer(serializers.ModelSerializer):
    share = ShareSerializer(read_only=True)
    share_id = serializers.PrimaryKeyRelatedField(
        source='share',
        queryset=Share.objects.all(),
        write_only=True,
    )

    class Meta:
        model = PriceAlert
        fields = [
            'id',
            'share',
            'share_id',
            'target_price',
            'condition',
            'is_active',
            'triggered',
            'triggered_at',
            'created_at',
        ]
        read_only_fields = ['id', 'triggered', 'triggered_at', 'created_at']

    def validate_target_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Целевая цена должна быть больше нуля.')
        return value
