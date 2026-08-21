from abc import ABC, abstractmethod
from django.db.models import QuerySet
from .models import GeoEvent

class MapFilterStrategy(ABC):
    @abstractmethod
    def filter(self, user) -> QuerySet:
        pass

class GlobalFilterStrategy(MapFilterStrategy):
    def filter(self, user) -> QuerySet:
        return GeoEvent.objects.all().order_by('-created_at')

class FollowingFilterStrategy(MapFilterStrategy):
    def filter(self, user) -> QuerySet:
        if not user.is_authenticated:
            return GeoEvent.objects.none()
        following_users = user.following.all()
        return GeoEvent.objects.filter(user__in=following_users).order_by('-created_at')

class EmptyFilterStrategy(MapFilterStrategy):
    def filter(self, user) -> QuerySet:
        return GeoEvent.objects.none()

class FilterStrategyFactory:
    @staticmethod
    def get_strategy(filter_type: str) -> MapFilterStrategy:
        strategies = {
            'global': GlobalFilterStrategy(),
            'following': FollowingFilterStrategy(),
            'empty': EmptyFilterStrategy(),
        }
        return strategies.get(filter_type, GlobalFilterStrategy())
