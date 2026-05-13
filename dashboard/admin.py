from django.contrib import admin

from dashboard.models import (
    BenchmarkMetrics,
    ModelMetric,
    ProjectStats,
    TaskMetric,
)


@admin.register(BenchmarkMetrics)
class BenchmarkMetricsAdmin(admin.ModelAdmin):
    list_display = ('phase', 'title', 'created_at')
    list_filter = ('phase', 'created_at')
    search_fields = ('title', 'phase')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Phase Info', {
            'fields': ('phase', 'title'),
        }),
        ('Data', {
            'fields': ('data',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TaskMetric)
class TaskMetricAdmin(admin.ModelAdmin):
    list_display = ('task_display', 'phase', 'pr_auc', 'auroc', 'f1_score', 'status')
    list_filter = ('task_name', 'phase', 'status', 'created_at')
    search_fields = ('task_name', 'phase')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Task Info', {
            'fields': ('task_name', 'phase', 'status'),
        }),
        ('Metrics', {
            'fields': ('pr_auc', 'auroc', 'f1_score'),
        }),
        ('Additional', {
            'fields': ('other_metrics',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def task_display(self, obj):
        return obj.get_task_name_display()
    task_display.short_description = 'Task'


@admin.register(ModelMetric)
class ModelMetricAdmin(admin.ModelAdmin):
    list_display = ('model_display', 'task_name', 'phase', 'pr_auc', 'rank')
    list_filter = ('model_name', 'phase', 'rank', 'created_at')
    search_fields = ('model_name', 'task_name', 'phase')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('rank',)
    
    fieldsets = (
        ('Model Info', {
            'fields': ('model_name', 'task_name', 'phase', 'rank'),
        }),
        ('Metrics', {
            'fields': ('pr_auc', 'auroc', 'inference_latency_ms'),
        }),
        ('Additional', {
            'fields': ('extra_metrics',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def model_display(self, obj):
        return obj.get_model_name_display()
    model_display.short_description = 'Model'


@admin.register(ProjectStats)
class ProjectStatsAdmin(admin.ModelAdmin):
    list_display = ('total_examples', 'test_coverage', 'test_count', 'last_updated')
    list_filter = ('last_updated',)
    readonly_fields = ('created_at', 'last_updated')
    
    fieldsets = (
        ('Project Overview', {
            'fields': ('total_examples', 'total_tasks', 'total_phases', 'total_models'),
        }),
        ('Quality Metrics', {
            'fields': ('test_coverage', 'type_errors', 'linting_violations', 'test_count'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        # Allow only one ProjectStats object
        return not self.model.objects.exists()


# Admin site customization
admin.site.site_header = "MarketImmune Benchmark Dashboard"
admin.site.site_title = "MarketImmune Admin"
admin.site.index_title = "Dashboard Administration"
