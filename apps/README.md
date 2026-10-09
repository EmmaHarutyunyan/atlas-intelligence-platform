# Django Apps

Each subdirectory here is a self-contained bounded context (Django app).

Convention for every app added starting in Milestone 2:

```
apps/<app_name>/
├── __init__.py
├── apps.py              # AppConfig
├── models.py             # thin: fields, relations, invariants only
├── services.py            # business logic / use-case orchestration
├── repositories.py        # optional: complex query encapsulation
├── serializers.py          # DRF serializers
├── views.py                # thin DRF viewsets, delegate to services
├── permissions.py          # DRF permission classes specific to this app
├── urls.py
├── admin.py
├── tasks.py                 # Celery tasks, if any
├── exceptions.py             # domain-specific exceptions
├── migrations/
└── tests/
    ├── factories.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

No app imports another app's `models.py` directly except `apps.core`. Cross-app
interaction happens through service-layer calls.
