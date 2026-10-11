import pytest

import models


@pytest.fixture
def user_factory(client):
    test_client, testing_session_local = client

    def create_user(username, role="user"):
        response = test_client.post(
            "/auth/register",
            json={
                "username": username,
                "password": "student-test-password",
            },
        )
        assert response.status_code == 200

        with testing_session_local() as db:
            user = db.query(models.User).filter(
                models.User.username == username
            ).one()
            user.role = role
            db.commit()
            user_id = user.id

        login_response = test_client.post(
            "/auth/login",
            data={
                "username": username,
                "password": "student-test-password",
            },
        )
        assert login_response.status_code == 200
        assert login_response.json()["token_type"] == "bearer"
        token = login_response.json()["access_token"]
        return user_id, {"Authorization": f"Bearer {token}"}

    return create_user


def add_student(testing_session_local, name, user_id):
    with testing_session_local() as db:
        student = models.Student(
            name=name,
            age=18,
            course="Testing",
            user_id=user_id,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student.id


def test_home(client):
    test_client, _ = client
    response = test_client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Student Management API"
    }


def test_get_students(client):
    test_client, _ = client
    response = test_client.get("/students")

    assert response.status_code == 401


def test_login(client, user_factory):
    _, headers = user_factory("login-test-user")

    assert headers["Authorization"].startswith("Bearer ")


def test_get_students_with_token(client, user_factory):
    test_client, _ = client
    _, headers = user_factory("student-list-test-user")
    response = test_client.get(
        "/students/",
        headers=headers,
    )

    assert response.status_code == 200


def test_admin_can_create_update_and_delete_students(client, user_factory):
    test_client, _ = client
    admin_id, headers = user_factory("student-admin", role="admin")

    create_response = test_client.post(
        "/students/",
        json={"name": "Created Student", "age": 18, "course": "Math"},
        headers=headers,
    )

    assert create_response.status_code == 201
    created_student = create_response.json()
    student_id = created_student["id"]
    assert created_student["name"] == "Created Student"
    assert created_student["user_id"] == admin_id

    update_response = test_client.put(
        f"/students/{student_id}",
        json={"name": "Updated Student", "age": 19, "course": "Science"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Student"
    assert update_response.json()["age"] == 19
    assert update_response.json()["course"] == "Science"

    delete_response = test_client.delete(
        f"/students/{student_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Student deleted successfully"
    assert test_client.get(
        f"/students/{student_id}",
        headers=headers,
    ).status_code == 404


def test_normal_user_cannot_create_update_or_delete_students(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    owner_id, _ = user_factory("student-owner", role="admin")
    _, user_headers = user_factory("student-normal")
    student_id = add_student(
        testing_session_local,
        "Existing Student",
        owner_id,
    )
    payload = {"name": "Changed Student", "age": 20, "course": "History"}

    assert test_client.post(
        "/students/",
        json=payload,
        headers=user_headers,
    ).status_code == 403
    assert test_client.put(
        f"/students/{student_id}",
        json=payload,
        headers=user_headers,
    ).status_code == 403
    assert test_client.patch(
        f"/students/{student_id}",
        json={"name": "Changed Student"},
        headers=user_headers,
    ).status_code == 403
    assert test_client.delete(
        f"/students/{student_id}",
        headers=user_headers,
    ).status_code == 403

    with testing_session_local() as db:
        students = db.query(models.Student).all()

    assert len(students) == 1
    assert students[0].id == student_id
    assert students[0].name == "Existing Student"
    assert students[0].age == 18
    assert students[0].course == "Testing"
    assert students[0].user_id == owner_id


def test_unauthenticated_users_cannot_access_protected_student_endpoints(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    owner_id, _ = user_factory("unauthenticated-test-owner", role="admin")
    student_id = add_student(
        testing_session_local,
        "Protected Student",
        owner_id,
    )

    requests = [
        test_client.get("/students/"),
        test_client.get(f"/students/{student_id}"),
        test_client.post(
            "/students/",
            json={"name": "New Student", "age": 18, "course": "Math"},
        ),
        test_client.put(
            f"/students/{student_id}",
            json={"name": "Changed", "age": 18, "course": "Math"},
        ),
        test_client.patch(
            f"/students/{student_id}",
            json={"name": "Changed"},
        ),
        test_client.delete(f"/students/{student_id}"),
    ]

    assert [response.status_code for response in requests] == [401] * 6


def test_admin_can_list_all_students_including_unowned_legacy_rows(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    admin_id, admin_headers = user_factory(
        "listing-admin",
        role="admin",
    )
    other_owner_id, _ = user_factory("listing-other-owner")
    add_student(testing_session_local, "Admin Student", admin_id)
    add_student(testing_session_local, "Other User Student", other_owner_id)
    add_student(testing_session_local, "Legacy Student", None)

    response = test_client.get("/students/", headers=admin_headers)

    assert response.status_code == 200
    assert {student["name"] for student in response.json()} == {
        "Admin Student",
        "Other User Student",
        "Legacy Student",
    }


def test_normal_user_lists_only_students_assigned_to_them(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    own_user_id, user_headers = user_factory("list-own-user")
    other_user_id, _ = user_factory("list-other-user")
    add_student(testing_session_local, "Own Student", own_user_id)
    add_student(testing_session_local, "Other Student", other_user_id)
    add_student(testing_session_local, "Legacy Student", None)

    response = test_client.get("/students/", headers=user_headers)

    assert response.status_code == 200
    assert [student["name"] for student in response.json()] == ["Own Student"]


def test_normal_user_getting_another_users_student_returns_not_found(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    owner_id, _ = user_factory("record-owner")
    _, user_headers = user_factory("record-reader")
    student_id = add_student(
        testing_session_local,
        "Private Student",
        owner_id,
    )

    response = test_client.get(
        f"/students/{student_id}",
        headers=user_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_unowned_legacy_student_is_hidden_from_normal_user(
    client,
    user_factory,
):
    test_client, testing_session_local = client
    _, user_headers = user_factory("legacy-record-reader")
    student_id = add_student(
        testing_session_local,
        "Unowned Legacy Student",
        None,
    )

    list_response = test_client.get("/students/", headers=user_headers)
    record_response = test_client.get(
        f"/students/{student_id}",
        headers=user_headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []
    assert record_response.status_code == 404
    assert record_response.json()["detail"] == "Student not found"
