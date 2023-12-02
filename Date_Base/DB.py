import os
from sqlalchemy import create_engine, Column, String, Integer
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


class BaseDateEror(BaseException):
    pass

Base = declarative_base()


class Tmp(Base):
    __tablename__ = 'tmp'
    address = Column(String, primary_key=True)
    private_key = Column(String)


class DateBase:
    def __init__(self, db_file):
        if os.path.isfile(db_file):
            self.engine = create_engine(f'sqlite:///{db_file}.db')
        else:
            self.engine = create_engine(f'sqlite:///{db_file}.db')
            self.create_tables()

        self.Session = sessionmaker(bind=self.engine)

    def insert_address(self, address: str, private_key: str):
        session = self.Session()
        try:
            if not self.get_address(address):
                tmp = Tmp(address=address, private_key=private_key)
                session.add(tmp)
                session.commit()
        except BaseException:
            session.rollback()
            raise BaseDateEror('Error when adding data')
        finally:
            session.close()

    def get_address(self, address):
        session = self.Session()
        try:
            result = session.query(Tmp).filter(Tmp.address == address).first()
            return result
        finally:
            session.close()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

if __name__ == '__main__':
    pass
