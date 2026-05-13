from rest_framework import serializers

from dashboard.models import BenchmarkMetrics, ModelMetric, ProjectStats, TaskMetric


class TaskMetricSerializer(serializers.ModelSerializer):
    task_display = serializers.CharField(source='get_task_name_display', read_only=True)

    class Meta:
        model = TaskMetric
        fields = [
            'id',
            'task_name',
            'task_display',
            'pr_auc',
            'auroc',
            'f1_score',
            'other_metrics',
            'status',
            'phase',
        ]


class ModelMetricSerializer(serializers.ModelSerializer):
    model_display = serializers.CharField(source='get_model_name_display', read_only=True)

    class Meta:
        model = ModelMetric
        fields = [
            'id',
            'model_name',
            'model_display',
            'task_name',
            'pr_auc',
            'auroc',
            'inference_latency_ms',
            'extra_metrics',
            'phase',
            'rank',
        ]


class BenchmarkMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkMetrics
        fields = ['phase', 'title', 'data', 'created_at', 'updated_at']


class ProjectStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStats
        fields = [
            'total_examples',
            'total_tasks',
            'total_phases',
            'total_models',
            'test_coverage',
            'type_errors',
            'linting_violations',
            'test_count',
            'last_updated',
        ]
