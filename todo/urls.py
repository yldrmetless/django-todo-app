from django.urls import path

from .views import (
    AdminDashboardView,
    CreateTaskView,
    EmployeeUserListView,
    TaskApproveOrRejectView,
    TaskCompleteRequestView,
    TaskDetailView,
    TasksListView,
)

urlpatterns = [
    path("employee-list/", EmployeeUserListView.as_view(), name="employee-list"),
    path("create-task/", CreateTaskView.as_view(), name="create-task"),
    path("tasks-list/", TasksListView.as_view(), name="tasks-list"),
    path("task-detail/<int:id>", TaskDetailView.as_view(), name="tasks-detail"),
    path(
        "tasks/<id>/request-complete/",
        TaskCompleteRequestView.as_view(),
        name="task-request-complete",
    ),
    path(
        "tasks/<int:id>/approve-or-reject/",
        TaskApproveOrRejectView.as_view(),
        name="task-approve-reject",
    ),
    path("dashboard/", AdminDashboardView.as_view(), name="dashboard"),
]
