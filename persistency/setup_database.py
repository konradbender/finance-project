
from secured import aws as secured
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.trador import Trador_Base

pw = secured.server_password
user = secured.server_user

engine = create_engine(f'postgresql://{user}:' + pw +
                       '@options-project.cnvyqwl6mmbn.eu-central-1.rds.amazonaws.com/postgres', pool_size = 20, max_overflow = 10)

Session = sessionmaker(bind=engine, autoflush=True)
session = Session()


Trador_Base.metadata.create_all(engine)
session = session.commit()

class my_connection:

    def __init__(self):
        self.engine = engine
        self.session = Session()