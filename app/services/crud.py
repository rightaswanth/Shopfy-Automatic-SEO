from app import db
from .custom_errors import NoContent, InternalError, BadRequest


class CRUD(object):
    def create(self, cls, data):
        try:
            record = cls(**data)
            db.session.add(record)
        except Exception as e:
            raise BadRequest("Please provide all fields correctly")
        self.db_commit()
        return record

    def update(self, cls, condition, data):
        record = cls.query.filter_by(**condition).update(data)
        if record:
            self.db_commit()
            record = cls.query.filter_by(**condition).first()
            return record
        raise NoContent()

    def create_if_not(self, cls, condition, data):
        record = cls.query.filter_by(**condition).first()
        if not record:
            return self.create(cls, data)
        return record

    def create_or_update(self, cls, condition, data):
        record = cls.query.filter_by(**condition).first()
        if not record:
            return self.create(cls, data)
        return self.update(cls, condition, data)

    def bulk_insertion(self, cls, data):
        for record in data:
            i = cls(**record)
            db.session.add(i)
        self.db_commit()

    def delete(self, cls, condition):
        records = cls.query.filter_by(**condition).all()
        for record in records:
            db.session.delete(record)
            self.db_commit()
        return True

    def db_commit(self):
        try:
            db.session.commit()
            return True
        except Exception as e:
            print(e)
            db.session.rollback()
        raise InternalError()
