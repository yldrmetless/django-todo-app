from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from todo.pagination import PostPagination
from .models import Task
from .serializers import TaskSerializer
from accounts.permissions import IsAdminUser, IsTododminUser
from django.db.models import Q
from django.utils import timezone
from accounts.models import User



class EmployeeUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, *args, **kwargs):

        employees = User.objects.filter(user_type='employee', is_active=True)

        employees_data = [
            {
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
            }
            for emp in employees
        ]

        return Response(
            {
                "status": 200,
                "message": "Employee users retrieved successfully.",
                "response": employees_data
            },
            status=status.HTTP_200_OK
        )


class CreateTaskView(APIView):
    permission_classes = [IsAuthenticated, IsTododminUser]

    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        description = request.data.get("description")
        due_date = request.data.get("due_date")
        assigned_user_id = request.data.get("assigned_user")

        # ===== VALIDATION =====
        if not title:
            return Response(
                {"error": "title field cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # assigned_user validation
        assigned_user = None
        if assigned_user_id:
            try:
                assigned_user = User.objects.get(id=assigned_user_id, is_deleted=False)
            except User.DoesNotExist:
                return Response(
                    {"error": "assigned_user not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # ===== CREATE TASK =====
        task = Task.objects.create(
            owner=request.user,
            title=title,
            description=description,
            due_date=due_date,
            assigned_user=assigned_user
        )

        # ===== RESPONSE =====
        return Response(
            {
                "status": 201,
                "message": "Task created successfully.",
                "response": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "due_date": task.due_date,
                    "assigned_user": assigned_user_id,
                    "assigned_user_name": f"{assigned_user.first_name} {assigned_user.last_name}" if assigned_user else None,
                    "is_completed": task.is_completed,
                    "created_at": task.created_at,
                }
            },
            status=status.HTTP_201_CREATED
        )

    

class TasksListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination

    def get(self, request, *args, **kwargs):
        user = request.user

        base_qs = Task.objects.filter(is_deleted=False)

        if user.user_type == "admin":
            tasks = base_qs
        else:
            tasks = base_qs.filter(
                Q(owner=user) | Q(assigned_user=user)
            )

        is_completed_param = request.query_params.get("is_completed")
        if is_completed_param is not None:
            value = is_completed_param.lower()
            if value in ["true", "1", "yes"]:
                tasks = tasks.filter(is_completed=True)
            elif value in ["false", "0", "no"]:
                tasks = tasks.filter(is_completed=False)

        due_date_start = request.query_params.get("due_date_start")
        due_date_end = request.query_params.get("due_date_end")

        if due_date_start:
            tasks = tasks.filter(due_date__gte=due_date_start)
        if due_date_end:
            tasks = tasks.filter(due_date__lte=due_date_end)

        tasks = tasks.order_by("-created_at")

        serializer = TaskSerializer(tasks, many=True)

        return Response(
            {
                "status": 200,
                "message": "Tasks retrieved successfully.",
                "response": serializer.data,
            },
            status=status.HTTP_200_OK,
        )




class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            task = Task.objects.get(id=id, owner=request.user, is_deleted=False)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "is_completed": task.is_completed,
            "is_deleted": task.is_deleted,
            "created_at": task.created_at,
            "task_owner": f"{task.owner.first_name} {task.owner.last_name}",
        }

        return Response(
            {
                "status": 200,
                "message": "Task retrieved successfully.",
                "response": task_data
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request, id, *args, **kwargs):
        try:
            task = Task.objects.get(id=id, owner=request.user, is_deleted=False)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.user.user_type != "admin":
            return Response(
                {"detail": "You do not have permission to update this task."},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data

        title = data.get("title")
        description = data.get("description")
        due_date = data.get("due_date")
        is_completed = data.get("is_completed")
        is_deleted = data.get("is_deleted")

        if "title" in data and (title is None or title == ""):
            return Response(
                {"error": "title field cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if title is not None:
            task.title = title

        if description is not None:
            task.description = description

        if due_date is not None:
            task.due_date = due_date

        if is_completed is not None:
            task.is_completed = bool(is_completed)

        if is_deleted is not None:
            task.is_deleted = bool(is_deleted)

        task.save()

        updated_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "is_completed": task.is_completed,
            "is_deleted": task.is_deleted,
            "created_at": task.created_at,
            "task_owner": f"{task.owner.first_name} {task.owner.last_name}",
        }

        return Response(
            {
                "status": 200,
                "message": "Task updated successfully.",
                "response": updated_data
            },
            status=status.HTTP_200_OK
        )
    


class TaskCompleteRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id, *args, **kwargs):

        user = request.user

        if user.user_type != "employee":
            return Response(
                {"detail": "Only employees can request completion."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            task = Task.objects.get(id=id, is_deleted=False)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if task.assigned_user != user:
            return Response(
                {"detail": "You are not assigned to this task."},
                status=status.HTTP_403_FORBIDDEN
            )

        if task.complete_requested:
            return Response(
                {"detail": "Completion request already submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.complete_requested = True
        task.save()

        return Response(
            {
                "status": 200,
                "message": "Completion request submitted successfully.",
                "response": {
                    "id": task.id,
                    "title": task.title,
                    "assigned_user": f"{task.assigned_user.first_name} {task.assigned_user.last_name}",
                    "complete_requested": task.complete_requested,
                }
            },
            status=status.HTTP_200_OK
        )
    



class TaskApproveOrRejectView(APIView):
    """
    Sadece user_type = 'admin' ve task.owner == request.user olan kullanıcı:
      - is_completed = True  yaparak görevi onaylayabilir
      - complete_requested = False + reason göndererek isteği reddedebilir
        ve reason_for_reject JSONField'ına {id, reason} formatında eklenir.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, id, *args, **kwargs):
        user = request.user

        if user.user_type != "admin":
            return Response(
                {"detail": "Only admins can approve or reject completion requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            task = Task.objects.get(id=id, is_deleted=False)
        except Task.DoesNotExist:
            return Response(
                {"detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if task.owner != user:
            return Response(
                {"detail": "You are not the owner of this task."},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data

        is_completed = data.get("is_completed", None)
        complete_requested = data.get("complete_requested", None)
        reason = data.get("reason", None)

        if is_completed is True:
            task.is_completed = True
            task.complete_requested = False
            task.save()

            return Response(
                {
                    "status": 200,
                    "message": "Task marked as completed by admin.",
                    "response": {
                        "id": task.id,
                        "title": task.title,
                        "is_completed": task.is_completed,
                        "complete_requested": task.complete_requested,
                        "reason_for_reject": task.reason_for_reject,
                    }
                },
                status=status.HTTP_200_OK
            )

        if complete_requested is False:
            if not reason:
                return Response(
                    {"detail": "reason field is required when rejecting completion request."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            existing_reasons = task.reason_for_reject or []

            if not isinstance(existing_reasons, list):
                existing_reasons = []

            new_id = len(existing_reasons) + 1

            existing_reasons.append({
                "id": new_id,
                "reason": reason
            })

            task.reason_for_reject = existing_reasons
            task.complete_requested = False
            task.is_completed = False
            task.save()

            return Response(
                {
                    "status": 200,
                    "message": "Completion request rejected by admin.",
                    "response": {
                        "id": task.id,
                        "title": task.title,
                        "is_completed": task.is_completed,
                        "complete_requested": task.complete_requested,
                        "reason_for_reject": task.reason_for_reject,
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "detail": (
                    "You must send either 'is_completed': true to approve "
                    "or 'complete_requested': false with 'reason' to reject."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    





class AdminDashboardView(APIView):
    """
    Sadece user_type='admin' olan ve sadece kendi owner olduğu task'ler için
    dashboard özeti döner.
    İsteğe bağlı olarak ?is_rejected=true|false filtresi ile task listesi dönebilir.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.user_type != "admin":
            return Response(
                {"detail": "Only admins can access this dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        qs = Task.objects.filter(owner=user, is_deleted=False)

        is_rejected_param = request.query_params.get("is_rejected", None)

        if is_rejected_param is not None:
            is_rejected_param = is_rejected_param.lower()
            now = timezone.now()

            if is_rejected_param == "true":
                filtered = qs.filter(
                    is_completed=False,
                    complete_requested=False
                ).filter(
                    Q(reason_for_reject__isnull=False) |
                    Q(due_date__lt=now)
                )

                tasks_data = [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "due_date": task.due_date,
                        "is_completed": task.is_completed,
                        "complete_requested": task.complete_requested,
                        "reason_for_reject": task.reason_for_reject,
                        "created_at": task.created_at,
                    }
                    for task in filtered
                ]

                return Response(
                    {
                        "status": 200,
                        "message": "Rejected / overdue tasks retrieved successfully.",
                        "response": tasks_data,
                    },
                    status=status.HTTP_200_OK
                )

            elif is_rejected_param == "false":
                filtered = qs.filter(is_completed=True)

                tasks_data = [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "due_date": task.due_date,
                        "is_completed": task.is_completed,
                        "complete_requested": task.complete_requested,
                        "reason_for_reject": task.reason_for_reject,
                        "created_at": task.created_at,
                    }
                    for task in filtered
                ]

                return Response(
                    {
                        "status": 200,
                        "message": "Completed tasks retrieved successfully.",
                        "response": tasks_data,
                    },
                    status=status.HTTP_200_OK
                )

            else:
                return Response(
                    {"detail": "Invalid value for is_rejected. Use 'true' or 'false'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        total_tasks = qs.count()
        completed_tasks = qs.filter(is_completed=True).count()
        active_tasks = qs.filter(is_completed=False).count()
        pending_approval_tasks = qs.filter(
            complete_requested=True,
            is_completed=False
        ).count()

        total_rejections = 0
        tasks_with_rejection = 0

        for task in qs:
            reasons = task.reason_for_reject or []
            if isinstance(reasons, list) and len(reasons) > 0:
                total_rejections += len(reasons)
                tasks_with_rejection += 1

        data = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_tasks": active_tasks,
            "pending_approval_tasks": pending_approval_tasks,
            "tasks_with_rejection": tasks_with_rejection,
            "total_rejections": total_rejections,
        }

        return Response(
            {
                "status": 200,
                "message": "Admin dashboard data retrieved successfully.",
                "response": data,
            },
            status=status.HTTP_200_OK
        )