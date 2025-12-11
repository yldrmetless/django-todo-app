import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from todo.models import Task

# Bu dosyadaki TÜM testler DB kullanabilir:
pytestmark = pytest.mark.django_db

User = get_user_model()


"""
    pytestmark = pytest.mark.django_db → dosyadaki tüm testlerin DB kullanmasına izin veriyoruz (her teste tek tek decorator yazmayacağız).

    create_admin_user():

    is_staff=True veriyoruz → IsAdminUser bunu kontrol eder.

    is_superuser=True de veriyoruz, zararı yok.

    -----------------------

    get_authenticated_client():

    DRF APIClient() oluşturuyoruz.

    force_authenticate ile request’lerde request.user olarak bu user’ı kullanmasını sağlıyoruz.
"""


def create_admin_user():
    """
    CreateTaskView için 'admin' demek:
    user.user_type == 'todo admin' olan kullanıcıdır.
    """
    return User.objects.create_user(
        username="adminuser",
        email="admin@example.com",
        password="adminpassword123",
        user_type="todo admin",
    )

def get_authenticated_client(user=None):
    """
    DRF APIClient oluştur ve kullanıcıyı authenticated et.
    """
    if user is None:
        user = create_admin_user()

    client = APIClient()
    client.force_authenticate(user=user)
    return client



def test_create_task_success_with_admin_user():
    """
    Senaryo:
    - Admin user ile login ol
    - Geçerli bir payload ile /api/todo/create-task/ endpointine POST at
    - 201 dönmeli
    - Response body doğru olmalı
    - DB'de gerçekten Task oluşmalı
    """
    admin_user = create_admin_user()
    client = get_authenticated_client(admin_user)

    url = reverse("create-task")  # -> /api/todo/create-task/
    payload = {
        "title": "Test Task",
        "description": "This is a test task.",
        "due_date": "2025-12-31T00:00:00Z",
        "assigned_user": None,
    }

    response = client.post(url, payload, format="json")

    assert response.status_code == 201

    data = response.json()
    assert data["status"] == 201
    assert data["message"] == "Task created successfully."
    assert data["response"]["title"] == payload["title"]
    assert data["response"]["description"] == payload["description"]
    assert data["response"]["assigned_user"] is None
    assert data["response"]["is_completed"] is False

    assert Task.objects.count() == 1
    task = Task.objects.first()
    assert task.title == payload["title"]
    assert task.description == payload["description"]
    assert task.owner == admin_user
    assert task.assigned_user is None


def test_create_task_empty_title_returns_400():
    """
    Senaryo:
    - Admin user ile login ol
    - title="" (veya None) ile istek at
    - API 400 döndürmeli
    - Hata mesajı 'title field cannot be empty.' olmalı
    - DB'ye Task kaydı eklenmemeli
    """
    # Arrange
    admin_user = create_admin_user()
    client = get_authenticated_client(admin_user)

    url = reverse("create-task")
    payload = {
        "title": "",  # 👈 boş title
        "description": "Some description",
        "due_date": "2025-12-31T00:00:00Z",
        "assigned_user": None,
    }

    # Act
    response = client.post(url, payload, format="json")

    # Assert
    assert response.status_code == 400

    data = response.json()
    assert "error" in data
    assert data["error"] == "title field cannot be empty."

    # DB kontrol: hiç Task oluşmamalı
    assert Task.objects.count() == 0



def test_create_task_with_invalid_assigned_user_returns_404():
    """
    Senaryo:
    - Todo admin user ile login ol
    - assigned_user olarak var olmayan bir id gönder
    - API 404 döndürmeli
    - Hata mesajı 'assigned_user not found.' olmalı
    - DB'ye Task kaydı eklenmemeli
    """
    # Arrange
    admin_user = create_admin_user()
    client = get_authenticated_client(admin_user)

    url = reverse("create-task")
    fake_user_id = 999999  # sistemde olmayan bir id

    payload = {
        "title": "Task with invalid assignee",
        "description": "This should fail.",
        "due_date": "2025-12-31T00:00:00Z",
        "assigned_user": fake_user_id,
    }

    # Act
    response = client.post(url, payload, format="json")

    # Assert
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"] == "assigned_user not found."
    print("RESPONSE:", response.status_code, response.json())


    # DB kontrol: Task oluşmamalı
    assert Task.objects.count() == 0




# def create_employee_user():
#     """
#     Normal çalışan kullanıcı.
#     CreateTaskView için yetkisiz olmalı.
#     """
#     return User.objects.create_user(
#         username="employeeuser",
#         email="employee@example.com",
#         password="employeepassword123",
#         user_type="employee",
#     )

def create_employee_user():
    """
    Normal çalışan kullanıcı.
    CreateTaskView için yetkili DEĞİL (IsTododminUser geçemez),
    ama assigned_user olarak atanabilir.
    """
    return User.objects.create_user(
        username="employeeuser",
        email="employee@example.com",
        password="employeepassword123",
        first_name="Ali",
        last_name="Veli",
        user_type="employee",
    )


def test_create_task_forbidden_for_employee_user():
    """
    Senaryo:
    - user_type='employee' olan bir kullanıcı ile create-task endpointine POST at
    - 403 Forbidden dönmeli
    - Response'ın içinde 'detail' olmalı
    - DB'de Task oluşmamalı
    """
    employee_user = create_employee_user()
    client = get_authenticated_client(employee_user)

    url = reverse("create-task")
    payload = {
        "title": "Employee created task",
        "description": "Employee should not be allowed to create tasks.",
        "due_date": "2025-12-31T00:00:00Z",
        "assigned_user": None,
    }

    response = client.post(url, payload, format="json")

    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 403

    data = response.json()
    assert "detail" in data
    assert data["detail"] == "You do not have permission to perform this action."

    assert Task.objects.count() == 0



