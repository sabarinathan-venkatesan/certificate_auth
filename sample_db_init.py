from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Certificate
from werkzeug.security import generate_password_hash

DB_URL = "mysql+pymysql://root:tiger@localhost/auth_validator"


def init_db():
    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add admin & user
    if not session.query(User).filter_by(username="admin").first():
        session.add(User(username="admin", password_hash=generate_password_hash("adminpass"), role="admin"))
    if not session.query(User).filter_by(username="user1").first():
        session.add(User(username="user1", password_hash=generate_password_hash("userpass"), role="user"))

    # Add trusted certificates
    sample = [
        Certificate(cert_id="JH2021CSE001", student_name="Rahul Sharma", roll_number="2021CSE45",
                    course="B.Tech CSE", institution="Ranchi University", year_of_passing=2021, marks_percentage=82.5),
        Certificate(cert_id="JH2020ECE002", student_name="Pooja Singh", roll_number="2020ECE32",
                    course="B.Tech ECE", institution="BIT Mesra", year_of_passing=2020, marks_percentage=78.0),
        Certificate(cert_id="JH2019CIV003", student_name="Amit Kumar", roll_number="2019CIV19",
                    course="B.Tech Civil", institution="NIT Jamshedpur", year_of_passing=2019, marks_percentage=74.3),
    ]
    for cert in sample:
        if not session.query(Certificate).filter_by(cert_id=cert.cert_id).first():
            session.add(cert)

    session.commit()
    session.close()
    print("✅ Database initialized: auth_validator.db created")

if __name__ == "__main__":
    init_db()
