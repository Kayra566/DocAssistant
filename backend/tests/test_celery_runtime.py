from app.workers.celery_app import celery_app


def test_all_background_tasks_are_registered():
    celery_app.loader.import_default_modules()

    assert {
        "ai.run_job",
        "billing.reconcile",
        "documents.process",
        "exports.run",
        "ping",
    } <= set(celery_app.tasks)
