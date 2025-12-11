from flask import jsonify
from flask_login import current_user
from app.admin import bp
from app.scheduler import scheduler


@bp.route('/jobs', methods=['GET'])
def jobs():
    """Return a JSON list of APScheduler jobs. Requires authentication.

    Returns 401 if the requester is not authenticated.
    """
    if not current_user or not current_user.is_authenticated:
        return jsonify({'error': 'unauthenticated'}), 401

    jobs = scheduler.get_jobs()
    jobs_list = []
    for j in jobs:
        try:
            next_run = j.next_run_time.isoformat() if j.next_run_time else None
        except Exception:
            next_run = None
        jobs_list.append({
            'id': j.id,
            'name': getattr(j, 'name', None),
            'next_run_time': next_run,
            'trigger': str(j.trigger),
            'args': getattr(j, 'args', None)
        })

    return jsonify(jobs_list), 200
