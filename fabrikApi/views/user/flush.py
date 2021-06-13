""" Reset User data. """

import logging
import arrow
import transaction
from zope.sqlalchemy.datamanager import mark_changed
from get_docker_secret import get_docker_secret
from cornice.service import Service

logger = logging.getLogger(__name__)

# SERVICES
fullreset = Service(
    cors_origins=('*',),
    name='fullreset',
    description='Reset Userdata...',
    path='/user/fullreset')

@fullreset.get(permission='observe')
def fullreset_view(request):
    """Resets all the user data (to day zero) 
    * Except inserted data (comments, proposals)... log files  
    """

    assert get_docker_secret('fabrikapi_testing_phase', default=False)
    user_id = request.local_userid
    assert user_id
        
    request.dbsession.execute(
        """DELETE FROM assembly_progression WHERE user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM stage_progression WHERE user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM content_progression WHERE user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM content_peerreview_progression WHERE user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM user_aggregates WHERE assembly_user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM user_aggregates_assembly_progression WHERE assembly_user_id = %s """ % (user_id)
    )
    request.dbsession.execute(
        """DELETE FROM user_aggregates_content_response WHERE response_user_id = %s """ % (user_id)
    )
    mark_changed(request.dbsession)
    transaction.commit()


# SERVICES
resetday = Service(
    cors_origins=('*',),
    name='dayreset',
    description='Reset Userdata of Today...',
    path='/user/dayreset')


@resetday.get(permission='observe')
def resetday_view(request):
    """Resets todays user data  
    """

    assert get_docker_secret('fabrikapi_testing_phase', default=False)
    user_id = request.local_userid
    assert user_id
    
    yesterday = arrow.utcnow().shift(hours=-48)
    request.dbsession.execute(
        """ 
        UPDATE assembly_progression
        SET
            number_of_day_sessions = 1,
            date_last_day_session = '%s',
            date_last_interaction = '%s'
        WHERE user_id = %s
        """ % (yesterday, yesterday, user_id))

    request.dbsession.execute(
        """ 
        UPDATE stage_progression
        SET
            completed = 0,
            date_completed = null,
            focused_content_id = 0,
            number_of_day_sessions = 0,
            date_last_day_session = '%s',
            date_last_interaction = '%s'
        WHERE user_id = %s
        """ % (yesterday, yesterday, user_id))

    request.dbsession.execute(
        """ 
        UPDATE content_progression
        SET
            discussed = 0,
            rating =  null,
            `read` = null,
            salience = null
        WHERE user_id = %s
        """ % (user_id))
    
    request.dbsession.execute(
        """ 
        DELETE FROM content_peerreview_progression
        WHERE date_created > '%s' AND user_id = %s
        """ % (yesterday, user_id))

    request.dbsession.execute(
        """ 
        UPDATE user_aggregates
        SET
            response_progression_count = 0,
            response_salience_count = 0,
            response_rating_avg = 0,
            response_rating_count = 0,
            number_of_day_sessions = 0,
            date_last_interaction = '%s'
        WHERE assembly_user_id = %s
        """ % (yesterday, user_id))

    mark_changed(request.dbsession)
    transaction.commit()
