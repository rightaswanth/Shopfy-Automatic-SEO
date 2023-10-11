from sqlalchemy.exc import IntegrityError

from app import db
from app.services.custom_errors import *


class CRUD:
    @classmethod
    def create(cls, model_is, data):
        try:
            record = model_is(**data)
            db.session.add(record)
        except Exception as e:
            raise BadRequest(f"Please provide all fields correctly {e}")
        cls.db_commit()
        return record
    
    @classmethod
    def update(cls, model_is, condition, data):
        try:
            record = model_is.query.filter_by(**condition).update(data)
        except IntegrityError as e:
            db.session.rollback()
            if 'errors.UniqueViolation':
                raise UnProcessable("This data already exists")
            raise UnProcessable()
        if record:
            cls.db_commit()
            return True
        raise NoContent()

    @classmethod
    def create_if_not(cls, model_is, condition, data):
        record = model_is.query.filter_by(**condition).first()
        if not record:
            return cls.create(model_is, data)
        return record

    @classmethod
    def create_or_update(cls, model_is, condition, data):
        record = model_is.query.filter_by(**condition).first()
        if not record:
            return cls.create(cls, data)
        return cls.update(cls, condition, data)

    @classmethod
    def bulk_insertion(cls, model_is, data):
        for record in data:
            i = model_is(**record)
            db.session.add(i)
        cls.db_commit()

    @classmethod
    def delete(cls, model_is, condition):
        records = model_is.query.filter_by(**condition).all()
        try:
            for record in records:
                db.session.delete(record)
            cls.db_commit()
        except Exception as e:
            print(f"Crud delete exception {e} {condition} {model_is}")
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
