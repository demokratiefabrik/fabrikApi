
import logging
from sqlalchemy import Boolean, Column, Integer

logger = logging.getLogger(__name__)


class EditableEntityMixin(object):
    edits = Column("edits", Integer, default=0)
    # did the user performed an edit action?


class ReadableEntityMixin(object):
    read = Column(Boolean, default=False)
    view = Column(Boolean, default=False)
    # view: boolean that is set to true if content is showed in content tree
    # (includes also children of current content)

    def set_read(self):
        """
        Update read status of progression_content
        """

        if self.read:
            return False

        logger.debug("set read %s" % self)
        self.read = True

        return (True)


class RateableEntityMixin(object):
    # RATING_RANGE = [0, 1, 2, 3]

    rating = Column(Integer)
    salience = Column(Integer)
    
    @property
    def is_rated(self):
        """ Use this method to asses if content has been rated """
        return self.rating is not None  # zero values

    def set_rating(self, rating):
        """ Update rating flag """

        assert "rating" in self.content.__roles__, "empty roled...."
        
        if rating is None:
            raise ValueError("cannot store None rating")

        if int(rating) not in self.content.RATING_RANGE:
            raise ValueError("Invalid rating value")

        if int(rating) == self.rating:
            # already rated
            return (False)

        self.rating = int(rating)

        return True

    @property
    def salienced(self):
        """ Is salience indicated? Use this method to asses if salience of content has been assessed """
        return self.salience is not None  # zero values

    def set_salience(self, salience):
        """ Update salience flag """

        assert "saliencing" in self.content.__roles__, "no saliencing permission...."

        if salience is None:
            raise ValueError("cannot store None salience")

        if int(salience) not in self.content.SALIENCE_RANGE:
            raise ValueError("Invalid salience value")

        if int(salience) == self.salience:
            # already salienced
            return (False)

        self.salience = int(salience)

        return True
