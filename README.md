# Django: blog (List/Detail + лайки), crud (CRUD + тесты), reports (тесты -> Word)

    pip install -r requirements.txt
    python manage.py migrate
    python manage.py test                 # все тесты (56)
    python manage.py test crud            # только тесты CRUD
    python manage.py export_tests_docx    # запустить тесты и записать их в tests_report.docx
    python manage.py runserver

Адреса: /blog/  /blog/<id>/  /crud/  /crud/create/  /crud/<id>/update/  /crud/<id>/delete/  /admin/

Отчёт только по CRUD: python manage.py export_tests_docx crud -o crud_report.docx