def test_create_task_with_valid_assigned_user_success():
    """
    Senaryo:
    - Bir todo admin user oluştur
    - Bir de normal employee user oluştur
    - Admin ile login olup, assigned_user olarak employee.id gönder
    - 201 dönmeli
    - Response'ta assigned_user ve assigned_user_name doğru olmalı
    - DB'de Task.owner = admin, Task.assigned_user = employee olmalı
    """
    admin_user = create_admin_user()
    employee_user = create_employee_user()

    client = get_authenticated_client(admin_user)

    url = reverse("create-task")
    payload = {
        "title": "Task with assignee",
        "description": "This task has an assigned employee.",
        "due_date": "2025-12-31T00:00:00Z",
        "assigned_user": employee_user.id,
    }

    response = client.post(url, payload, format="json")

    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 201

    data = response.json()
    assert data["status"] == 201
    assert data["message"] == "Task created successfully."

    resp = data["response"]
    assert resp["title"] == payload["title"]
    assert resp["description"] == payload["description"]
    assert resp["assigned_user"] == employee_user.id
    assert resp["assigned_user_name"] == f"{employee_user.first_name} {employee_user.last_name}"
    assert resp["is_completed"] is False

    assert Task.objects.count() == 1
    task = Task.objects.first()
    assert task.title == payload["title"]
    assert task.description == payload["description"]
    assert task.owner == admin_user
    assert task.assigned_user == employee_user




def task_list(owner, title, is_completed=False, due_date=None, assigned_user=None):
    """
    Testlerde Task oluşturmayı kısaltmak için helper.
    """
    if due_date is None:
        due_date = timezone.now()
    return Task.objects.create(
        owner=owner,
        assigned_user=assigned_user,
        title=title,
        description="test description",
        is_completed=is_completed,
        due_date=due_date,
    )



def test_tasks_list_all_filters_combined_for_admin():
    """
    Bu test, TasksListView içinde bulunan TÜM filtreleme mekanizmalarının
    ( is_completed, due_date_start, due_date_end ) doğru çalıştığını TEK
    senaryoda kontrol eder.

    Test akışı:

    1) Admin kullanıcı oluşturulur (tüm task'ları görebilir).
    2) Veritabanında 4 farklı task oluşturulur:
    - completed task (is_completed=True)
    - incomplete task (is_completed=False)
    - 7 gün önce oluşturulmuş "old task"
    - 7 gün sonrasında due_date'i olan "future task"

    3) Aşağıdaki filtreler API üzerinden tek tek test edilir:

    a) /tasks-list/?is_completed=true  
        → Sadece completed task gelmeli

    b) /tasks-list/?is_completed=false  
        → Sadece incomplete task gelmeli

    c) /tasks-list/?due_date_start=...  
        → Verilen tarihten SONRAKİ task'lar gelmeli (old task gelmez)

    d) /tasks-list/?due_date_end=...  
        → Verilen tarihten ÖNCEKİ task'lar gelmeli (future task gelmez)

    e) /tasks-list/?due_date_start=...&due_date_end=...  
        → Belirli tarih aralığındaki task'lar gelmeli
            (hem old hem future hariç)

    Bu testin amacı:
    - Tüm filtrelerin doğru işlediğini,
    - Birbirinden bağımsız şekilde çalıştığını,
    - Aynı test senaryosu içinde bütün edge case'lerin doğrulandığını
    kanıtlamaktır.
    """

    admin_user = create_admin_user()
    client = get_authenticated_client(admin_user)

    now = timezone.now()

    # ---- Test verileri ----
    task_completed = task_list(
        owner=admin_user,
        title="Completed Task",
        is_completed=True,
        due_date=now,
    )
    task_incomplete = task_list(
        owner=admin_user,
        title="Incomplete Task",
        is_completed=False,
        due_date=now,
    )
    task_old = task_list(
        owner=admin_user,
        title="Old Task",
        due_date=now - timedelta(days=7),
    )
    task_future = task_list(
        owner=admin_user,
        title="Future Task",
        due_date=now + timedelta(days=7),
    )

    url = reverse("tasks-list")


    response = client.get(url, {"is_completed": "true"}, format="json")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["response"]]
    assert "Completed Task" in titles
    assert "Incomplete Task" not in titles

    response = client.get(url, {"is_completed": "false"}, format="json")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["response"]]
    assert "Incomplete Task" in titles
    assert "Completed Task" not in titles

    start = (now - timedelta(days=3)).isoformat()
    response = client.get(url, {"due_date_start": start}, format="json")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["response"]]
    assert "Old Task" not in titles  # çünkü 7 gün önce
    assert "Completed Task" in titles
    assert "Incomplete Task" in titles
    assert "Future Task" in titles

    end = (now + timedelta(days=3)).isoformat()
    response = client.get(url, {"due_date_end": end}, format="json")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["response"]]
    assert "Future Task" not in titles  # 7 gün sonrası
    assert "Old Task" in titles
    assert "Completed Task" in titles
    assert "Incomplete Task" in titles

    start = (now - timedelta(days=1)).isoformat()
    end = (now + timedelta(days=1)).isoformat()

    response = client.get(url, {"due_date_start": start, "due_date_end": end}, format="json")
    assert response.status_code == 200

    titles = [item["title"] for item in response.json()["response"]]

    assert "Completed Task" in titles
    assert "Incomplete Task" in titles
    assert "Old Task" not in titles
    assert "Future Task" not in titles