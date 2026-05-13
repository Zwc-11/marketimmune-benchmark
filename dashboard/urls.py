from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()
router.register(r'task-metrics', views.TaskMetricViewSet)
router.register(r'model-metrics', views.ModelMetricViewSet)
router.register(r'benchmark-metrics', views.BenchmarkMetricsViewSet)

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('api/', include(router.urls)),
    path('api/stats/', views.project_stats, name='project_stats'),
    path('api/summary/', views.dashboard_summary, name='dashboard_summary'),
    path('api/leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/phase/<int:phase_id>/', views.phase_details, name='phase_details'),
]
