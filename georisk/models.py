from django.db import models
from django.conf import settings

class GeoEvent(models.Model):
    TYPE_CHOICES = [
        ('Inundacao', 'Inundação'),
        ('Desmoronamento', 'Desmoronamento'),
        ('Queimada', 'Queimada'),
        ('Geada', 'Geada'),
        ('Tempestade', 'Tempestade'),
    ]

    SEVERITY_CHOICES = [
        ('Baixa', 'Baixa'),
        ('Media', 'Média'),
        ('Critica', 'Crítica'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='geo_events')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.severity} ({self.latitude}, {self.longitude})"
