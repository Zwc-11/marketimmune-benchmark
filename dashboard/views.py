from django.shortcuts import render
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from dashboard.models import BenchmarkMetrics, ModelMetric, ProjectStats, TaskMetric
from dashboard.serializers import (
    BenchmarkMetricsSerializer,
    ModelMetricSerializer,
    ProjectStatsSerializer,
    TaskMetricSerializer,
)


class DashboardView(View):
    """Serve the main dashboard page"""
    def get(self, request):
        context = {
            'title': 'MarketImmune Benchmark Dashboard',
        }
        return render(request, 'dashboard/index.html', context)


class TaskMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for task metrics"""
    queryset = TaskMetric.objects.all()
    serializer_class = TaskMetricSerializer


class ModelMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for model metrics"""
    queryset = ModelMetric.objects.all()
    serializer_class = ModelMetricSerializer


class BenchmarkMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for benchmark metrics"""
    queryset = BenchmarkMetrics.objects.all()
    serializer_class = BenchmarkMetricsSerializer


@api_view(['GET'])
def project_stats(request):
    """Get overall project statistics"""
    try:
        stats = ProjectStats.objects.latest('last_updated')
        serializer = ProjectStatsSerializer(stats)
        return Response(serializer.data)
    except ProjectStats.DoesNotExist:
        return Response({'error': 'Project stats not available'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def dashboard_summary(request):
    """Get comprehensive dashboard summary"""
    try:
        stats = ProjectStats.objects.latest('last_updated')
        task_metrics = TaskMetric.objects.all()
        model_metrics = ModelMetric.objects.all().order_by('rank')
        
        return Response({
            'stats': ProjectStatsSerializer(stats).data,
            'task_metrics': TaskMetricSerializer(task_metrics, many=True).data,
            'model_metrics': ModelMetricSerializer(model_metrics, many=True).data,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def leaderboard(request):
    """Get model leaderboard"""
    models = ModelMetric.objects.all().order_by('rank')
    serializer = ModelMetricSerializer(models, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def phase_details(request, phase_id):
    """Get details for a specific phase"""
    try:
        benchmark = BenchmarkMetrics.objects.get(phase=phase_id)
        task_metrics = TaskMetric.objects.filter(phase=phase_id)
        
        return Response({
            'benchmark': BenchmarkMetricsSerializer(benchmark).data,
            'tasks': TaskMetricSerializer(task_metrics, many=True).data,
        })
    except BenchmarkMetrics.DoesNotExist:
        return Response({'error': 'Phase not found'}, status=status.HTTP_404_NOT_FOUND)
