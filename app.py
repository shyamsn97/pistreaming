from celery import Celery

# internal imports
class CeleryConfig:
    CELERY_ACCEPT_CONTENT = ["pickle"]
    CELERY_SERIALIZER = "pickle"
    CELERY_RESULT_SERIALIZER = "pickle"
    CELERY_IMPORTS = "tasks"

RESULT_EXPIRE_TIME = 60  # keep tasks around for four hours

app = Celery(result_expires=RESULT_EXPIRE_TIME)
app.config_from_object(CeleryConfig)
app.conf.update(
    CELERY_ACCEPT_CONTENT=["pickle"],
    CELERY_TASK_SERIALIZER="pickle",
    CELERY_RESULT_SERIALIZER="pickle",
    CELERY_IMPORTS=("pistreaming.tasks"),
)