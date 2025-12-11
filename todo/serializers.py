from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    task_owner = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "is_completed",
            "created_at",
            "task_owner",
        ]

    def get_task_owner(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}"
