<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Student Management System</title>

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        body {
            background-color: #0b1220;
            color: white;
        }
        .container {
            margin-top: 50px;
        }
        .card {
            background-color: #111827;
            border-radius: 15px;
            padding: 20px;
        }
        input {
            margin-bottom: 10px;
        }
        table {
            margin-top: 20px;
        }
    </style>
</head>

<body>

<div class="container">
    <h2 class="text-center mb-4">🎓 Student Management System</h2>

    <!-- Add Student Form -->
    <div class="card">
        <h4>Add Student</h4>

        <form action="/add_student" method="POST">
            <input type="text" name="name" class="form-control" placeholder="Enter Name" required>

            <input type="text" name="roll_no" class="form-control" placeholder="Enter Roll Number" required>

            <button type="submit" class="btn btn-primary w-100 mt-2">Add Student</button>
        </form>
    </div>

    <!-- Student List -->
    <div class="card mt-4">
        <h4>Student List</h4>

        <table class="table table-dark table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Roll No</th>
                </tr>
            </thead>
            <tbody>
                {% for student in students %}
                <tr>
                    <td>{{ student[0] }}</td>
                    <td>{{ student[1] }}</td>
                    <td>{{ student[2] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

</div>

</body>
</html>