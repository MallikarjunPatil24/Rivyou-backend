import threading
from django.db import connection

def _save_log(user_id, query, results_count):
    from django.contrib.auth import get_user_model
    from .models import SearchLog
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id) if user_id else None
        SearchLog.objects.create(user=user, query=query, results_count=results_count)
    except Exception as e:
        import logging
        logger = logging.getLogger('analytics')
        logger.error(f"Error saving search query log asynchronously: {e}")
    finally:
        # Close connection in threads to avoid database pool leaks
        connection.close()

def log_search_async(user, query, results_count):
    """
    Asynchronously logs search query and result details in a background thread.
    Does not block the request-response cycle.
    """
    user_id = user.id if user and user.is_authenticated else None
    thread = threading.Thread(
        target=_save_log,
        args=(user_id, query, results_count),
        name="AsyncSearchLogThread"
    )
    thread.daemon = True
    thread.start()
