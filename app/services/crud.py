from app import db
from app.services.custom_errors import *
import psycopg2
from sqlalchemy.exc import IntegrityError

class CRUD():
    def create(self, cls, data):
        try:
            record = cls(**data)
            db.session.add(record)
        except Exception as e:
            raise BadRequest(f"Please provide all fields correctly {e}")
        self.db_commit()
        return record

    def update(self, cls, condition, data):
        try:
            record = cls.query.filter_by(**condition).update(data)
        except IntegrityError as e:
            db.session.rollback()
            if 'errors.UniqueViolation':
                raise UnProcessable("This data already exists")
            raise UnProcessable()
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
        try:
            for record in records:
                db.session.delete(record)
            self.db_commit()
        except Exception as e:
            print(f"Crud delete exception {e} {condition} {cls}")
        return True

    @staticmethod
    def db_commit():
        try:
            db.session.commit()
            return True
        except IntegrityError as e:
            print(e)
            db.session.rollback()
            if 'errors.UniqueViolation':
                raise UnProcessable("This data already exists")
        except Exception as e:
            print(e)
            db.session.rollback()
            raise InternalError()